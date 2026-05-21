let userData = null;

window.addEventListener('load', () => {
    loadProfilo();
});

document.addEventListener('DOMContentLoaded', () => {
    const settingsBtn = document.getElementById('settingsBtn');
    if (settingsBtn) {
        // Inseriamo l'icona dell'ingranaggio SVG corretta
        settingsBtn.innerHTML = `
      <svg fill="none" viewBox="0 0 24 24" stroke-width="1.8" stroke="currentColor" style="width:18px; height:18px;">
        <path stroke-linecap="round" stroke-linejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.324.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 0 1 1.37.49l1.296 2.247a1.125 1.125 0 0 1-.26 1.43l-1.003.828c-.293.241-.438.613-.43.992a7.723 7.723 0 0 1 0 .255c-.008.378.137.75.43.991l1.004.827c.424.35.534.954.26 1.43l-1.298 2.247a1.125 1.125 0 0 1-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.47 6.47 0 0 1-.22.128c-.331.183-.581.495-.644.869l-.213 1.281c-.09.543-.56.94-1.11.94h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 0 1-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 0 1-1.369-.49l-1.297-2.247a1.125 1.125 0 0 1 .26-1.43l1.004-.827c.292-.24.437-.613.43-.991a6.932 6.932 0 0 1 0-.255c.007-.38-.138-.751-.43-.992l-1.004-.827a1.125 1.125 0 0 1-.26-1.43l1.297-2.247a1.125 1.125 0 0 1 1.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.086.22-.128.332-.183.582-.495.644-.869l.214-1.28Z" />
        <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
      </svg>
    `;

        settingsBtn.addEventListener('click', (e) => {
            e.preventDefault();
            const existingMenu = document.getElementById('settings-menu');
            if (existingMenu) {
                existingMenu.remove();
                return;
            }
            const menu = document.createElement('div');
            menu.id = 'settings-menu';
            menu.style.position = 'fixed';
            menu.style.bottom = '80px';
            menu.style.right = '20px';
            menu.style.backgroundColor = '#0d1f2f';
            menu.style.border = '1px solid rgba(255,255,255,0.1)';
            menu.style.borderRadius = '12px';
            menu.style.padding = '10px';
            menu.style.zIndex = '1000';
            menu.innerHTML = `
        <button id="changeColorBtn" style="display:block; width:100%; background: none; border: none; color: white; padding: 8px; cursor: pointer; text-align: left;">🎨 Cambia colore sfondo</button>
        <button id="resetPwBtn" style="display:block; width:100%; background: none; border: none; color: #ff6060; padding: 8px; cursor: pointer; text-align: left;">🔑 Reimposta password</button>
        <button id="closeMenuBtn" style="display:block; width:100%; background: none; border: none; color: gray; padding: 8px; cursor: pointer; text-align: left;">✕ Chiudi</button>
      `;
            document.body.appendChild(menu);

            document.getElementById('changeColorBtn').onclick = () => {
                menu.remove();
                showThemeSelector();
            };
            document.getElementById('resetPwBtn').onclick = () => {
                window.location.href = '/reset-password';
            };
            document.getElementById('closeMenuBtn').onclick = () => menu.remove();
        });
    }
});

function loadProfilo() {
    fetch('/api/profilo')
        .then(r => r.json())
        .then(data => {
            if (data.ok) {
                userData = data;
                renderProfilo(data);
                populateCompetenceSelect(data.competenze_list);
            }
        })
        .catch(err => console.error('Errore:', err));
}

function renderProfilo(data) {
    const user = data.user;
    const stats = data.stats;

    const initials = (user.nome.charAt(0) + user.cognome.charAt(0)).toUpperCase();
    const avatarBig = document.getElementById('profile-av-big');
    if (avatarBig) avatarBig.textContent = initials;

    const sidebarAv = document.getElementById('sidebar-av');
    if (sidebarAv) sidebarAv.textContent = 'S';

    const fullName = `${user.nome} ${user.cognome}`;
    document.getElementById('profile-name').textContent = fullName;
    document.getElementById('profile-tagline-text').textContent = fullName;
    document.getElementById('profile-bio').textContent = user.descrizione_profilo || 'Bio non ancora compilata';

    document.getElementById('stat-lezioni').textContent = stats.lezioni_date || 0;
    document.getElementById('stat-comp').textContent = stats.competenze || 0;
    document.getElementById('stat-rating').textContent = (stats.media_feedback || 0).toFixed(1);

    renderLezioni(data.lezioni_create);
    renderCompetenze(data.competenze);
    renderFeedback(data.feedback);
}

