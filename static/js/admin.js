/* admin.js */
function switchTab(tab, btn) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-section').forEach(s => s.style.display = 'none');
    btn.classList.add('active');
    document.getElementById('section-' + tab).style.display = 'block';
    document.getElementById('tab-title').textContent = btn.textContent;

    if (tab === 'utenti') loadUtenti();
    if (tab === 'lezioni') loadLezioni();
    if (tab === 'competenze') loadCompetenze();
}

function loadUtenti() {
    fetch('/api/admin/utenti')
        .then(r => r.json())
        .then(data => {
            if (data.ok) {
                document.getElementById('utenti-tbody').innerHTML = data.utenti.map(u => `
          <tr>
            <td>${u.id_utente}</td>
            <td>${u.nome} ${u.cognome}</td>
            <td>@${u.username}</td>
            <td>${u.email}</td>
            <td>${u.codice_univoco}</td>
            <td><button class="btn-del" onclick="deleteUtente(${u.id_utente})">Elimina</button></td>
          </tr>
        `).join('');
            }
        })
        .catch(err => console.error("Errore caricamento utenti:", err));
}

function deleteUtente(id) {
    if (confirm("Sei sicuro di voler eliminare definitivamente questo utente?")) {
        fetch(`/api/admin/utenti/${id}`, { method: 'DELETE' })
            .then(r => r.json())
            .then(data => {
                alert(data.message || data.error);
                loadUtenti();
            })
            .catch(err => console.error(err));
    }
}

function loadLezioni() {
    fetch('/api/admin/lezioni')
        .then(r => r.json())
        .then(data => {
            if (data.ok) {
                document.getElementById('lezioni-tbody').innerHTML = data.lezioni.map(l => `
          <tr>
            <td>${l.id_lezione}</td>
            <td>${l.titolo}</td>
            <td>${l.nome_insegnante}</td>
            <td>${l.data_lezione}</td>
            <td>${l.orario}</td>
            <td><button class="btn-del" onclick="deleteLezione(${l.id_lezione})">Rimuovi</button></td>
          </tr>
        `).join('');
            }
        })
        .catch(err => console.error("Errore caricamento lezioni:", err));
}

function deleteLezione(id) {
    if (confirm("Sei sicuro di voler rimuovere questo corso dal sistema?")) {
        fetch(`/api/admin/lezioni/${id}`, { method: 'DELETE' })
            .then(r => r.json())
            .then(data => {
                alert(data.message || data.error);
                loadLezioni();
            })
            .catch(err => console.error(err));
    }
}

function loadCompetenze() {
    fetch('/api/admin/competenze')
        .then(r => r.json())
        .then(data => {
            if (data.ok) {
                document.getElementById('competenze-tbody').innerHTML = data.competenze.map(c => `
          <tr>
            <td>${c.id_competenza}</td>
            <td>${c.nome_competenza}</td>
            <td>${c.categoria}</td>
            <td><button class="btn-del" onclick="deleteCompetenza(${c.id_competenza})">Rimuovi</button></td>
          </tr>
        `).join('');
            }
        })
        .catch(err => console.error("Errore caricamento competenze:", err));
}

function addCompetenza() {
    const nome_competenza = document.getElementById('comp-nome').value.trim();
    const categoria = document.getElementById('comp-categoria').value.trim();
    const descrizione = document.getElementById('comp-desc').value.trim();

    if (!nome_competenza || !categoria) {
        alert("Specifica nome e categoria.");
        return;
    }

    fetch('/api/admin/competenze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nome_competenza, categoria, descrizione })
        })
        .then(r => r.json())
        .then(data => {
            alert(data.message || data.error);
            if (data.ok) {
                document.getElementById('comp-nome').value = '';
                document.getElementById('comp-categoria').value = '';
                document.getElementById('comp-desc').value = '';
                loadCompetenze();
            }
        })
        .catch(err => console.error(err));
}

function deleteCompetenza(id) {
    if (confirm("Sei sicuro di voler rimuovere questa materia?")) {
        fetch(`/api/admin/competenze/${id}`, { method: 'DELETE' })
            .then(r => r.json())
            .then(data => {
                alert(data.message || data.error);
                loadCompetenze();
            })
            .catch(err => console.error(err));
    }
}

window.addEventListener('load', () => {
    loadUtenti();
});