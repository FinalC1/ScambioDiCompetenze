// Sidebar avatar
  const rawUser = (localStorage.getItem('sb_username') || '').trim();
  const firstName = rawUser.split(/\s+/)[0];
  const display = firstName ? firstName.charAt(0).toUpperCase() + firstName.slice(1).toLowerCase() : 'U';
  document.getElementById('sidebar-av').textContent = 'S';

  let currentCat = 'tutto';
  let currentQuery = '';

  // Event listeners
  document.getElementById('search-input').addEventListener('keydown', e => {
    if (e.key === 'Enter') doSearch();
  });

  document.getElementById('search-input').addEventListener('input', e => {
    currentQuery = e.target.value.trim().toLowerCase();
    render();
  });

  function selectCat(btn) {
    document.querySelectorAll('.cat-pill').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    currentCat = btn.dataset.cat;
    render();
  }

  function doSearch() {
    currentQuery = document.getElementById('search-input').value.trim().toLowerCase();
    render();
  }

  function render() {
    fetch('/api/lezioni?q=' + encodeURIComponent(currentQuery) + '&categoria=' + encodeURIComponent(currentCat === 'tutto' ? '' : currentCat))
      .then(r => r.json())
      .then(data => {
        if (data.ok) {
          renderResults(data.lezioni);
        } else {
          console.error('Errore:', data.error);
        }
      })
      .catch(err => console.error('Errore fetch:', err));
  }

  function renderResults(lezioni) {
    const area = document.getElementById('results-area');

    if (lezioni.length === 0) {
      const label = currentQuery ? `"${currentQuery}"` : 'in questa categoria';
      area.innerHTML = `
        <div class="empty-state">
          <p>Nessun risultato trovato per ${label}</p>
          <a onclick="resetFilters()">Reset filtri</a>
        </div>`;
    } else {
      const cards = lezioni.map((l, i) => `
        <div class="skill-card" style="animation-delay:${i * 0.05}s" onclick="window.location.href='/lezione/${l.id_lezione}'">
          <div class="skill-card-top">
            <div class="skill-icon">
              <svg fill="none" viewBox="0 0 24 24" stroke-width="1.8">
                <circle cx="11" cy="11" r="8" stroke="currentColor"/>
                <path stroke-linecap="round" d="m21 21-4.35-4.35" stroke="currentColor"/>
              </svg>
            </div>
            <span class="skill-cat-badge">${l.categoria || 'Lezione'}</span>
          </div>
          <h3>${l.titolo}</h3>
          <p>${l.descrizione}</p>
          <button class="btn-vedi">Vedi Lezione</button>
          <a class="link-richiedi" href="/lezione/${l.id_lezione}">Dettagli →</a>
        </div>`).join('');

      area.innerHTML = `<div class="skills-grid">${cards}</div>`;
    }

    // Mostra/nascondi suggerimenti
    document.getElementById('suggestions-section').style.display =
      (currentCat === 'tutto' && !currentQuery) ? 'block' : 'none';
  }

  function resetFilters() {
    currentQuery = '';
    currentCat = 'tutto';
    document.getElementById('search-input').value = '';
    document.querySelectorAll('.cat-pill').forEach(p => p.classList.remove('active'));
    document.querySelector('[data-cat="tutto"]').classList.add('active');
    render();
  }

  // Carica suggerimenti
  function loadSuggestions() {
    fetch('/api/lezioni?q=&categoria=')
      .then(r => r.json())
      .then(data => {
        if (data.ok && data.lezioni.length > 0) {
          const lezioni = data.lezioni.slice(0, 2);
          const grid = document.getElementById('suggestions-grid');
          grid.innerHTML = lezioni.map(l => `
            <div class="sug-card" onclick="window.location.href='/lezione/${l.id_lezione}'">
              <div class="sug-thumb">
                <svg class="sug-thumb-placeholder" viewBox="0 0 130 140" xmlns="http://www.w3.org/2000/svg">
                  <rect width="130" height="140" fill="#0f2a3f"/>
                  <rect x="0" y="0" width="130" height="70" fill="#0d2235" opacity="0.9"/>
                  <ellipse cx="65" cy="35" rx="50" ry="20" fill="#1a3d5c" opacity="0.5"/>
                  <rect x="0" y="70" width="130" height="70" fill="#0a1e2f"/>
                  <line x1="0" y1="140" x2="130" y2="0" stroke="rgba(255,255,255,0.04)" stroke-width="1"/>
                  <line x1="130" y1="140" x2="0" y2="0" stroke="rgba(255,255,255,0.04)" stroke-width="1"/>
                </svg>
              </div>
              <div class="sug-body">
                <div>
                  <div class="sug-body-top">
                    <h4>${l.titolo}</h4>
                    <span class="sug-mode">${l.modalita}</span>
                  </div>
                  <p class="sug-desc">${l.descrizione}</p>
                </div>
                <div class="sug-footer">
                  <div class="sug-meta">
                    <span><svg fill="none" viewBox="0 0 24 24" stroke-width="1.8"><path stroke-linecap="round" stroke-linejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 0 1 2.25-2.25h13.5A2.25 2.25 0 0 1 21 7.5v11.25m-18 0A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75" stroke="currentColor"/></svg>${l.data_lezione}</span>
                    <span><svg fill="none" viewBox="0 0 24 24" stroke-width="1.8"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" stroke="currentColor"/></svg>${l.orario}</span>
                  </div>
                  <a class="sug-link" href="/lezione/${l.id_lezione}">Dettagli</a>
                </div>
              </div>
            </div>
          `).join('');
        }
      })
      .catch(err => console.error('Errore caricamento suggerimenti:', err));
  }

  // Carica al load
  window.addEventListener('load', () => {
    render();
    loadSuggestions();
  });