function renderLezioni(lezioni) {
    const container = document.getElementById('lezioni-container');
    if (lezioni.length === 0) {
        container.innerHTML = '<div class="empty-state">Nessuna lezione creata ancora.</div>';
        return;
    }

    container.innerHTML = lezioni.map((l, i) => `
    <div class="lesson-thumb-card" onclick="window.location.href='/lezione/${l.id_lezione}'" style="position: relative; animation: fadeUp 0.35s both; animation-delay: ${i * 0.05}s">
      <svg viewBox="0 0 400 300" xmlns="http://www.w3.org/2000/svg">
        <rect width="400" height="300" fill="#0f2a3f"/>
        <ellipse cx="200" cy="100" rx="150" ry="60" fill="#1a3d5c" opacity="0.7"/>
        <rect x="60" y="130" width="280" height="20" rx="8" fill="#1e4d6b" opacity="0.5"/>
        <rect x="100" y="160" width="200" height="15" rx="6" fill="#1e4d6b" opacity="0.4"/>
        <rect x="30" y="200" width="340" height="10" rx="5" fill="#1e4d6b" opacity="0.3"/>
        <rect x="0" y="230" width="400" height="70" fill="#0a1f2f"/>
      </svg>
      <div class="lesson-thumb-card-label">${l.titolo}</div>
    </div>
  `).join('');
}

function renderCompetenze(competenze) {
    const container = document.getElementById('comp-grid');
    if (competenze.length === 0) {
        container.innerHTML = '<div class="empty-state" style="grid-column: 1/-1;">Nessuna competenza ancora.</div>';
        return;
    }

    container.innerHTML = competenze.map(c => `
    <div class="comp-card">
      <div class="comp-av">${c.nome_competenza.charAt(0).toUpperCase()}</div>
      <div class="comp-info">
        <strong>${c.nome_competenza}</strong>
        <span>Livello: ${c.livello}</span>
      </div>
      <span class="comp-badge">${c.tipo}</span>
    </div>
  `).join('');
}

function renderFeedback(feedback) {
    const container = document.getElementById('feedback-list');
    if (feedback.length === 0) {
        container.innerHTML = '<div class="empty-state">Nessun feedback ricevuto ancora.</div>';
        return;
    }

    container.innerHTML = feedback.map((f, i) => `
    <div class="feedback-card" style="animation: fadeUp 0.35s both; animation-delay: ${i * 0.05}s">
      <div class="feedback-top">
        <div class="feedback-av a">${f.nome.charAt(0).toUpperCase()}</div>
        <div>
          <div class="feedback-author">${f.nome} ${f.cognome}</div>
        </div>
        <div class="feedback-date">${f.data_feedback}</div>
      </div>
      <div class="stars">
        ${Array(5).fill(0).map(() => `<svg viewBox="0 0 24 24"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>`).join('')}
      </div>
      <p class="feedback-text">${f.commento || 'Nessun commento'}</p>
    </div>
  `).join('');
}

function populateCompetenceSelect(comps) {
  const select = document.getElementById('modal-materia');
  if (select) {
    select.innerHTML = '<option value="" disabled selected>Scegli...</option>';
    comps.forEach(c => {
      const opt = document.createElement('option');
      opt.value = c.id_competenza;
      opt.textContent = c.nome_competenza;
      select.appendChild(opt);
    });
  }
}

