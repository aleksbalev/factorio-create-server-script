import digitalocean
import argparse
import time
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Get the API token from the environment variables
api_token = os.getenv("DIGITALOCEAN_API_TOKEN")

# Authenticate with DigitalOcean API
if not api_token:
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


def create_droplet_from_snapshot(snapshot_name):
    droplet = digitalocean.Droplet(
        token=api_token,
        name="factorio-server",
        region="fra1",
        image=snapshot_name,
        size_slug="s-1vcpu-2gb-70gb-intel",
        backups=False,
    )
    droplet.create()

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
        print(f"Server created: {droplet.id}")
        print(f"Server IP: {droplet.ip_address}:34197")
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
