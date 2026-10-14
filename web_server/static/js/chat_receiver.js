let isReceiverChatOpen = false;
let unreadCount = 0;
let chatWebSocket = null;

document.addEventListener('DOMContentLoaded', () => {
    if (currentUserId) {
        loadReceiverHistory();
        connectChatWebSocket();
    }
});

function toggleReceiverChat() {
    const container = document.getElementById('receiverChatWidget');
    const icon = document.getElementById('receiverChatIcon');
    isReceiverChatOpen = !isReceiverChatOpen;
    
    if (isReceiverChatOpen) {
        container.classList.remove('collapsed');
        icon.innerText = 'expand_more';
        clearUnreadBadge();
        scrollToBottomRx();
    } else {
        container.classList.add('collapsed');
        icon.innerText = 'expand_less';
    }
}

async function loadReceiverHistory() {
    try {
        const res = await fetch(`/chat/history`);
        const data = await res.json();
        if (data.status) {
            const msgs = document.getElementById('messagesContainerRx');
            msgs.innerHTML = '';
            data.object.forEach(msg => {
                appendReceiverMessage(msg.content);
            });
            scrollToBottomRx();
        }
    } catch (err) {
        console.error("Failed to load history", err);
    }
}

function connectChatWebSocket() {
    // Protocol configuration
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/socket/chat/ws/${currentUserRole}`;
    
    chatWebSocket = new WebSocket(wsUrl);
    
    chatWebSocket.onopen = function() {
        console.log("Chat WebSocket Connected for User ID:", currentUserId);
    };
    
    chatWebSocket.onmessage = function(event) {
        const data = JSON.parse(event.data);
        if (data.type === 'new_message') {
            appendReceiverMessage(data.message.content, data.message.sender_email);
            
            if (!isReceiverChatOpen) {
                // pop open the chat box automatically
                toggleReceiverChat();
            } else {
                // animate the bell if already open
                const icon = document.querySelector('.chat-header-rx .material-symbols-outlined');
                if (icon) {
                    icon.classList.remove('ringing');
                    void icon.offsetWidth; // trigger reflow
                    icon.classList.add('ringing');
                }
            }
        }
    };
    
    chatWebSocket.onclose = function() {
        console.log("Chat WebSocket Disconnected. Reconnecting in 5s...");
        setTimeout(() => connectChatWebSocket(), 5000);
    };
}

function appendReceiverMessage(content, senderEmail = '') {
    const msgs = document.getElementById('messagesContainerRx');
    const wrapper = document.createElement('div');
    wrapper.style.display = 'flex';
    wrapper.style.flexDirection = 'column';
    wrapper.style.alignItems = 'flex-start';
    wrapper.style.marginBottom = '5px';
    
    if (senderEmail) {
        const senderLabel = document.createElement('small');
        senderLabel.className = 'text-muted';
        senderLabel.style.fontSize = '0.7em';
        senderLabel.style.marginBottom = '2px';
        senderLabel.innerText = senderEmail;
        wrapper.appendChild(senderLabel);
    }

    const blob = document.createElement('div');
    blob.className = 'message-blob-rx message-received-rx';
    blob.style.marginBottom = '0';
    blob.innerText = content;
    wrapper.appendChild(blob);
    
    msgs.appendChild(wrapper);
    scrollToBottomRx();
}

function scrollToBottomRx() {
    const msgs = document.getElementById('messagesContainerRx');
    msgs.scrollTop = msgs.scrollHeight;
}

function clearUnreadBadge() {
    unreadCount = 0;
    const badge = document.getElementById('chatUnreadBadge');
    badge.style.display = 'none';
}
