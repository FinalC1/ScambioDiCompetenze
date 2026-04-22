
    // Estrai ID lezione dall'URL
    const lessonId = parseInt(window.location.pathname.split('/').pop());

    window.addEventListener('load', () => {
      loadLesson();
    });

    function loadLesson() {
      fetch(`/api/lezioni/${lessonId}`)
        .then(r => r.json())
        .then(data => {
          if (data.ok) {
            renderLesson(data);
          } else {
            alert('Errore: ' + (data.error || 'Lezione non trovata'));
            window.location.href = '/dashboard';
          }
        })
        .catch(err => {
          console.error('Errore:', err);
          alert('Errore nel caricamento della lezione');
          window.location.href = '/dashboard';
        });
    }

    function renderLesson(data) {
      const l = data.lezione;

      // Titolo e descrizione
      document.getElementById('lesson-title').textContent = l.titolo;
      document.getElementById('lesson-desc').textContent = l.descrizione;

      // Data e ora hero
      document.getElementById('hero-date').textContent = `${l.data_lezione} alle ${l.orario}`;

      // Badge
      const badgesHtml = `
        <span class="badge blue">${l.categoria || 'Lezione'}</span>
        <span class="badge ghost">${l.modalita}</span>
      `;
      document.getElementById('badges-container').innerHTML = badgesHtml;

      // Meta
      document.getElementById('meta-data').textContent = l.data_lezione;
      document.getElementById('meta-orario').textContent = l.orario;
      document.getElementById('meta-posti').textContent = `${data.posti_disponibili} disponibili`;
      document.getElementById('meta-luogo').textContent = l.luogo;

      // Teacher
      document.getElementById('teacher-name').textContent = l.nome_insegnante;

      // Cosa imparerai (dividiamo la descrizione in punti)
      const points = l.descrizione.split('\n').filter(p => p.trim());
      const learnHtml = points.length > 0 
        ? points.map(p => `<li><svg fill="none" viewBox="0 0 24 24" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5" stroke="currentColor"/></svg>${p}</li>`).join('')
        : '<li><svg fill="none" viewBox="0 0 24 24" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5" stroke="currentColor"/></svg>Impara contenuti interessanti</li>';
      document.getElementById('learn-list').innerHTML = learnHtml;

      // Materiali
      const materialiHtml = data.materiali.length > 0
        ? data.materiali.map(m => `
            <div class="material-item">
              <div class="material-icon">
                <svg fill="none" viewBox="0 0 24 24" stroke-width="1.8"><path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" stroke="currentColor"/></svg>
              </div>
              <div class="material-info">
                <strong>${m.nome_materiale}</strong>
                <span>${m.tipo || 'Materiale'}</span>
              </div>
              <a href="#" class="material-dl">Scarica</a>
            </div>
          `).join('')
        : '<p style="color: var(--text-sub); font-size: 0.9rem;">Nessun materiale disponibile.</p>';
      document.getElementById('materiali-container').innerHTML = materialiHtml;

      // Partecipanti
      const partecipantiHtml = data.partecipanti.length > 0
        ? data.partecipanti.map(p => `
            <div class="participant">
              <div class="part-av">${p.nome.charAt(0).toUpperCase()}</div>
              <div>
                <div class="part-name">${p.nome} ${p.cognome}</div>
                <div class="part-role">Partecipante</div>
              </div>
            </div>
          `).join('')
        : '<p style="color: var(--text-sub); font-size: 0.9rem;">Nessun partecipante ancora.</p>';
      document.getElementById('partecipanti-container').innerHTML = partecipantiHtml;

      // Pulsante azione
      renderActionButton(data);
    }

    function renderActionButton(data) {
      const area = document.getElementById('action-area');
      
      if (data.is_teacher) {
        area.innerHTML = `
          <button class="btn-teacher" disabled>
            <svg fill="none" viewBox="0 0 24 24" stroke-width="1.8"><path stroke-linecap="round" stroke-linejoin="round" d="M4.26 10.147a60.438 60.438 0 0 0-.491 6.347A48.62 48.62 0 0 1 12 20.904a48.62 48.62 0 0 1 8.232-4.41 60.46 60.46 0 0 0-.491-6.347m-15.482 0a50.636 50.636 0 0 0-2.658-.813A59.906 59.906 0 0 1 12 3.493a59.903 59.903 0 0 1 10.399 5.84c-.896.248-1.783.52-2.658.814m-15.482 0A50.717 50.717 0 0 1 12 13.489a50.702 50.702 0 0 1 3.741-3.342M6.75 15a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5Zm0 0v-3.675A55.378 55.378 0 0 1 12 8.443m-7.007 11.55A5.981 5.981 0 0 0 6.75 15.75v-1.5" stroke="currentColor"/></svg>
            Sei l'insegnante di questa lezione
          </button>`;
      } else if (data.is_booked) {
        area.innerHTML = `
          <button class="btn-book booked" disabled>
            <svg fill="none" viewBox="0 0 24 24" stroke-width="2.5" width="18" height="18"><path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5" stroke="currentColor"/></svg>
            Prenotato
          </button>
          <button class="btn-contact" onclick="contactTeacher()">
            <svg fill="none" viewBox="0 0 24 24" stroke-width="1.8"><path stroke-linecap="round" stroke-linejoin="round" d="M2.25 12.76c0 1.6 1.123 2.994 2.707 3.227 1.068.157 2.148.279 3.238.364.466.037.893.281 1.153.671L12 21l2.652-3.978c.26-.39.687-.634 1.153-.67 1.09-.086 2.17-.208 3.238-.365 1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0 0 12 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018Z" stroke="currentColor"/></svg>
            Contatta Insegnante
          </button>
          <button class="cancel-link" onclick="cancelBooking()">Annulla prenotazione</button>`;
      } else {
        area.innerHTML = `
          <button class="btn-book" onclick="bookLesson()">Prenota il tuo posto</button>
          <button class="btn-contact" onclick="contactTeacher()">
            <svg fill="none" viewBox="0 0 24 24" stroke-width="1.8"><path stroke-linecap="round" stroke-linejoin="round" d="M2.25 12.76c0 1.6 1.123 2.994 2.707 3.227 1.068.157 2.148.279 3.238.364.466.037.893.281 1.153.671L12 21l2.652-3.978c.26-.39.687-.634 1.153-.67 1.09-.086 2.17-.208 3.238-.365 1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0 0 12 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018Z" stroke="currentColor"/></svg>
            Contatta Insegnante
          </button>
          <p class="tos-note">Prenotando confermi di aver letto il codice di condotta SkillBridge.</p>`;
      }
    }

    function switchTab(name, btn) {
      document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById('tab-' + name).classList.add('active');
    }

    function showToast(title, body) {
      const t = document.getElementById('toast');
      t.querySelector('.toast-title').textContent = title;
      t.querySelector('.toast-body').textContent = body;
      t.classList.add('show');
      setTimeout(() => t.classList.remove('show'), 3500);
    }

    function bookLesson() {
      fetch(`/api/lezioni/${lessonId}/prenota`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'}
      })
      .then(r => r.json())
      .then(data => {
        if (data.ok) {
          showToast('Successo!', 'Prenotazione confermata con successo!');
          setTimeout(() => loadLesson(), 1000);
        } else {
          alert(data.error || 'Errore');
        }
      });
    }

    function cancelBooking() {
      if (confirm('Sei sicuro di voler annullare la prenotazione?')) {
        fetch(`/api/lezioni/${lessonId}/annulla`, {
          method: 'POST',
          headers: {'Content-Type': 'application/json'}
        })
        .then(r => r.json())
        .then(data => {
          if (data.ok) {
            showToast('Annullata', 'Prenotazione annullata.');
            setTimeout(() => loadLesson(), 1000);
          } else {
            alert(data.error || 'Errore');
          }
        });
      }
    }

    function contactTeacher() {
      alert('Funzione messaggi disponibile dalla sezione Messaggi');
      window.location.href = '/messaggi';
    }