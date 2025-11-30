// script.js - BK Chat Web + P2P Hybrid
let username = "";
let currentChannel = null;

// DOM Elements
const usernameInput = document.getElementById('username');
const channelSelect = document.getElementById('channel-select');
const currentChannelName = document.getElementById('current-channel-name');
const messagesDiv = document.getElementById('messages');
const messageInput = document.getElementById('message-input');
const sendBtn = document.getElementById('send-btn');

// Lấy danh sách channel khi trang load
async function loadChannels() {
    try {
        const response = await fetch('/getlist');
        const data = await response.json();
        
        if (data.status === 'success') {
            channelSelect.innerHTML = '<option value="">– Choose a channel –</option>';
            data.channels.forEach(ch => {
                const opt = document.createElement('option');
                opt.value = ch;
                opt.textContent = '# ' + ch;
                channelSelect.appendChild(opt);
            });
        }
    } catch (err) {
        console.error("Không lấy được danh sách channel:", err);
    }
}

// Khởi tạo Peer khi người dùng nhập tên
async function initPeer() {
    if (!username) return;

    const peerData = {
        username: username,
        peer_ip: "127.0.0.1",        // Web sẽ dùng dynamic port
        peer_port: 0,                  // PeerClient sẽ tự chọn port trống
        tracker_ip: "127.0.0.1",
        tracker_port: 8001
    };

    try {
        const res = await fetch('/init-peer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(peerData)
        });
        const result = await res.json();
        if (result.status === 'success') {
            console.log("Peer initialized:", username);
            loadChannels(); // Sau khi init mới được join channel
        } else {
            alert("Lỗi: " + result.message);
        }
    } catch (err) {
        console.error("Init peer failed:", err);
    }
}

// Join channel khi chọn từ dropdown
async function joinChannel(channel) {
    if (!channel || !username) return;

    currentChannel = channel;
    currentChannelName.textContent = '# ' + channel;
    messageInput.disabled = false;
    sendBtn.disabled = false;
    messagesDiv.innerHTML = '<div style="text-align:center;color:#777;padding:20px;">Loading messages...</div>';

    try {
        const res = await fetch('/join-channel', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, channel })
        });
        const data = await res.json();

        if (data.status === 'success') {
            console.log("Joined channel:", channel);
            loadMessages(); // Lấy tin nhắn cũ
        } else {
            alert("Join failed: " + data.message);
            messagesDiv.innerHTML = '<div style="color:red;text-align:center;">Failed to join channel</div>';
        }
    } catch (err) {
        console.error("Join error:", err);
    }
}

// Lấy lịch sử tin nhắn
async function loadMessages() {
    if (!currentChannel) return;

    try {
        const res = await fetch('/get-messages', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, channel: currentChannel })
        });
        const data = await res.json();

        messagesDiv.innerHTML = '';
        if (data.messages && data.messages.length > 0) {
            data.messages.forEach(msg => addMessage(msg));
        } else {
            messagesDiv.innerHTML = '<div style="text-align:center;color:#aaa;">No messages yet. Start chatting!</div>';
        }
        scrollToBottom();
    } catch (err) {
        console.error("Load messages error:", err);
    }
}

// Thêm 1 tin nhắn vào giao diện
function addMessage(msg) {
    const div = document.createElement('div');
    div.className = 'message';
    div.innerHTML = `
        <strong>${msg.username || 'Unknown'}</strong>: ${msg.text || msg.message}
        <br><small>${new Date(msg.timestamp || Date.now()).toLocaleTimeString()}</small>
    `;
    messagesDiv.appendChild(div);
    scrollToBottom();
}

function scrollToBottom() {
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

// Gửi tin nhắn (dùng broadcast trong channel)
async function sendMessage() {
    const text = messageInput.value.trim();
    if (!text || !currentChannel) return;

    try {
        const res = await fetch('/broadcast-peer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                username: username,
                message: text,
                channel: currentChannel
            })
        });
        const data = await res.json();

        if (data.status === 'success') {
            messageInput.value = '';
            // Optimistic UI: hiện tin nhắn ngay lập tức
            addMessage({
                username: username,
                text: text,
                timestamp: new Date().toISOString()
            });
        }
    } catch (err) {
        alert("Send failed!");
        console.error(err);
    }
}

// === EVENT LISTENERS ===
usernameInput.addEventListener('change', (e) => {
    username = e.target.value.trim();
    if (username) {
        initPeer();
    }
});

channelSelect.addEventListener('change', (e) => {
    const channel = e.target.value;
    if (channel) {
        joinChannel(channel);
    }
});

sendBtn.addEventListener('click', sendMessage);
messageInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});

// Nhận tin nhắn real-time từ các peer khác (qua Socket.IO hoặc polling)
// Ở đây dùng polling đơn giản mỗi 2 giây
setInterval(() => {
    if (currentChannel && username) {
        loadMessages(); // Cập nhật tin nhắn mới
    }
}, 2000);

// Load danh sách channel khi trang mở
loadChannels();