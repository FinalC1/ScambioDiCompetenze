window.activeChatId = null;
window.activeSenderName = '';

window.addEventListener('load', () => {
    loadConversations();
});

let myUserId = null;

function loadConversations() {
    fetch('/api/messaggi/conversazioni')
        .then(r => r.json())
        .then(data => {
            if (data.ok) {
                renderConvList(data.conversazioni);
                if (data.conversazioni.length > 0 && !window.activeChatId) {
                    openConv(data.conversazioni[0].id_utente, data.conversazioni[0].nome);
                }
            }
        })
        .catch(err => console.error('Errore:', err));
}

function renderConvList(conversations, filter = '') {
    const el = document.getElementById('conv-list');
    const vis = conversations.filter(c =>
        c.nome.toLowerCase().includes(filter.toLowerCase())
    );
    el.innerHTML = vis.map(c => {
        // CHIAVE DI RISOLUZIONE: il confronto ora avviene tramite ID mittente corretto
        const prev = c.ultimo_msg ? (c.ultimo_mittente_id === myUserId ? 'Tu: ' : '') + c.ultimo_msg : '';
        return `<div class="conv-item${c.id_utente === window.activeChatId ? ' active' : ''}" 
                  data-user-id="${c.id_utente}" 
                  onclick="openConv(${c.id_utente}, '${c.nome.replace(/'/g, "\\'")}')">
      <div class="av-wrap">
        <div class="conv-av">
          <svg viewBox="0 0 44 44">
            <circle cx="22" cy="22" r="22" fill="#0f2a3f"/>
            <text x="22" y="28" text-anchor="middle" font-size="18" font-weight="bold" fill="#fff">
              ${c.nome.charAt(0).toUpperCase()}
            </text>
          </svg>
        </div>
      </div>
      <div class="conv-info">
        <div class="conv-top">
          <span class="conv-name">${c.nome}</span>
          <span class="conv-time">${c.ora || ''}</span>
        </div>
        <div class="conv-prev">${prev.substring(0, 40)}${prev.length > 40 ? '...' : ''}</div>
      </div>
    </div>`;
    }).join('');
}

window.updateConvPreview = function(userId, testo, ora) {
    const items = document.querySelectorAll(`.conv-item[data-user-id="${userId}"]`);
    items.forEach(item => {
        const prevEl = item.querySelector('.conv-prev');
        const timeEl = item.querySelector('.conv-time');
        if (prevEl) prevEl.textContent = (userId === myUserId ? 'Tu: ' : '') + testo;
        if (timeEl) timeEl.textContent = ora;
        const list = item.parentElement;
        if (list) list.prepend(item);
    });
};

function filterConvs(v) {
    fetch('/api/messaggi/conversazioni')
        .then(r => r.json())
        .then(data => {
            if (data.ok) renderConvList(data.conversazioni, v);
        });
}

function renderChat(userId, userName) {
    fetch(`/api/messaggi/chat/${userId}`)
        .then(r => r.json())
        .then(data => {
                if (data.ok) {
                    myUserId = data.my_user_id;
                    document.getElementById('chat-area').innerHTML = `
          <div class="chat-hdr">
            <div class="chat-hdr-l">
              <div class="hdr-av">
                <svg viewBox="0 0 44 44">
                  <circle cx="22" cy="22" r="22" fill="#0f2a3f"/>
                  <text x="22" y="28" text-anchor="middle" font-size="18" font-weight="bold" fill="#fff">
                    ${userName.charAt(0).toUpperCase()}
                  </text>
                </svg>
              </div>
              <div>
                <div class="hdr-name">${escapeHtml(userName)}</div>
                <div class="hdr-online">Online</div>
              </div>
            </div>
          </div>
          <div class="msgs" id="chat-msgs">
            ${data.messaggi.map(m => `
              <div class="${m.id_mittente === data.my_user_id ? 'msg-out' : 'msg-in'} msg-item" data-id="${m.id_messaggio}">
                <div class="bbl">${escapeHtml(m.contenuto)}</div>
                <div class="ts">${m.ora || ''}</div>
              </div>
            `).join('')}
          </div>
          <div class="chat-bar">
            <div class="inp-wrap">
              <input type="text" id="chat-input" placeholder="Scrivi un messaggio..."
                onkeydown="if(event.key==='Enter') window.sendMessage && window.sendMessage()"/>
            </div>
            <button class="send-btn" onclick="window.sendMessage && window.sendMessage()">
              <svg viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" fill="none">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 12 3.269 3.125A59.769 59.769 0 0 1 21.485 12 59.768 59.768 0 0 1 3.27 20.875L5.999 12Zm0 0h7.5"/>
              </svg>
            </button>
          </div>
        `;
        const msgsDiv = document.getElementById('chat-msgs');
        if (msgsDiv) msgsDiv.scrollTop = msgsDiv.scrollHeight;
      }
    })
    .catch(err => console.error('Errore caricamento conversazione:', err));
}

function openConv(userId, userName) {
  window.activeChatId = userId;
  window.activeSenderName = userName;
  renderChat(userId, userName);
  document.querySelectorAll('.conv-item').forEach(el => {
    if (el.dataset.userId == userId) el.classList.add('active');
    else el.classList.remove('active');
  });
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/[&<>]/g, function(m) {
    if (m === '&') return '&amp;';
    if (m === '<') return '&lt;';
    if (m === '>') return '&gt;';
    return m;
  });
}