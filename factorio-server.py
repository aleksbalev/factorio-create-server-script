import digitalocean
import argparse
import time
from dotenv import load_dotenv
import os
import paramiko

# Load environment variables from .env file
load_dotenv()

# Get the API token from the environment variables
api_token = os.getenv("DIGITALOCEAN_API_TOKEN")
ssh_key_path = os.getenv("SSH_KEY_PATH")
ssh_key_id = os.getenv("SSH_KEY_ID")

# Expand the SSH key path to handle the tilde
if ssh_key_path:
    ssh_key_path = os.path.expanduser(ssh_key_path)

# Authenticate with DigitalOcean API
if not api_token or not ssh_key_path or not ssh_key_id:
    raise Exception(
        "API token not found. Please set DIGITALOCEAN_API_TOKEN in your .env file."
    )

manager = digitalocean.Manager(token=api_token)


def get_single_snapshot():
    snapshots = manager.get_all_snapshots()
    if len(snapshots) != 1:
        raise Exception("There should be exactly one snapshot.")
    return snapshots[0].id


def get_single_droplet():
    droplets = manager.get_all_droplets()
    if len(droplets) != 1:
        raise Exception("There should be exactly one droplet.")
    return droplets[0].id


def wait_for_droplet_ip(droplet):
    droplet.load()
    while not droplet.ip_address:
        print("Waiting for droplet IP address...")
        time.sleep(5)
        droplet.load()
    return droplet.ip_address


def clean_up_droplet(droplet):
    ip_address = wait_for_droplet_ip(droplet)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip_address, username="root", key_filename=ssh_key_path)

    commands = [
        "rm -rf /tmp/*",
        "rm -rf /var/tmp/*",
        "find /var/log -type f -exec truncate -s 0 {} \;",
        "find /var/cache -type f -exec rm -f {} \;",
        "find /var/lib -type f -exec rm -f {} \;",
        "find /var/spool -type f -exec rm -f {} \;",
        "find /var/log -type f -exec truncate -s 0 {} \;",
        'find /home -name "*.bak" -type f -exec rm -f {} \;',
        'find /home -name "*.tmp" -type f -exec rm -f {} \;',
        'find /home -name "*.log" -type f -exec truncate -s 0 {} \;',
        "sync",
        "cat /dev/zero > /zero; sync; rm /zero; sync",  # Zero out free space
    ]

    for command in commands:
        print(f"Executing: {command}")
        stdin, stdout, stderr = ssh.exec_command(command)
        stdout.channel.recv_exit_status()  # Wait for command to finish
        output = stdout.read().decode()
        error = stderr.read().decode()
        if output:
            print(output)
        if error:
            print(error)
    ssh.close()


def create_droplet_from_snapshot(snapshot_name):
    droplet = digitalocean.Droplet(
        token=api_token,
        name="factorio-server",
        region="fra1",
        image=snapshot_name,
        size_slug="s-1vcpu-1gb-amd",
        ssh_keys=[ssh_key_id],
        backups=False,
    )

    try:
        droplet.create()
    except digitalocean.baseapi.DataReadError as e:
        print(f"Error creating droplet: {e}")
        return None

    actions = droplet.get_actions()
    for action in actions:
        action.load()
        while action.status != "completed":
            time.sleep(5)
            action.load()

    droplet.load()
    return droplet


def stop_droplet_and_manage_snapshots(droplet_id, old_snapshot_name):
    droplet = digitalocean.Droplet(token=api_token, id=droplet_id)

    clean_up_droplet(droplet)

    droplet.power_off()
    time.sleep(60)

    droplet.take_snapshot("factorio-server-snapshot")

    actions = droplet.get_actions()
    for action in actions:
        action.load()
        while action.status != "completed":
            time.sleep(5)
            action.load()

    old_snapshot = manager.get_image(old_snapshot_name)
    old_snapshot.destroy()

    droplet.destroy()


def main():
    parser = argparse.ArgumentParser(description="Manage DigitalOcean droplets.")
    parser.add_argument(
        "action",
        choices=["start", "stop"],
        help="Action to perform: start or stop the droplet",
    )

    args = parser.parse_args()

    if args.action == "start":
        snapshot_name = get_single_snapshot()
        print("Creating server...")
        droplet = create_droplet_from_snapshot(snapshot_name)
        if droplet:
            print(f"Server created: {droplet.id}")
            print(f"Server IP: {droplet.ip_address}:34197")
        else:
            print("Failed to create server")

    elif args.action == "stop":
        droplet_id = get_single_droplet()
        snapshot_name = get_single_snapshot()
        print("Destroying server and saving data...")
        stop_droplet_and_manage_snapshots(droplet_id, snapshot_name)
        print("Droplet stopped and snapshots managed.")
    else:
        print("Invalid action.")


if __name__ == "__main__":
    main()
