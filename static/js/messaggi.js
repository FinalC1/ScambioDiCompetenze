window.activeChatId = null;
window.activeSenderName = '';
let myUserId = null;
let pollingInterval = null;

window.addEventListener('load', () => {
    loadConversations();

    // Controlla se siamo stati reindirizzati cliccando su "Contatta Insegnante"
    const directId = sessionStorage.getItem('sb_direct_chat_id');
    const directName = sessionStorage.getItem('sb_direct_chat_name');
    if (directId && directName) {
        sessionStorage.removeItem('sb_direct_chat_id');
        sessionStorage.removeItem('sb_direct_chat_name');
        openConv(parseInt(directId), directName);
    }
});

function loadConversations() {
    fetch('/api/messaggi/conversazioni')
        .then(r => r.json())
        .then(data => {
            if (data.ok) {
                renderConvList(data.conversazioni);
            }
        })
        .catch(err => console.error('Errore:', err));
}

function renderConvList(conversations, filter = '') {
    const el = document.getElementById('conv-list');
    const vis = conversations.filter(c =>
        c.nome.toLowerCase().includes(filter.toLowerCase())
    );
    if (vis.length === 0) {
        el.innerHTML = '<div style="padding:20px; text-align:center; color:rgba(255,255,255,0.2); font-size:0.85rem;">Nessuna conversazione attiva</div>';
        return;
    }
    el.innerHTML = vis.map(c => {
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

function startNewChatByCode() {
    const inputEl = document.getElementById('search-code-input');
    const query = inputEl.value.trim();
    if (!query) {
        alert("Inserisci un codice univoco o uno username.");
        return;
    }

    fetch(`/api/utenti/cerca?q=${encodeURIComponent(query)}`)
        .then(r => r.json())
        .then(data => {
            if (data.ok) {
                openConv(data.utente.id, data.utente.nome);
                inputEl.value = '';
            } else {
                alert(data.error || "Utente non trovato.");
            }
        })
        .catch(err => {
            console.error(err);
            alert("Errore durante la ricerca.");
        });
}

function renderChat(userId, userName) {
    myUserId = parseInt(sessionStorage.getItem('sb_my_user_id') || 0);

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
    <div class="msgs" id="chat-msgs"></div>
    <div class="chat-bar">
      <div class="inp-wrap">
        <input type="text" id="chat-input" placeholder="Scrivi un messaggio..."
          onkeydown="if(event.key==='Enter') window.sendMessage()"/>
      </div>
      <button class="send-btn" onclick="window.sendMessage()">
        <svg viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" fill="none">
          <path stroke-linecap="round" stroke-linejoin="round" d="M6 12 3.269 3.125A59.769 59.769 0 0 1 21.485 12 59.768 59.768 0 0 1 3.27 20.875L5.999 12Zm0 0h7.5"/>
        </svg>
      </button>
    </div>
  `;

    fetchChatMessages(userId, true);
}

function fetchChatMessages(userId, scroll = false) {
    fetch(`/api/messaggi/chat/${userId}`)
        .then(r => r.json())
        .then(data => {
            if (data.ok) {
                myUserId = data.my_user_id;
                sessionStorage.setItem('sb_my_user_id', myUserId);
                const container = document.getElementById('chat-msgs');
                if (!container) return;

                container.innerHTML = data.messaggi.map(m => `
          <div class="${m.id_mittente === myUserId ? 'msg-out' : 'msg-in'} msg-item" data-id="${m.id_messaggio}">
            <div class="bbl">${escapeHtml(m.contenuto)}</div>
            <div class="ts">${m.ora || ''}</div>
          </div>
        `).join('');

                if (scroll) {
                    container.scrollTop = container.scrollHeight;
                }
            }
        })
        .catch(err => console.error('Errore caricamento storico messaggi:', err));
}

function openConv(userId, userName) {
    window.activeChatId = userId;
    window.activeSenderName = userName;
    renderChat(userId, userName);

    document.querySelectorAll('.conv-item').forEach(el => {
        if (el.dataset.userId == userId) el.classList.add('active');
        else el.classList.remove('active');
    });

    // AVVIO POLLING AUTOMATICO (Aggiorna la chat in background ogni 2.5 secondi)
    if (pollingInterval) clearInterval(pollingInterval);
    pollingInterval = setInterval(() => {
        if (window.activeChatId === userId) {
            fetchChatMessages(userId, false);
        }
    }, 2500);
}

// CHIAVE DI RISOLUZIONE: INVIO MESSAGGI VIA RICHIESTA HTTP POST (INDISTRUTTIBILE)
window.sendMessage = function() {
    if (!window.activeChatId) return;
    const inp = document.getElementById('chat-input');
    const text = inp ? inp.value.trim() : '';
    if (!text) return;

    // Invio della richiesta HTTP sicura
    fetch('/api/messaggi/invia', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                destinatario_id: window.activeChatId,
                contenuto: text
            })
        })
        .then(r => r.json())
        .then(data => {
            if (data.ok) {
                if (inp) inp.value = '';
                fetchChatMessages(window.activeChatId, true);
                loadConversations();
            } else {
                alert("Impossibile inviare il messaggio: " + data.error);
            }
        })
        .catch(err => {
            console.error("Errore nell'invio del messaggio:", err);
            alert("Errore di rete. Impossibile inviare.");
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