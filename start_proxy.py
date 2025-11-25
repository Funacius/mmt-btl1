# start_proxy.py
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
start_proxy
~~~~~~~~~~~~~~~~~

This module serves as the entry point for launching a proxy server using Python's socket framework.
It parses command-line arguments to configure the server's IP address and port, reads virtual host
definitions from a configuration file, and initializes the proxy server with routing information.
"""

import socket
import threading
import argparse
import re
from urllib.parse import urlparse   # Python 3
from collections import defaultdict

from daemon import create_proxy

PROXY_PORT = 8080


def parse_virtual_hosts(config_file):
    """
    Parses virtual host blocks from a config file.

    :config_file (str): Path to the NGINX-like config file.
    :rtype dict: { host: (proxy_map OR list_of_proxy, policy) }
    """

    with open(config_file, 'r') as f:
        config_text = f.read()

    # Match each host block: host "..." { ... }
    host_blocks = re.findall(r'host\s+"([^"]+)"\s*\{(.*?)\}', config_text, re.DOTALL)

    routes = {}

    for host, block in host_blocks:
        proxy_map = {}

        # Find all proxy_pass entries inside the block
        proxy_passes = re.findall(r'proxy_pass\s+http://([^\s;]+);', block)

        current_list = proxy_map.get(host, [])
        current_list = current_list + proxy_passes
        proxy_map[host] = current_list

        # Find dist_policy if present
        policy_match = re.search(r'dist_policy\s+(\w+)', block)
        if policy_match:
            dist_policy = policy_match.group(1)
        else:
            dist_policy = 'round-robin'

        # Build mapping + policy
        # - Nếu chỉ có 1 proxy_pass: lưu string
        # - Nếu nhiều proxy_pass: lưu list và áp dụng policy sau này trong proxy.py
        if len(proxy_map.get(host, [])) == 1:
            routes[host] = (proxy_map.get(host, [])[0], dist_policy)
        else:
            routes[host] = (proxy_map.get(host, []), dist_policy)

    # Debug: in ra map đã parse
    for key, value in routes.items():
        print(key, value)

    return routes


if __name__ == "__main__":
    """
    Entry point for launching the proxy server.
    """

    parser = argparse.ArgumentParser(prog='Proxy', description='', epilog='Proxy daemon')
    parser.add_argument('--server-ip', default='0.0.0.0')
    parser.add_argument('--server-port', type=int, default=PROXY_PORT)

    args = parser.parse_args()
    ip = args.server_ip
    port = args.server_port

    # Đọc cấu hình từ config/proxy.conf
    routes = parse_virtual_hosts("config/proxy.conf")

    # Khởi động proxy
    create_proxy(ip, port, routes)