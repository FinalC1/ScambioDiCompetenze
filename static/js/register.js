const form = document.getElementById('register-form');
const btnRegister = document.getElementById('btn-register');

function showToast(title, body, type = 'info') {
    const toast = document.getElementById('toast');
    toast.className = `toast ${type}`;
    toast.querySelector('.toast-title').textContent = title;
    toast.querySelector('.toast-body').textContent = body;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 4000);
}

function clearErrors() {
    document.querySelectorAll('.field.error').forEach(f => {
        f.classList.remove('error');
        f.querySelector('.error-message').classList.remove('show');
        f.querySelector('.error-message').textContent = '';
    });
}

function showFieldError(fieldId, message) {
    const field = document.getElementById(fieldId).parentElement;
    field.classList.add('error');
    const errorEl = field.querySelector('.error-message');
    if (errorEl) {
        errorEl.textContent = message;
        errorEl.classList.add('show');
    }
}

function handleSubmit(event) {
    event.preventDefault();
    clearErrors();

    const nome = document.getElementById('nome').value.trim();
    const cognome = document.getElementById('cognome').value.trim();
    const email = document.getElementById('email').value.trim().toLowerCase();
    const password = document.getElementById('password').value;
    const bio = document.getElementById('bio').value.trim();
    const username = document.getElementById('username').value.trim(); // Risolto ReferenceError

    if (!nome || !cognome) {
        showFieldError('nome', 'Nome e cognome obbligatori');
        return;
    }

    if (!email || !email.includes('@')) {
        showFieldError('email', 'Email valida obbligatoria');
        return;
    }

    if (password.length < 6) {
        showFieldError('password', 'Password minimo 6 caratteri');
        return;
    }

    btnRegister.disabled = true;
    btnRegister.classList.add('loading');
    btnRegister.innerHTML = '<div class="loader"></div> Registrazione in corso...';

    fetch('/api/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                nome,
                cognome,
                email,
                password,
                bio,
                username
            })
        })
        .then(r => r.json())
        .then(data => {
            btnRegister.disabled = false;
            btnRegister.classList.remove('loading');
            btnRegister.textContent = 'Registrati';

            if (data.ok) {
                showToast('Successo!', data.message, 'success');
                form.reset();
                setTimeout(() => {
                    window.location.href = '/login';
                }, 2000);
            } else {
                showToast('Errore', data.error || 'Errore durante la registrazione', 'error');
                if (data.error && data.error.toLowerCase().includes('email')) {
                    showFieldError('email', data.error);
                }
            }
        })
        .catch(err => {
            btnRegister.disabled = false;
            btnRegister.classList.remove('loading');
            btnRegister.textContent = 'Registrati';
            console.error('Errore:', err);
            showToast('Errore', 'Errore di rete. Riprova.', 'error');
        });
}

document.getElementById('password').addEventListener('keypress', e => {
    if (e.key === 'Enter') handleSubmit(e);
});