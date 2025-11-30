#
# Copyright (C) 2025 pdnguyen of HCMC University of Technology VNU-HCM.
# All rights reserved.
# This file is part of the CO3093/CO3094 course.
#
# WeApRous release
#
# The authors hereby grant to Licensee personal permission to use
# and modify the Licensed Source Code for the sole purpose of studying
# while attending the course
#

"""
daemon.request
~~~~~~~~~~~~~~~~~

This module provides a Request object to manage and persist 
request settings (cookies, auth, proxies).
"""
from .dictionary import CaseInsensitiveDict
import base64

class Request():
    """The fully mutable "class" `Request <Request>` object,
    containing the exact bytes that will be sent to the server.

    Instances are generated from a "class" `Request <Request>` object, and
    should not be instantiated manually; doing so may produce undesirable
    effects.

    Usage::

      >>> import deamon.request
      >>> req = request.Request()
      ## Incoming message obtain aka. incoming_msg
      >>> r = req.prepare(incoming_msg)
      >>> r
      <Request>
    """
    __attrs__ = [
        "method",
        "url",
        "headers",
        "body",
        "reason",
        "cookies",
        "body",
        "routes",
        "hook",
    ]

    def __init__(self):
        #: HTTP verb to send to the server.
        self.method = None
        #: HTTP URL to send the request to.
        self.url = None
        #: dictionary of HTTP headers.
        self.headers = None
        #: HTTP path
        self.path = None        
        # The cookies set used to create Cookie header
        self.cookies = None
        #: request body to send to the server.
        self.body = None
        #: Routes
        self.routes = {}
        #: Hook point for routed mapped-path
        self.hook = None

    def extract_request_line(self, request):
        try:
            lines = request.splitlines()
            first_line = lines[0]
            method, path, version = first_line.split()
            path = path.strip().rstrip('\r\n')
            if path == '/':
                path = '/index.html'
        except Exception:
            return None, None

        return method, path, version
             
    def prepare_headers(self, request):
        """Prepares the given HTTP headers."""
        lines = request.split('\r\n')
        headers = {}
        for line in lines[1:]:
            if ': ' in line:
                key, val = line.split(': ', 1)
                headers[key.lower()] = val
        return headers

    def prepare(self, request, routes=None):
        """Prepares the entire request with the given parameters."""
        
        self.method, self.path, self.version = self.extract_request_line(request)
        if self.method:
            self.method = self.method.upper()
        print("[Request] {} path {} version {}".format(self.method, self.path, self.version))
        if "\r\n\r\n" in request:
            raw_header, raw_body = request.split("\r\n\r\n", 1)
        else:
            raw_header, raw_body = request, ""
            
        self.headers = self.prepare_headers(raw_header)
        # Parse cookies with error handling
        raw_cookie = self.headers.get("cookie", "")
        self.cookies = CaseInsensitiveDict()

        try:
            if raw_cookie:
                cookie_pairs = raw_cookie.split(";")
                for pair in cookie_pairs:
                    if "=" in pair:
                        k, v = pair.strip().split("=", 1)
                        self.cookies[k] = v
                print(f"[Request] Parsed cookies: {dict(self.cookies)}")
        except Exception as e:
            print(f"[Request] Error parsing cookie: {e}")
            self.cookies = CaseInsensitiveDict()
        if routes:
            lookup_key = (self.method, self.path)
            self.hook = routes.get(lookup_key)
        # Prepare the request line from the request header

        #
        # @bksysnet Preapring the webapp hook with WeApRous instance
        # The default behaviour with HTTP server is empty routed
        #
        # TODO manage the webapp hook in this mounting point
        #
        # if not routes == {}:
        #     self.routes = routes
        #     self.hook = routes.get((self.method, self.path))
        #     #
        #     # self.hook manipulation goes here
        #     # ...
        #     #

        # self.headers = self.prepare_headers(raw_header)
        # raw_cookie = self.headers.get("cookie", "")
        # self.cookies = CaseInsensitiveDict()

        # if raw_cookie:
        #     cookie_pairs = raw_cookie.split(";")
        #     for pair in cookie_pairs:
        #         if "=" in pair:
        #             k, v = pair.strip().split("=", 1)
        #             self.cookies[k] = v
            #
            #  TODO: implement the cookie function here
            #        by parsing the header            #
        if self.method == "POST":
            self.body = raw_body
        else:
            self.body = ""
        
        return

    def prepare_body(self, data, files, json=None):
        if json is not None:
            import json as json_lib
            body = json_lib.dumps(json)
        elif data is not None:
            body = data
        else:
            body = ""
        self.body = body
        self.prepare_content_length(self.body)
        #
        # TODO prepare the request authentication
        #
	# self.auth = ...
        return


    def prepare_content_length(self, body):
        if body is None:
            length = "0"
        else:
            length = str(len(body.encode("utf-8")))

        self.headers["Content-Length"] = length
        #
        # TODO prepare the request authentication
        #
	# self.auth = ...
        return


    def prepare_auth(self, auth, url=""):
        #
        # TODO prepare the request authentication
        #
	# self.auth = ...
        if auth is None:
                return

        username, password = auth
        token = f"{username}:{password}"
        base64_token = base64.b64encode(token.encode()).decode()

        self.headers["authorization"] = f"Basic {base64_token}"
        return

    def prepare_cookies(self, cookies):
        cookie_str = "; ".join([f"{k}={v}" for k, v in cookies.items()])
        self.headers["Cookie"] = cookie_str
