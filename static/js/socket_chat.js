// socket_chat.js - Versione per evitare i duplicati
const socket = io({
    transports: ['websocket', 'polling'],
    reconnection: true
});

socket.on('connect', () => console.log('[WS] WebSocket connesso in background'));
socket.on('disconnect', () => console.log('[WS] WebSocket scollegato'));

socket.on('nuovo_messaggio', (msg) => {
    // Lasciamo che sia il polling di messaggi.js a gestire il rendering per evitare conflitti e duplicati
    if (window.activeChatId && msg.id_mittente === window.activeChatId) {
        if (typeof fetchChatMessages === 'function') {
            fetchChatMessages(window.activeChatId, true);
        }
    }
});