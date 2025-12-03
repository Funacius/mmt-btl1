import socket
import threading
import json
from collections import defaultdict
import uuid
import time
import argparse

HOST = "192.168.1.3"
PORT = 9000

class Peer:
    def __init__(self, port):
        self.id = str(uuid.uuid4())[:8]
        self.port = port
        self.server_sock = None
        self.connections = {}       # peer_id -> socket
        self.connections_lock = threading.Lock()
        self.channel_msgs = defaultdict(list)  # channel -> message list
        self.running = True

    # server intialize
    def start_server(self):
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_sock.bind((HOST, self.port))
        self.server_sock.listen(8)
        print(f"[INFO] Peer server listening on {HOST}:{self.port} (id={self.id})")
        threading.Thread(target=self._accept_loop, daemon=True).start()

    def _accept_loop(self):
        while self.running:
            try:
                conn, addr = self.server_sock.accept()
                threading.Thread(target=self._handle_connection, args=(conn,), daemon=True).start()
            except Exception as e:
                print("[ERROR] Accept loop:", e)

    def _handle_connection(self, conn):
        peer_id = None
        try:
            # expect{"type":"handshake","id":"peerid"} 
            raw = b""
            while not raw.endswith(b"\n"):
                chunk = conn.recv(4096)
                if not chunk:
                    return
                raw += chunk
            obj = json.loads(raw.decode())
            if obj.get("type") == "handshake":
                peer_id = obj.get("id")
                with self.connections_lock:
                    self.connections[peer_id] = conn
                print(f"[INFO] Handshake from {peer_id}")
            else:
                conn.close()
                return

            # Receive loop
            while True:
                data = b""
                while not data.endswith(b"\n"):
                    chunk = conn.recv(4096)
                    if not chunk:
                        raise ConnectionError("Peer disconnected")
                    data += chunk
                msg = json.loads(data.decode())
                self._process_message(msg, peer_id)
        except Exception as e:
            if peer_id:
                with self.connections_lock:
                    self.connections.pop(peer_id, None)
            try:
                conn.close()
            except:
                pass
            print(f"[INFO] Connection closed from {peer_id or '?'} ({e})")

    # Message processing
    def _process_message(self, msg, from_peer):
        mtype = msg.get("type")
        if mtype == "msg":
            channel = msg.get("channel", "general")
            text = msg.get("text")
            atomic = {"from": from_peer, "text": text, "channel": channel, "ts": time.time()}
            self.channel_msgs[channel].append(atomic)
            print(f"\n[#{channel}] {from_peer}: {text}\n> ", end="", flush=True)

    # Peer connection
    def connect_to_peer(self, host, port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((host, port))
            hs = json.dumps({"type":"handshake","id":self.id}).encode()+b"\n"
            s.sendall(hs)
            threading.Thread(target=self._handle_connection, args=(s,), daemon=True).start()
            print(f"[INFO] Connected to peer at {host}:{port}")
        except Exception as e:
            print("[ERROR] Connect to peer failed:", e)

    # Chat logic
    def broadcast(self, channel, text):
        payload = {"type":"msg","channel":channel,"text":text}
        to_remove = []
        with self.connections_lock:
            for pid, sock in list(self.connections.items()):
                try:
                    sock.sendall(json.dumps(payload).encode()+b"\n")
                except Exception as e:
                    print(f"[WARN] Send to {pid} failed ({e})")
                    to_remove.append(pid)
            for pid in to_remove:
                self.connections.pop(pid, None)
        # Local
        self.channel_msgs[channel].append({"from": self.id, "text": text, "channel": channel, "ts": time.time()})

    def send_to_peer(self, peer_id, text, channel="general"):
        payload = {"type":"msg","channel":channel,"text":text}
        with self.connections_lock:
            s = self.connections.get(peer_id)
            if not s:
                print("[WARN] No connection to", peer_id)
                return
            try:
                s.sendall(json.dumps(payload).encode()+b"\n")
            except Exception as e:
                print("[WARN] Send error", e)

    # CLI mini UI
    def cli_loop(self):
        print("Commands: connect <host> <port>, broadcast <channel> <text>, send <peer_id> <text>, list_peers, list_ch, show_ch <channel>, quit")
        while True:
            try:
                cmd = input("> ").strip()
            except EOFError:
                break
            if not cmd:
                continue
            parts = cmd.split(" ", 2)
            if parts[0] == "quit":
                self.running = False
                try: self.server_sock.close()
                except: pass
                with self.connections_lock:
                    for s in self.connections.values():
                        try: s.close()
                        except: pass
                break
            elif parts[0] == "connect" and len(parts) >= 3:
                host = parts[1]
                port = int(parts[2])
                self.connect_to_peer(host, port)
            elif parts[0] == "broadcast" and len(parts) >= 3:
                ch, text = parts[1], parts[2]
                self.broadcast(ch, text)
            elif parts[0] == "send" and len(parts) >= 3:
                pid, text = parts[1], parts[2]
                self.send_to_peer(pid, text)
            elif parts[0] == "list_peers":
                with self.connections_lock:
                    print("Connected peers:", list(self.connections.keys()))
            elif parts[0] == "list_ch":
                print("Channels:", list(self.channel_msgs.keys()))
            elif parts[0] == "show_ch" and len(parts) >= 2:
                ch = parts[1]
                for m in self.channel_msgs.get(ch, []):
                    print(f"{m['from']}: {m['text']}")
            else:
                print("Unknown command")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='Backend', description='', epilog='Beckend daemon')
    parser.add_argument('--server-ip', default='0.0.0.0')
    parser.add_argument('--server-port', type=int, default=PORT)
    port = int(input("Enter port for this peer: "))
    peer = Peer(port)
    peer.start_server()
    peer.cli_loop()
