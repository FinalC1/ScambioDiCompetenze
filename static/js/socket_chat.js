/**
 * socket_chat.js
 * Messaggistica in tempo reale con Socket.IO.
 * Sostituisce completamente il vecchio sistema di polling.
 *
 * Includi in skillbridge-messaggi.html DOPO socket.io.min.js:
 * <script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>
 * <script src="/static/js/socket_chat.js"></script>
 */

// ── Connessione Socket.IO ────────────────────────────────────────────────────
const socket = io({
  transports: ['websocket', 'polling'],
  reconnection: true,
  reconnectionDelay: 1000,
  reconnectionAttempts: 10
});

socket.on('connect', () => {
  console.log('[WS] Connesso:', socket.id);
});

socket.on('disconnect', () => {
  console.log('[WS] Disconnesso, riconnessione...');
});

// ── Ricezione messaggio in tempo reale ──────────────────────────────────────
socket.on('nuovo_messaggio', (msg) => {
  const container = document.getElementById('msgs-container');

  // Se la chat corrente è quella del mittente/destinatario → mostra
  if (window.activeChatId &&
      (msg.id_mittente === window.activeChatId || msg.out)) {

    if (container) {
      // Evita duplicati (il mittente lo ha già aggiunto ottimisticamente)
      if (msg.out && document.querySelector(`[data-id="${msg.id_messaggio}"]`)) return;

      const div = document.createElement('div');
      div.className = msg.out ? 'msg-out' : 'msg-in';
      div.dataset.id = msg.id_messaggio;
      div.innerHTML = `<div class="bbl">${escapeHtml(msg.contenuto)}</div><div class="ts">${msg.ora}</div>`;
      container.appendChild(div);
      container.scrollTop = container.scrollHeight;
    }
  }

  // Aggiorna preview nella lista conversazioni
  updateConvPreview(msg.out ? window.activeChatId : msg.id_mittente, msg.contenuto, msg.ora);

  // Notifica se app non in primo piano
  if (!msg.out && window.activeSenderName) {
    window.showMessageNotification?.(window.activeSenderName, msg.contenuto);
  }
});

// ── Invio messaggio ─────────────────────────────────────────────────────────
window.sendMessage = function() {
  if (!window.activeChatId) return;
  const inp  = document.getElementById('chat-input');
  const text = (inp?.value || '').trim();
  if (!text) return;

  // Mostra subito nella UI (ottimistico)
  const container = document.getElementById('msgs-container');
  if (container) {
    const div = document.createElement('div');
    div.className = 'msg-out';
    const now = new Date();
    const ts  = `${now.getHours().toString().padStart(2,'0')}:${now.getMinutes().toString().padStart(2,'0')}`;
    div.innerHTML = `<div class="bbl">${escapeHtml(text)}</div><div class="ts">${ts}</div>`;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
  }

  inp.value = '';

  // Invia al server tramite WebSocket
  socket.emit('messaggio_privato', {
    destinatario_id: window.activeChatId,
    contenuto: text
  });
};

// ── Helper ───────────────────────────────────────────────────────────────────
function escapeHtml(t) {
  return t.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
          .replace(/"/g,'&quot;').replace(/'/g,'&#039;');
}

function updateConvPreview(userId, testo, ora) {
  // Aggiorna l'anteprima nell'elemento .conv-item corrispondente
  const items = document.querySelectorAll('.conv-item');
  items.forEach(item => {
    if (item.dataset.userId == userId) {
      const prev = item.querySelector('.conv-prev');
      const time = item.querySelector('.conv-time');
      if (prev) prev.textContent = testo;
      if (time) time.textContent = ora;
      // Sposta in cima alla lista
      const list = item.parentElement;
      if (list) list.prepend(item);
    }
  });
}
