let _token = '';
let _codice = '';

function showMsg(text, type = 'err') {
    const el = document.getElementById('msg-box');
    el.textContent = text;
    el.className = `msg ${type}`;
    el.style.display = 'block';
    setTimeout(() => el.style.display = 'none', 5000);
}

function setLoading(btnId, loading) {
    const btn = document.getElementById(btnId);
    btn.disabled = loading;
    if (loading) btn.innerHTML = '<div class="loader"></div> Attendere...';
    else btn.innerHTML = btn.dataset.label || btn.textContent;
}

function goStep(n) {
    document.querySelectorAll('.step').forEach(s => s.classList.remove('active'));
    document.getElementById('step' + n).classList.add('active');
}

function goStep1() { goStep(1); }

async function step1Submit() {
    const email = document.getElementById('email-input').value.trim();
    if (!email) { showMsg('Inserisci la tua email'); return; }
    document.getElementById('btn1').dataset.label = 'Invia codice';
    setLoading('btn1', true);
    const r = await fetch('/api/reset-password/richiedi', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
    }).then(x => x.json());
    setLoading('btn1', false);
    if (r.ok) {
        _token = r.token || '';
        showMsg('Codice inviato! Controlla la tua email.', 'ok');
        setTimeout(() => goStep(2), 1200);
    } else {
        showMsg(r.error || 'Errore');
    }
}

async function step2Submit() {
    const codice = document.getElementById('codice-input').value.trim();
    if (codice.length < 6) { showMsg('Inserisci il codice a 6 cifre'); return; }
    document.getElementById('btn2').dataset.label = 'Verifica codice';
    setLoading('btn2', true);
    const r = await fetch('/api/reset-password/verifica', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: _token, codice })
    }).then(x => x.json());
    setLoading('btn2', false);
    if (r.ok) {
        _codice = codice;
        goStep(3);
    } else {
        showMsg(r.error || 'Codice errato o scaduto');
    }
}

async function step3Submit() {
    const pw1 = document.getElementById('pw1').value;
    const pw2 = document.getElementById('pw2').value;
    if (pw1.length < 6) { showMsg('La password deve essere di almeno 6 caratteri'); return; }
    if (pw1 !== pw2) { showMsg('Le password non coincidono'); return; }
    document.getElementById('btn3').dataset.label = 'Aggiorna password';
    setLoading('btn3', true);
    const r = await fetch('/api/reset-password/nuova', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: _token, codice: _codice, password: pw1 })
    }).then(x => x.json());
    setLoading('btn3', false);
    if (r.ok) {
        goStep(4);
    } else {
        showMsg(r.error || 'Errore aggiornamento password');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const emailInput = document.getElementById('email-input');
    if (emailInput) emailInput.focus();
});