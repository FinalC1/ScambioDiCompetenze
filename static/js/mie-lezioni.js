window.addEventListener('load', () => {
    loadMieLezioni();
  });

  const rawUser = (localStorage.getItem('sb_username') || '').trim();
  const firstName = rawUser.split(/\s+/)[0];
  const displayName = firstName ? firstName.charAt(0).toUpperCase() + firstName.slice(1).toLowerCase() : 'U';
  document.getElementById('sidebar-av').textContent = 'S';

  function loadMieLezioni() {
    fetch('/api/mie-lezioni')
      .then(r => r.json())
      .then(data => {
        if (data.ok) {
          renderTab('frequentando', data.frequentando);
          renderTab('insegnando', data.insegnando);
        }
      })
      .catch(err => console.error('Errore:', err));
  }

  function renderTab(tabName, lessons) {
    const container = document.getElementById(`list-${tabName}`);
    if (lessons.length === 0) {
      container.innerHTML = '<div class="empty"><svg fill="none" viewBox="0 0 24 24" stroke-width="1.8"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" stroke="currentColor"/></svg>Nessuna lezione.</div>';
      return;
    }

    container.innerHTML = lessons.map((l, i) => `
      <div class="lesson-row" style="animation-delay:${i*0.07}s">
        <div class="lesson-thumb">
          <svg viewBox="0 0 90 68" xmlns="http://www.w3.org/2000/svg">
            <rect width="90" height="68" fill="#0f2a3f"/>
            <g stroke="rgba(255,255,255,0.07)" stroke-width="0.8" fill="none">
              <line x1="0" y1="68" x2="45" y2="0"/><line x1="90" y1="68" x2="45" y2="0"/>
              <line x1="0" y1="34" x2="90" y2="34"/>
            </g>
          </svg>
        </div>
        <div class="lesson-info">
          <div class="lesson-badges">
            <span class="badge-cat">${l.categoria || 'Lezione'}</span>
            <span class="badge-mode">${l.modalita}</span>
          </div>
          <div class="lesson-name">${l.titolo}</div>
          <div class="lesson-meta-row">
            <span>
              <svg fill="none" viewBox="0 0 24 24" stroke-width="1.8"><path stroke-linecap="round" stroke-linejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 0 1 2.25-2.25h13.5A2.25 2.25 0 0 1 21 7.5v11.25m-18 0A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75" stroke="currentColor"/></svg>
              ${l.data_lezione}
            </span>
            <span>
              <svg fill="none" viewBox="0 0 24 24" stroke-width="1.8"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" stroke="currentColor"/></svg>
              ${l.orario}
            </span>
            ${l.nome_insegnante ? `<span class="role-tag">
              <svg fill="none" viewBox="0 0 24 24" stroke-width="1.8"><path stroke-linecap="round" stroke-linejoin="round" d="M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.501 20.118a7.5 7.5 0 0 1 14.998 0A17.933 17.933 0 0 1 12 21.75c-2.676 0-5.216-.584-7.499-1.632Z" stroke="currentColor"/></svg>
              ${l.nome_insegnante}
            </span>` : ''}
          </div>
        </div>
        <button class="btn-detail" onclick="window.location.href='/lezione/${l.id_lezione}'">Vedi</button>
      </div>
    `).join('');
  }

  function switchTab(tabName) {
    document.querySelectorAll('.toggle-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.lesson-list').forEach(l => l.style.display = 'none');
    const tabId = tabName === 'insegnando' ? 'tab-ins' : 'tab-freq';
    document.getElementById(tabId).classList.add('active');
    document.getElementById(`list-${tabName}`).style.display = 'flex';
  }