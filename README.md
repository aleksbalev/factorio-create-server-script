# Factorio Server Management Script

A simple Python script to manage your Factorio server affordably using Digital Ocean.

## Overview

This script offers a cost-effective way to host your own Factorio server on Digital Ocean. By utilizing Digital Ocean's hourly droplet rates, you can minimize costs.

- **Start the server**: `python factorio-server.py start`
- **Stop the server**: `python factorio-server.py stop`

**Note:** Destroying the droplet when stopping the server is essential to avoid monthly billing. This process might take a few minutes.

### Disadvantages

1. **Changing IP Address**: The IP address changes unless you opt for a Reserved IP. For long-term usage within a month, a Reserved IP might become cost-effective.
2. **User Knowledge**: Your friends need to know how to operate the server script on their devices.
3. **Startup and Shutdown Time**: The server takes approximately 4-5 minutes in total to start and stop.

## Dependencies

Ensure you have the following dependencies installed before running the script:

```sh
pip install python-digitalocean
pip install python-dotenv

Create a Digital Ocean account to obtain an API key. Then, create a .env file in the same directory as the script and add your API key:

`DIGITALOCEAN_API_TOKEN=Your_API_Token`

```
