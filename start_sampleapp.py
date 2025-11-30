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
from apps.P2P import Peer

peer_instance = Peer(port=9005)   # ví dụ – port này nên dynamic theo máy bạn
peer_instance.start_server()
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

@app.route('/leave', methods=['POST'])
def leave(headers=None, body=None):
    try:
        data = json.loads(body or "{}")
        peer_id = data.get("peer_id")
        if peer_id:
            tracker.remove_peer(peer_id)
            print(f"[Tracker] Peer {peer_id} has left the network")
        return json.dumps({"status": "OK", "message": "Peer removed"})
    except Exception as e:
        print(f"[Tracker] Error removing peer: {e}")
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
        print(tracker.get_peers())
        return json.dumps({"status": "UPDATED"})

    except Exception as e:
        return json.dumps({"status": "ERROR", "message": str(e)})

@app.route('/connect-peer', methods=['POST'])
def connect_peer(headers="guest", body="{}"):
    try:
        data = json.loads(body)
        host = data.get("host")
        port = data.get("port")

        if not host or not port:
            return json.dumps({"status": "ERROR", "message": "host/port required"})

        peer_instance.connect_to_peer(host, int(port))
        return json.dumps({"status": "OK", "message": "Connected"})

    except Exception as e:
        return json.dumps({"status": "ERROR", "message": str(e)})
    
@app.route('/broadcast-peer', methods=['POST'])
def broadcast_peer(headers="guest", body="{}"):
    try:
        data = json.loads(body)
        channel = data.get("channel", "general")
        text = data.get("text", "")

        peer_instance.broadcast(channel, text)
        return json.dumps({"status": "OK"})

    except Exception as e:
        return json.dumps({"status": "ERROR", "message": str(e)})

@app.route('/send-peer', methods=['POST'])
def send_peer(headers="guest", body="{}"):
    try:
        data = json.loads(body)
        peer_id = data.get("peer_id")
        text = data.get("text", "")
        channel = data.get("channel", "general")

        if not peer_id:
            return json.dumps({"status": "ERROR", "message": "peer_id required"})

        peer_instance.send_to_peer(peer_id, text, channel)
        return json.dumps({"status": "OK"})

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

@app.route('/add-list', methods=['POST'])
def add_list(headers="guest", body="{}"):
    """
    API example: http://IP:port/add-list/

    Ý tưởng:
    - Client gửi lên peer_id + channel mới muốn join.
    - Server thêm channel đó vào list channels của peer trong TrackerState.
    """
    try:
        data = json.loads(body)

        peer_id = data.get("peer_id")
        new_channel = data.get("channel")

        if not peer_id or not new_channel:
            return json.dumps({
                "status": "ERROR",
                "message": "peer_id and channel required"
            })

        # Lấy peer hiện tại từ tracker
        peers = tracker.get_peers()              # list of dict
        found = None
        for p in peers:
            if p.get("peer_id") == peer_id:
                found = p
                break

        if not found:
            return json.dumps({
                "status": "ERROR",
                "message": "peer_id not registered"
            })

        channels = found.get("channels", [])
        if new_channel not in channels:
            channels.append(new_channel)

        # Cập nhật lại tracker
        tracker.update_peer(peer_id, channels=channels)

        print("[Tracker] Add channel:", peer_id, channels)
        return json.dumps({"status": "OK", "channels": channels})

    except Exception as e:
        return json.dumps({"status": "ERROR", "message": str(e)})

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