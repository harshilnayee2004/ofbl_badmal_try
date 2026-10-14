let isSenderChatOpen = false;
let chatSenderSocket = null;

document.addEventListener('DOMContentLoaded', () => {
    if (currentUserId && currentUserRole) {
        connectSenderWebSocket();
    }
});

function toggleSenderChat() {
    const container = document.getElementById('senderChatWidget');
    const icon = document.getElementById('senderChatIcon');
    isSenderChatOpen = !isSenderChatOpen;
    
    if (isSenderChatOpen) {
        container.classList.remove('collapsed');
        icon.innerText = 'expand_more';
        loadGlobalChat();
    } else {
        container.classList.add('collapsed');
        icon.innerText = 'expand_less';
    }
}

async function loadGlobalChat() {
    document.getElementById('chatConversation').classList.add('active');
    
    const messagesContainer = document.getElementById('messagesContainer');
    messagesContainer.innerHTML = '<div class="text-center text-muted small p-2">Loading messages...</div>';
    
    try {
        const res = await fetch(`/chat/history`);
        const data = await res.json();
        
        if (data.status) {
            messagesContainer.innerHTML = '';
            data.object.forEach(msg => {
                const alignStyle = msg.sender_id === currentUserId ? 'sent' : 'received';
                appendMessage(msg.content, alignStyle, msg.sender_email);
            });
            scrollToBottom();
        }
    } catch (err) {
        console.error("Failed to load global chat history", err);
    }
}

function connectSenderWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/socket/chat/ws/${currentUserRole}`;
    
    chatSenderSocket = new WebSocket(wsUrl);
    
    chatSenderSocket.onopen = function() {
        console.log("Global Sender WebSocket Connected for Role:", currentUserRole);
    };
    
    chatSenderSocket.onmessage = function(event) {
        const data = JSON.parse(event.data);
        if (data.type === 'new_message') {
            const alignStyle = data.message.sender_id === currentUserId ? 'sent' : 'received';
            
            if (isSenderChatOpen) {
                appendMessage(data.message.content, alignStyle, data.message.sender_email);
            }
        }
    };
    
    chatSenderSocket.onclose = function() {
        console.log("Global Sender WebSocket Disconnected. Reconnecting in 5s...");
        setTimeout(() => connectSenderWebSocket(), 5000);
    };
}

function appendMessage(content, type, senderEmail = '') {
    const msgs = document.getElementById('messagesContainer');
    if (!msgs) return;
    
    const wrapper = document.createElement('div');
    wrapper.style.display = 'flex';
    wrapper.style.flexDirection = 'column';
    wrapper.style.marginBottom = '5px';
    if (type === 'sent') {
        wrapper.style.alignItems = 'flex-end';
    } else {
        wrapper.style.alignItems = 'flex-start';
    }
    
    if (senderEmail) {
        const senderLabel = document.createElement('small');
        senderLabel.className = 'text-muted';
        senderLabel.style.fontSize = '0.7em';
        senderLabel.style.marginBottom = '2px';
        senderLabel.innerText = senderEmail;
        wrapper.appendChild(senderLabel);
    }
    
    const blob = document.createElement('div');
    blob.className = `message-blob message-${type}`;
    blob.style.marginBottom = '0'; // override default margin
    blob.innerText = content;
    wrapper.appendChild(blob);
    
    msgs.appendChild(wrapper);
    scrollToBottom();
}

function scrollToBottom() {
    const msgs = document.getElementById('messagesContainer');
    if (msgs) msgs.scrollTop = msgs.scrollHeight;
}

async function sendChatMessage() {
    const input = document.getElementById('chatMessageInput');
    const content = input.value.trim();
    if (!content) return;
    
    input.value = '';
    
    try {
        // Appending visually is completely handled by the broadcast WebSocket pipeline globally!
        const res = await fetch('/chat/send', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                content: content
            })
        });
        const data = await res.json();
        if (!data.status) {
            console.error("Failed to send message", data.message);
        }
    } catch (err) {
        console.error("Error sending message", err);
    }
}

document.getElementById('chatMessageInput').addEventListener('keypress', function (e) {
    if (e.key === 'Enter') {
        sendChatMessage();
    }
});