function switchTab(name, btn) {
  document.querySelectorAll('.ptab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  btn.classList.add('active');
  document.getElementById('tab-' + name).classList.add('active');
}

function openEditModal() {
  if (!userData) return;
  const user = userData.user;
  document.getElementById('edit-nome').value = user.nome;
  document.getElementById('edit-cognome').value = user.cognome;
  document.getElementById('edit-bio').value = user.descrizione_profilo || '';
  document.getElementById('modal-edit-overlay').classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeEditModal() {
  document.getElementById('modal-edit-overlay').classList.remove('open');
  document.body.style.overflow = '';
}

function closeEditModalOutside(e) {
  if (e.target === document.getElementById('modal-edit-overlay')) closeEditModal();
}

function saveProfile() {
  const nome = document.getElementById('edit-nome').value.trim();
  const cognome = document.getElementById('edit-cognome').value.trim();
  const bio = document.getElementById('edit-bio').value.trim();

  if (!nome || !cognome) {
    alert('Nome e cognome obbligatori');
    return;
  }

  fetch('/api/profilo/aggiorna', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ nome, cognome, descrizione_profilo: bio })
  })
  .then(r => r.json())
  .then(data => {
    if (data.ok) {
      alert('Profilo aggiornato!');
      closeEditModal();
      loadProfilo();
    } else {
      alert(data.error);
    }
  });
}

function openModal() {
  document.getElementById('modal-overlay').classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeModal() {
  document.getElementById('modal-overlay').classList.remove('open');
  document.body.style.overflow = '';
}

function closeModalOutside(e) {
  if (e.target === document.getElementById('modal-overlay')) closeModal();
}

function saveComp() {
  const id_comp = document.getElementById('modal-materia').value;
  const livello = document.getElementById('modal-livello').value;
  const tipo = document.getElementById('modal-tipo').value;

  if (!id_comp) {
    alert('Seleziona una competenza');
    return;
  }

  const btn = document.getElementById('btn-save-comp');
  btn.disabled = true;
  btn.innerHTML = '<div class="loader"></div> Salvataggio...';

  fetch('/api/competenze/aggiungi', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id_competenza: parseInt(id_comp), livello, tipo })
  })
  .then(r => r.json())
  .then(data => {
    btn.disabled = false;
    btn.textContent = 'Salva Competenza';
    if (data.ok) {
      alert('Competenza aggiunta!');
      closeModal();
      loadProfilo();
    }
  });
}

function showThemeSelector() {
  const colors = ['#060f1a', '#0a2a4a', '#1a1a2e', '#2d2d44'];
  const selector = document.createElement('div');
  selector.id = 'theme-selector';
  selector.style.position = 'fixed';
  selector.style.bottom = '80px';
  selector.style.right = '20px';
  selector.style.backgroundColor = '#0d1f2f';
  selector.style.border = '1px solid rgba(255,255,255,0.1)';
  selector.style.borderRadius = '12px';
  selector.style.padding = '10px';
  selector.style.zIndex = '1000';
  selector.style.display = 'flex';
  selector.style.gap = '10px';
  colors.forEach(color => {
    const btn = document.createElement('button');
    btn.style.width = '40px';
    btn.style.height = '40px';
    btn.style.backgroundColor = color;
    btn.style.border = '2px solid white';
    btn.style.borderRadius = '50%';
    btn.style.cursor = 'pointer';
    btn.onclick = () => {
      // CHIAVE DI RISOLUZIONE: Aggiorna sia il body che la variabile CSS `--bg` per modificare il colore a livello globale
      document.documentElement.style.setProperty('--bg', color);
      document.body.style.backgroundColor = color;
      localStorage.setItem('skillbridge_theme', color);
      selector.remove();
    };
    selector.appendChild(btn);
  });
  const closeBtn = document.createElement('button');
  closeBtn.textContent = '✕';
  closeBtn.style.backgroundColor = 'transparent';
  closeBtn.style.border = 'none';
  closeBtn.style.color = 'white';
  closeBtn.style.cursor = 'pointer';
  closeBtn.onclick = () => selector.remove();
  selector.appendChild(closeBtn);
  document.body.appendChild(selector);
}

const savedTheme = localStorage.getItem('skillbridge_theme') || '#060f1a';
document.documentElement.style.setProperty('--bg', savedTheme);
document.body.style.backgroundColor = savedTheme;

document.addEventListener('keydown', e => {
  if (e.key === 'Escape') {
    closeEditModal();
    closeModal();
    const selector = document.getElementById('theme-selector');
    if (selector) selector.remove();
    const menu = document.getElementById('settings-menu');
    if (menu) menu.remove();
  }
});