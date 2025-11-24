# apps/tracker.py
# -*- coding: utf-8 -*-

class TrackerState(object):
    """
    Lưu trữ thông tin các peer đang online.

    Cấu trúc:
        self.peers = {
            "peerA": {
                "peer_id": "peerA",
                "ip": "127.0.0.1",
                "port": 9000,
                "channels": ["general", "tech"]
            },
            ...
        }
    """

    def __init__(self):
        # {peer_id: {"peer_id": str, "ip": str, "port": int, "channels": [str]}}
        self.peers = {}

    def register_peer(self, peer_id, ip, port, channels):
        """
        Đăng ký (hoặc ghi đè) 1 peer mới.

        :param peer_id: định danh peer (string, duy nhất)
        :param ip: địa chỉ IP của peer
        :param port: cổng TCP của peer
        :param channels: list các channel mà peer tham gia
        """
        if channels is None:
            channels = []

        # đảm bảo channels là list
        if isinstance(channels, basestring):
            channels = [channels]

        self.peers[peer_id] = {
            "peer_id": peer_id,
            "ip": ip,
            "port": port,
            "channels": channels,
        }

    def update_peer(self, peer_id, ip=None, port=None, channels=None):
        """
        Cập nhật thông tin cho peer đã tồn tại.
        Các tham số None sẽ bị bỏ qua, chỉ update những gì truyền vào.
        """
        if peer_id not in self.peers:
            # không có thì bỏ qua (hoặc có thể raise exception tùy bạn)
            return

        peer = self.peers[peer_id]

        if ip is not None:
            peer["ip"] = ip
        if port is not None:
            peer["port"] = port
        if channels is not None:
            if isinstance(channels, basestring):
                channels = [channels]
            peer["channels"] = channels

    def get_peers(self, channel=None):
        """
        Lấy danh sách các peer.

        :param channel:
            - None  => trả về tất cả peer
            - "general" => chỉ trả peer tham gia channel "general"
        :return: list[dict]
        """
        if channel is None or channel == "":
            return list(self.peers.values())

        result = []
        for p in self.peers.values():
            chs = p.get("channels", [])
            if channel in chs:
                result.append(p)
        return result

    def remove_peer(self, peer_id):
        """
        Xoá 1 peer khỏi tracker (khi peer off).
        """
        if peer_id in self.peers:
            del self.peers[peer_id]
