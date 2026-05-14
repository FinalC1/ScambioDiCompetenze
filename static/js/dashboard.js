// Carica dati al caricamento della pagina
window.addEventListener('load', () => {
  loadDashboard();
});

// Leggi username dal localStorage (fallback)
const raw = localStorage.getItem('sb_username') || 'Utente';
const firstName = raw.trim().split(/\s+/)[0];
const display = firstName.charAt(0).toUpperCase() + firstName.slice(1).toLowerCase();
fetch('/api/me')
  .then(r => r.json())
  .then(data => {
    if (data.ok) {
      const nome = data.user.nome;
      document.getElementById('welcome-title').textContent = `Bentornato, ${nome}!`;
    }
  });
document.querySelector('.sidebar-logo .avatar').textContent = 'S';

function loadDashboard() {
  fetch('/api/dashboard')
    .then(r => r.json())
    .then(data => {
      if (data.ok) {
        document.getElementById('stat-lezioni').textContent = data.stats.lezioni_frequentate;
        document.getElementById('stat-punti').textContent = data.stats.punti;
        document.getElementById('stat-feedback').textContent = (data.stats.media_feedback || 0) + ' / 5';
        renderLessons(data.lezioni_consigliate);
        renderSkills(data.competenze);
        populateCompetenceSelect(data.competenze_list);
      } else {
        console.error('Errore:', data.error);
        document.getElementById('lezioni-container').innerHTML = '<div class="error-msg">Impossibile caricare i dati. Riprova più tardi.</div>';
      }
    })
    .catch(err => {
      console.error('Errore fetch:', err);
      document.getElementById('lezioni-container').innerHTML = '<div class="error-msg">Errore di connessione al server. Verifica la tua rete o riprova tra poco.</div>';
    });
}

function renderLessons(lessons) {
  const container = document.getElementById('lezioni-container');
  if (!lessons || lessons.length === 0) {
    container.innerHTML = '<p style="color: var(--text-sub);">Nessuna lezione disponibile.</p>';
    return;
  }
  container.innerHTML = lessons.map(l => `
    <div class="lesson-card">
      <div class="lesson-thumb-placeholder">
        <svg viewBox="0 0 120 90" xmlns="http://www.w3.org/2000/svg">
          <rect width="120" height="90" fill="#0f2a3f"/>
          <ellipse cx="60" cy="30" rx="40" ry="18" fill="#1a3d5c" opacity="0.7"/>
          <rect x="20" y="40" width="80" height="5" rx="2.5" fill="#1e4d6b" opacity="0.5"/>
          <rect x="30" y="50" width="60" height="4" rx="2" fill="#1e4d6b" opacity="0.4"/>
          <rect x="10" y="60" width="100" height="3" rx="1.5" fill="#1e4d6b" opacity="0.3"/>
          <rect x="0" y="70" width="120" height="20" fill="#0a1f2f"/>
        </svg>
        <span class="lesson-badge">${l.categoria || 'Lezione'}</span>
      </div>
      <div class="lesson-body">
        <div class="lesson-body-top">
          <h3>${l.titolo}</h3>
          <span class="lesson-mode">${l.modalita}</span>
        </div>
        <p class="lesson-desc">${l.descrizione}</p>
        <div class="lesson-meta">
          <span><svg fill="none" viewBox="0 0 24 24" stroke-width="1.8"><path stroke-linecap="round" stroke-linejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 0 1 2.25-2.25h13.5A2.25 2.25 0 0 1 21 7.5v11.25m-18 0A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75m-18 0v-7.5A2.25 2.25 0 0 1 5.25 9h13.5A2.25 2.25 0 0 1 21 11.25v7.5" stroke="currentColor"/></svg>${l.data_lezione}</span>
          <span><svg fill="none" viewBox="0 0 24 24" stroke-width="1.8"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" stroke="currentColor"/></svg>${l.orario}</span>
        </div>
        <div class="lesson-footer">
          <span class="lesson-teacher">Insegnante: <strong>${l.nome_insegnante}</strong></span>
          <button class="btn-detail" onclick="window.location.href='/lezione/${l.id_lezione}'">Vedi Dettagli</button>
        </div>
      </div>
    </div>
  `).join('');
}

function renderSkills(skills) {
  const container = document.getElementById('skill-container');
  if (!skills || skills.length === 0) {
    container.innerHTML = '<p style="font-size: 0.85rem; color: var(--text-sub); text-align: center;">Nessuna competenza ancora.</p>';
    return;
  }
  container.innerHTML = skills.map(s => `
    <div class="skill-item">
      <div class="skill-avatar blue">${s.nome_competenza.charAt(0).toUpperCase()}</div>
      <div class="skill-info">
        <strong>${s.nome_competenza}</strong>
        <span>Livello: ${s.livello}</span>
      </div>
      <span class="skill-badge">${s.tipo}</span>
    </div>
  `).join('');
}

function populateCompetenceSelect(comps) {
  const select = document.getElementById('modal-competenza');
  if (!comps) return;
  comps.forEach(c => {
    const opt = document.createElement('option');
    opt.value = c.id_competenza;
    opt.textContent = c.nome_competenza;
    select.appendChild(opt);
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

function publishLesson() {
  const titolo = document.getElementById('modal-titolo').value.trim();
  const descrizione = document.getElementById('modal-descrizione').value.trim();
  const id_comp = document.getElementById('modal-competenza').value;
  const data = document.getElementById('modal-data').value;
  const orario = document.getElementById('modal-orario').value;
  const modalita = document.getElementById('modal-modalita').value;
  const luogo = document.getElementById('modal-luogo').value.trim();

  if (!titolo || !data || !orario) {
    alert('Titolo, data e orario sono obbligatori!');
    return;
  }

  fetch('/api/lezioni/crea', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      titolo, descrizione, id_competenza: id_comp,
      data_lezione: data, orario, modalita, luogo,
      numero_massimo_partecipanti: 10, durata: 60
    })
  })
  .then(r => r.json())
  .then(data => {
    if (data.ok) {
      alert('Lezione creata con successo!');
      closeModal();
      loadDashboard();
    } else {
      alert('Errore: ' + (data.error || 'Sconosciuto'));
    }
  });
}

document.addEventListener('keydown', e => { if(e.key==='Escape') closeModal(); });