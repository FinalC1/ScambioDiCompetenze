// socket_chat.js - versione finale
const socket = io({
  transports: ['websocket', 'polling'],
  reconnection: true
});

socket.on('connect', () => console.log('[WS] Connesso'));
socket.on('disconnect', () => console.log('[WS] Disconnesso'));

socket.on('nuovo_messaggio', (msg) => {
  // msg = { id_messaggio, id_mittente, contenuto, ora, out }
  const container = document.getElementById('chat-msgs');
  if (window.activeChatId && (msg.id_mittente === window.activeChatId || msg.out)) {
    if (container) {
      // Evita duplicati
      if (document.querySelector(`.msg-item[data-id="${msg.id_messaggio}"]`)) return;
      const div = document.createElement('div');
      div.className = msg.out ? 'msg-out' : 'msg-in';
      div.setAttribute('data-id', msg.id_messaggio);
      div.innerHTML = `<div class="bbl">${escapeHtml(msg.contenuto)}</div><div class="ts">${msg.ora}</div>`;
      container.appendChild(div);
      container.scrollTop = container.scrollHeight;
    }
  }
  // Aggiorna anteprima nella lista conversazioni
  if (window.updateConvPreview) {
    window.updateConvPreview(msg.id_mittente, msg.contenuto, msg.ora);
  }
});

window.sendMessage = function() {
  if (!window.activeChatId) return;
  const inp = document.getElementById('chat-input');
  const text = inp?.value.trim();
  if (!text) return;
  // Aggiunta ottimistica
  const container = document.getElementById('chat-msgs');
  const now = new Date();
  const ora = `${now.getHours().toString().padStart(2,'0')}:${now.getMinutes().toString().padStart(2,'0')}`;
  const tempId = 'temp_' + Date.now();
  const div = document.createElement('div');
  div.className = 'msg-out';
  div.setAttribute('data-id', tempId);
  div.innerHTML = `<div class="bbl">${escapeHtml(text)}</div><div class="ts">${ora}</div>`;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
  inp.value = '';
  socket.emit('messaggio_privato', {
    destinatario_id: window.activeChatId,
    contenuto: text
  });
};

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/[&<>]/g, function(m) {
    if (m === '&') return '&amp;';
    if (m === '<') return '&lt;';
    if (m === '>') return '&gt;';
    return m;
  });
}