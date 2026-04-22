/**
 * pwa_init.js
 * Registra il Service Worker e gestisce il banner "Installa app".
 * Includi questo file in fondo a TUTTI gli HTML con:
 * <script src="/static/js/pwa_init.js"></script>
 */

// ── 1. Registra Service Worker ──────────────────────────────────────────────
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js', { scope: '/' })
      .then(reg => console.log('[SW] Registrato:', reg.scope))
      .catch(err => console.log('[SW] Errore:', err));
  });
}

// ── 2. Banner "Installa SkillBridge" ────────────────────────────────────────
let deferredPrompt = null;

window.addEventListener('beforeinstallprompt', e => {
  e.preventDefault();
  deferredPrompt = e;

  // Mostra il banner solo se non già installata
  if (!window.matchMedia('(display-mode: standalone)').matches) {
    showInstallBanner();
  }
});

function showInstallBanner() {
  if (document.getElementById('pwa-banner')) return;

  const banner = document.createElement('div');
  banner.id = 'pwa-banner';
  banner.innerHTML = `
    <div style="
      position:fixed; bottom:20px; left:50%; transform:translateX(-50%);
      background:#0d1f2f; border:1px solid rgba(37,132,255,0.4);
      border-radius:14px; padding:14px 20px; display:flex; align-items:center;
      gap:14px; z-index:9999; box-shadow:0 8px 32px rgba(0,0,0,0.5);
      max-width:360px; width:calc(100% - 40px); animation: slideUp .3s ease;
    ">
      <img src="/static/icons/icon-48x48.png" style="width:40px;height:40px;border-radius:10px;"/>
      <div style="flex:1;">
        <div style="font-size:.9rem;font-weight:700;color:#fff;">Installa SkillBridge</div>
        <div style="font-size:.78rem;color:rgba(255,255,255,0.55);">Aggiungila alla schermata home</div>
      </div>
      <button id="pwa-install-btn" style="
        background:#2584ff;border:none;color:#fff;font-family:inherit;
        font-size:.82rem;font-weight:600;padding:8px 14px;border-radius:8px;cursor:pointer;">
        Installa
      </button>
      <button id="pwa-close-btn" style="
        background:none;border:none;color:rgba(255,255,255,0.4);
        font-size:1.1rem;cursor:pointer;padding:4px;">✕</button>
    </div>
    <style>
      @keyframes slideUp {
        from { opacity:0; transform:translateX(-50%) translateY(20px); }
        to   { opacity:1; transform:translateX(-50%) translateY(0); }
      }
    </style>
  `;
  document.body.appendChild(banner);

  document.getElementById('pwa-install-btn').addEventListener('click', async () => {
    if (!deferredPrompt) return;
    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    console.log('[PWA] Scelta utente:', outcome);
    deferredPrompt = null;
    banner.remove();
  });

  document.getElementById('pwa-close-btn').addEventListener('click', () => {
    banner.remove();
    // Non mostrare di nuovo per questa sessione
    sessionStorage.setItem('pwa-banner-dismissed', '1');
  });
}

// ── 3. Notifiche push (chiedi permesso dopo login) ──────────────────────────
window.requestNotificationPermission = async function() {
  if ('Notification' in window && Notification.permission === 'default') {
    const perm = await Notification.requestPermission();
    console.log('[Notifiche]', perm);
  }
};

// Chiedi dopo 3 secondi dalla pagina messaggi
if (window.location.pathname === '/messaggi') {
  setTimeout(() => window.requestNotificationPermission(), 3000);
}

// ── 4. Mostra notifica quando arriva messaggio (anche con app in background) ─
window.showMessageNotification = function(nome, testo) {
  if (document.visibilityState === 'visible') return; // app aperta, non serve
  if (Notification.permission !== 'granted') return;
  new Notification(`📩 ${nome}`, {
    body: testo,
    icon: '/static/icons/icon-192x192.png',
    badge: '/static/icons/icon-72x72.png'
  });
};
