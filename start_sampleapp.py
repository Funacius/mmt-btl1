#
# Copyright (C) 2025 pdnguyen of HCMC University of Technology VNU-HCM.
# All rights reserved.
# This file is part of the CO3093/CO3094 course,
# and is released under the "MIT License Agreement". Please see the LICENSE
# file that should have been included as part of this package.
#
# WeApRous release
#
# The authors hereby grant to Licensee personal permission to use
# and modify the Licensed Source Code for the sole purpose of studying
# while attending the course
#


"""
start_sampleapp
~~~~~~~~~~~~~~~~~

This module provides a sample RESTful web application using the WeApRous framework.

It defines basic route handlers and launches a TCP-based backend server to serve
HTTP requests. The application includes a login endpoint and a greeting endpoint,
and can be configured via command-line arguments.
"""

import json
import socket
import argparse

from apps.Tracker import TrackerState
tracker = TrackerState()

from daemon.weaprous import WeApRous

PORT = 8000  # Default port

app = WeApRous()


@app.route('/login', methods=['POST'])
def login(headers="guest", body="anonymous"):
    """
    Handle user login via POST request.

    This route simulates a login process and prints the provided headers and body
    to the console.

    :param headers (str): The request headers or user identifier.
    :param body (str): The request body or login payload.
    """
    try:
        data = json.loads(body)

        peer_id = data.get("peer_id")
        ip = data.get("ip")
        port = data.get("port")
        channels = data.get("channels", [])

        if peer_id is None or ip is None or port is None:
            return json.dumps({"status": "ERROR", "message": "Missing required fields"})

        tracker.register_peer(peer_id, ip, port, channels)

        print("[Tracker] Registered:", peer_id, ip, port, channels)
        return json.dumps({"status": "OK"})

    except Exception as e:
        return json.dumps({"status": "ERROR", "message": str(e)})


@app.route('/submit-info', methods=['POST'])
def submit_info(headers="guest", body="{}"):
    try:
        data = json.loads(body)
        peer_id = data.get("peer_id")

        if peer_id is None:
            return json.dumps({"status": "ERROR", "message": "peer_id required"})

        tracker.update_peer(
            peer_id,
            ip=data.get("ip"),
            port=data.get("port"),
            channels=data.get("channels")
        )

        print("[Tracker] Updated:", peer_id, data)
        return json.dumps({"status": "UPDATED"})

    except Exception as e:
        return json.dumps({"status": "ERROR", "message": str(e)})


@app.route('/get-list', methods=['POST', 'GET'])
def get_list(headers="guest", body="{}"):
    try:
        channel = None
        if body:
            try:
                data = json.loads(body)
                channel = data.get("channel")
            except Exception:
                channel = None

        peers = tracker.get_peers(channel)

        return json.dumps({
            "status": "OK",
            "peers": peers
        })

    except Exception as e:
        return json.dumps({"status": "ERROR", "message": str(e)})


@app.route('/hello', methods=['PUT'])
def hello(headers, body):
    """
    Handle greeting via PUT request.

    This route prints a greeting message to the console using the provided headers
    and body.

    :param headers (str): The request headers or user identifier.
    :param body (str): The request body or message payload.
    """
    print("[SampleApp] ['PUT'] Hello in {} to {}".format(headers, body))


if __name__ == "__main__":
    # Parse command-line arguments to configure server IP and port
    parser = argparse.ArgumentParser(prog='Backend', description='', epilog='Beckend daemon')
    parser.add_argument('--server-ip', default='0.0.0.0')
    parser.add_argument('--server-port', type=int, default=PORT)

    args = parser.parse_args()
    ip = args.server_ip
    port = args.server_port

    # Prepare and launch the RESTful application
    app.prepare_address(ip, port)
    app.run()