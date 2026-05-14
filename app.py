"""
SkillBridge — app.py
Backend Flask con:
  - Flask-SocketIO  → messaggi in tempo reale (WebSocket)
  - PostgreSQL       → database cloud Supabase (pooler)
  - Reset password   → 2FA via email con logging
"""

import os, re, secrets, hashlib, time, smtplib
from datetime import date, datetime, timedelta
from functools import wraps

from flask import Flask, send_from_directory, request, redirect, session, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
import psycopg2
import psycopg2.extras
from psycopg2 import pool, OperationalError

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURAZIONE
# ─────────────────────────────────────────────────────────────────────────────
app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.environ.get('SECRET_KEY', 'skillbridge_secret_2024')

# SocketIO con CORS per Render
socketio = SocketIO(app,
    cors_allowed_origins='*',
    async_mode='gevent',
    logger=False,
    engineio_logger=False
)

# ── Database PostgreSQL (Supabase) ──────────────────────────────────────────
DB_URL = os.environ.get(
    'DB_URL',
    'postgresql://postgres:PASSWORD@HOST:5432/postgres'  # modifica con la tua URL Supabase
)

# Forza uso connection pooler (porta 6543) se è Supabase
if 'supabase' in DB_URL and ':5432' in DB_URL:
    DB_URL = DB_URL.replace(':5432', ':6543')
    print('[DB] Utilizzo connection pooler su porta 6543')

# Pool di connessioni
try:
    db_pool = pool.SimpleConnectionPool(1, 5, DB_URL, connect_timeout=10)
    print('[DB] Pool creato con successo')
except Exception as e:
    print(f'[DB] ERRORE pool: {e}')
    db_pool = None

def get_db(retries=2):
    if db_pool is None:
        raise Exception("Pool DB non disponibile")
    for i in range(retries):
        try:
            conn = db_pool.getconn()
            conn.autocommit = False
            return conn
        except OperationalError as e:
            print(f'[DB] Tentativo {i+1} fallito: {e}')
            if i == retries - 1:
                raise
            time.sleep(2 ** i)
    raise Exception("Impossibile connettersi al DB")

def put_db(conn):
    if db_pool and conn:
        db_pool.putconn(conn)

# ── Email ───────────────────────────────────────────────────────────────────
MAIL_FROM = os.environ.get('MAIL_FROM', 'skillbridge.einaudi@gmail.com')
MAIL_PASS = os.environ.get('MAIL_PASS', 'jwlu iret icve xuea')  # <- sostituisci con App Password valida

def send_email(dest, subject, body):
    if not MAIL_FROM or not MAIL_PASS:
        print('[MAIL] Credenziali mancanti')
        return False
    try:
        s = smtplib.SMTP('smtp.gmail.com', 587, timeout=15)
        s.starttls()
        s.login(MAIL_FROM, MAIL_PASS)
        msg = f'Subject: {subject}\nContent-Type: text/plain; charset=utf-8\n\n{body}'
        s.sendmail(MAIL_FROM, dest, msg.encode('utf-8'))
        s.quit()
        print(f'[MAIL] ✅ Inviata a {dest}')
        return True
    except smtplib.SMTPAuthenticationError:
        print('[MAIL] ❌ Autenticazione fallita - controlla MAIL_PASS (deve essere App Password)')
        return False
    except Exception as e:
        print(f'[MAIL] ❌ Errore: {e}')
        return False

# ─────────────────────────────────────────────────────────────────────────────
# PAROLACCE
# ─────────────────────────────────────────────────────────────────────────────
PAROLACCE = [
    'cazzo','minchia','vaffanculo','stronzo','stronza','merda','coglione',
    'bastardo','bastarda','puttana','fanculo','frocio','troia','cagna',
    'negro','negra','cornuto','fuck','shit','bitch','asshole','bastard','dick'
]

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def is_valid_email(e):
    return re.search(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}$', e)

def is_valid_username(u):
    return re.match(r'^[a-zA-Z0-9_.]{3,30}$', u)

def censura(t):
    if not t: return t
    for p in PAROLACCE:
        t = re.sub(re.escape(p), p[0]+'*'*(len(p)-2)+p[-1], t, flags=re.IGNORECASE)
    return t

def genera_codice():
    h = secrets.token_hex(4).upper()
    return f"SB-{h[:4]}-{h[4:]}"

def login_required(f):
    @wraps(f)
    def d(*a, **kw):
        if 'user_id' not in session:
            return jsonify({'ok': False, 'error': 'Non autenticato'}), 401
        return f(*a, **kw)
    return d

def page_guard(f):
    @wraps(f)
    def d(*a, **kw):
        if 'user_id' not in session:
            return redirect('/login')
        return f(*a, **kw)
    return d

def ok(**kw):    return jsonify({'ok': True,  **kw})
def err(m, c=400): return jsonify({'ok': False, 'error': m}), c

# ─────────────────────────────────────────────────────────────────────────────
# DB INIT
# ─────────────────────────────────────────────────────────────────────────────
def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS utente (
      id_utente           SERIAL PRIMARY KEY,
      nome                VARCHAR(50)  NOT NULL,
      cognome             VARCHAR(50)  NOT NULL,
      email               VARCHAR(100) NOT NULL UNIQUE,
      password            VARCHAR(255) NOT NULL,
      data_registrazione  DATE,
      descrizione_profilo TEXT,
      foto_profilo        VARCHAR(255),
      username            VARCHAR(30)  UNIQUE,
      codice_univoco      VARCHAR(20)  UNIQUE
    );
    CREATE TABLE IF NOT EXISTS competenza (
      id_competenza   SERIAL PRIMARY KEY,
      nome_competenza VARCHAR(100) NOT NULL,
      descrizione     TEXT,
      categoria       VARCHAR(50)
    );
    CREATE TABLE IF NOT EXISTS utente_competenza (
      id_utente     INT REFERENCES utente(id_utente)     ON DELETE CASCADE,
      id_competenza INT REFERENCES competenza(id_competenza) ON DELETE CASCADE,
      livello       VARCHAR(20),
      tipo          VARCHAR(20) NOT NULL,
      PRIMARY KEY (id_utente, id_competenza, tipo)
    );
    CREATE TABLE IF NOT EXISTS lezione (
      id_lezione                  SERIAL PRIMARY KEY,
      titolo                      VARCHAR(100) NOT NULL,
      descrizione                 TEXT,
      data_lezione                DATE,
      orario                      TIME,
      durata                      INT,
      modalita                    VARCHAR(20),
      luogo                       VARCHAR(100),
      numero_massimo_partecipanti INT,
      id_insegnante               INT REFERENCES utente(id_utente)     ON DELETE CASCADE,
      id_competenza               INT REFERENCES competenza(id_competenza) ON DELETE SET NULL
    );
    CREATE TABLE IF NOT EXISTS prenotazione (
      id_prenotazione  SERIAL PRIMARY KEY,
      data_prenotazione DATE,
      stato            VARCHAR(20),
      id_utente        INT REFERENCES utente(id_utente)  ON DELETE CASCADE,
      id_lezione       INT REFERENCES lezione(id_lezione) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS feedback (
      id_feedback   SERIAL PRIMARY KEY,
      voto          INT CHECK (voto BETWEEN 1 AND 5),
      commento      TEXT,
      data_feedback DATE,
      id_lezione    INT REFERENCES lezione(id_lezione) ON DELETE CASCADE,
      id_utente     INT REFERENCES utente(id_utente)  ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS materiale (
      id_materiale      SERIAL PRIMARY KEY,
      id_lezione        INT REFERENCES lezione(id_lezione) ON DELETE CASCADE,
      tipo              VARCHAR(20) NOT NULL,
      titolo            VARCHAR(100),
      url_risorsa       TEXT,
      data_caricamento  TIMESTAMP DEFAULT NOW()
    );
    CREATE TABLE IF NOT EXISTS messaggio (
      id_messaggio    SERIAL PRIMARY KEY,
      id_mittente     INT NOT NULL REFERENCES utente(id_utente) ON DELETE CASCADE,
      id_destinatario INT NOT NULL REFERENCES utente(id_utente) ON DELETE CASCADE,
      contenuto       TEXT NOT NULL,
      data_invio      TIMESTAMP DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_msg_mitt ON messaggio(id_mittente);
    CREATE INDEX IF NOT EXISTS idx_msg_dest ON messaggio(id_destinatario);
    CREATE TABLE IF NOT EXISTS reset_password (
      id         SERIAL PRIMARY KEY,
      id_utente  INT NOT NULL REFERENCES utente(id_utente) ON DELETE CASCADE,
      token      VARCHAR(64) NOT NULL UNIQUE,
      codice     VARCHAR(8)  NOT NULL,
      scadenza   TIMESTAMP   NOT NULL,
      usato      BOOLEAN DEFAULT FALSE
    );
    """)
    conn.commit()
    cur.close()
    put_db(conn)
    print('[DB] Tabelle pronte.')

# ─────────────────────────────────────────────────────────────────────────────
# PWA — manifest e service worker
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/manifest.json')
def manifest():
    return send_from_directory('static', 'manifest.json')

@app.route('/sw.js')
def service_worker():
    resp = send_from_directory('static', 'sw.js')
    resp.headers['Service-Worker-Allowed'] = '/'
    resp.headers['Cache-Control'] = 'no-cache'
    return resp

@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static', 'favicon.ico')

# ─────────────────────────────────────────────────────────────────────────────
# PAGINE HTML
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/')
def home():
    return redirect('/dashboard' if 'user_id' in session else '/login')

@app.route('/login')
def login_page():    return send_from_directory('templates','skillbridge-login.html')
@app.route('/register')
def register_page(): return send_from_directory('templates','skillbridge-register.html')
@app.route('/reset-password')
def reset_pw_page(): return send_from_directory('templates','skillbridge-reset-password.html')
@app.route('/dashboard')
@page_guard
def dashboard_page(): return send_from_directory('templates','skillbridge-dashboard.html')
@app.route('/cerca')
@page_guard
def search_page():    return send_from_directory('templates','skillbridge-search.html')
@app.route('/lezione/<int:id>')
@page_guard
def lesson_page(id):  return send_from_directory('templates','skillbridge-lesson.html')
@app.route('/mie-lezioni')
@page_guard
def mie_lezioni_page(): return send_from_directory('templates','skillbridge-mie-lezioni.html')
@app.route('/messaggi')
@page_guard
def messaggi_page():  return send_from_directory('templates','skillbridge-messaggi.html')
@app.route('/profilo')
@page_guard
def profilo_page():   return send_from_directory('templates','skillbridge-profilo.html')

# ─────────────────────────────────────────────────────────────────────────────
# API: AUTH
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/api/login', methods=['POST'])
def api_login():
    d = request.get_json()
    lid = (d.get('email') or '').strip().lower()
    pw  = d.get('password','')
    if not lid or not pw: return err('Email/username e password obbligatori')
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        "SELECT * FROM utente WHERE (LOWER(email)=%s OR LOWER(username)=%s) AND password=%s",
        (lid, lid, hash_pw(pw))
    )
    user = cur.fetchone()
    cur.close()
    put_db(conn)
    if not user: return err('Credenziali errate',401)
    session.update({'user_id':user['id_utente'],'user_name':user['nome'],
                    'user_cognome':user['cognome'],'user_username':user.get('username','')})
    return ok(user={'id':user['id_utente'],'nome':user['nome'],'cognome':user['cognome'],
                    'username':user.get('username','')})

@app.route('/api/register', methods=['POST'])
def api_register():
    d=request.get_json()
    nome    =(d.get('nome')    or '').strip()
    cognome =(d.get('cognome') or '').strip()
    email   =(d.get('email')   or '').strip().lower()
    pw      = d.get('password','')
    bio     = censura((d.get('bio') or '').strip())
    username=(d.get('username')or '').strip().lower()

    if not nome or not cognome: return err('Nome e cognome obbligatori')
    if not is_valid_email(email): return err('Email non valida')
    if len(pw)<6: return err('Password minimo 6 caratteri')
    if username and not is_valid_username(username):
        return err('Username non valido (3-30 caratteri: lettere, numeri, _, .)')

    conn = get_db()
    cur = conn.cursor()
    try:
        if not username:
            base=re.sub(r'[^a-z0-9_.]','', (cognome+'.'+nome).lower())[:25] or 'user'
            username, i = base, 0
            while True:
                cur.execute("SELECT id_utente FROM utente WHERE username=%s",(username,))
                if not cur.fetchone(): break
                i+=1; username=f'{base}{i}'
        codice=genera_codice()
        while True:
            cur.execute("SELECT id_utente FROM utente WHERE codice_univoco=%s",(codice,))
            if not cur.fetchone(): break
            codice=genera_codice()
        cur.execute(
            "INSERT INTO utente (nome,cognome,email,password,descrizione_profilo,"
            "username,codice_univoco,data_registrazione) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            (nome,cognome,email,hash_pw(pw),bio,username,codice,date.today())
        )
        conn.commit()
        cur.close()
        put_db(conn)
        send_email(email,'Benvenuto in SkillBridge!',
            f'Ciao {nome},\n\nBenvenuto in SkillBridge!\n'
            f'Username: @{username}\nCodice univoco: {codice}\n\n'
            f'Il codice serve per farti trovare nella chat.\n\nIl team di SkillBridge')
        return ok(message='Registrazione completata!')
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return err('Email già registrata')
    except Exception as e:
        conn.rollback()
        print(f'[REG] {e}')
        return err('Errore registrazione')

@app.route('/api/logout', methods=['GET','POST'])
def api_logout():
    session.clear()
    return redirect('/login')

@app.route('/logout')
def logout_redirect():
    return redirect('/api/logout')

@app.route('/api/me')
def api_me():
    if 'user_id' not in session: return err('Non autenticato',401)
    return ok(user={'id':session['user_id'],'nome':session['user_name'],
                    'cognome':session.get('user_cognome',''),'username':session.get('user_username','')})

# ─────────────────────────────────────────────────────────────────────────────
# API: RESET PASSWORD (2FA mail) — con logging e controllo errori
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/api/reset-password/richiedi', methods=['POST'])
def api_reset_richiedi():
    try:
        data = request.get_json()
        if not data:
            return err('Dati mancanti', 400)
        email = (data.get('email') or '').strip().lower()
        if not email:
            return err('Email obbligatoria', 400)
        
        print(f'[RESET] Richiesta per email: {email}')
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT id_utente,nome FROM utente WHERE LOWER(email)=%s", (email,))
        user = cur.fetchone()
        if not user:
            cur.close()
            put_db(conn)
            print(f'[RESET] Email non trovata: {email}')
            # Per sicurezza rispondiamo ok (non riveliamo esistenza)
            return ok(message="Se l'email è registrata riceverai un codice.")
        
        # Invalida vecchi token
        cur.execute("UPDATE reset_password SET usato=TRUE WHERE id_utente=%s AND usato=FALSE", (user['id_utente'],))
        token = secrets.token_urlsafe(32)
        codice = str(secrets.randbelow(900000)+100000)
        scad = datetime.now() + timedelta(minutes=15)
        cur.execute("INSERT INTO reset_password (id_utente, token, codice, scadenza) VALUES (%s, %s, %s, %s)",
                    (user['id_utente'], token, codice, scad))
        conn.commit()
        cur.close()
        put_db(conn)
        
        # Invia email
        subject = "SkillBridge — Codice verifica reset password"
        body = f"Ciao {user['nome']},\n\nCodice di verifica: {codice}\nValido 15 minuti.\n\nSe non hai richiesto il reset, ignora questa mail."
        success = send_email(email, subject, body)
        if not success:
            print(f'[RESET] Invio email fallito per {email}')
            return err("Errore nell'invio del codice. Riprova più tardi.", 500)
        
        print(f'[RESET] Codice inviato a {email}')
        return ok(token=token, message='Codice inviato!')
    except Exception as e:
        print(f'[RESET] Errore generale: {e}')
        return err("Errore interno del server", 500)

@app.route('/api/reset-password/verifica', methods=['POST'])
def api_reset_verifica():
    d=request.get_json()
    token=(d.get('token') or '').strip(); codice=(d.get('codice') or '').strip()
    if not token or not codice: return err('Dati mancanti')
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM reset_password WHERE token=%s AND usato=FALSE AND scadenza>NOW()",(token,))
    row_=cur.fetchone()
    cur.close(); put_db(conn)
    if not row_: return err('Token scaduto o non valido',400)
    if row_['codice']!=codice: return err('Codice errato',400)
    return ok(message='Codice corretto.')

@app.route('/api/reset-password/nuova', methods=['POST'])
def api_reset_nuova():
    d=request.get_json()
    token=(d.get('token') or '').strip(); codice=(d.get('codice') or '').strip(); pw=d.get('password','')
    if not token or not codice or not pw: return err('Dati mancanti')
    if len(pw)<6: return err('Password minimo 6 caratteri')
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM reset_password WHERE token=%s AND usato=FALSE AND scadenza>NOW()",(token,))
    row_=cur.fetchone()
    if not row_ or row_['codice']!=codice:
        cur.close(); put_db(conn); return err('Token o codice non valido',400)
    cur.execute("UPDATE utente SET password=%s WHERE id_utente=%s",(hash_pw(pw),row_['id_utente']))
    cur.execute("UPDATE reset_password SET usato=TRUE WHERE token=%s",(token,))
    conn.commit()
    cur.close(); put_db(conn)
    return ok(message='Password aggiornata!')

# ─────────────────────────────────────────────────────────────────────────────
# API: DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/api/dashboard')
@login_required
def api_dashboard():
    uid=session['user_id']
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT COUNT(*) AS n FROM prenotazione WHERE id_utente=%s AND stato='Confermata'",(uid,))
    freq=cur.fetchone()['n'] or 0
    cur.execute("""SELECT COALESCE(ROUND(AVG(f.voto::numeric),1),0) AS m FROM feedback f
                   JOIN lezione l ON f.id_lezione=l.id_lezione WHERE l.id_insegnante=%s""",(uid,))
    media=float(cur.fetchone()['m'] or 0)
    cur.execute("SELECT COUNT(*) AS n FROM lezione WHERE id_insegnante=%s",(uid,))
    ins_n=cur.fetchone()['n'] or 0
    cur.execute("""SELECT l.id_lezione,l.titolo,l.descrizione,l.data_lezione::text,
                          l.orario::text,l.durata,l.modalita,l.luogo,l.numero_massimo_partecipanti,
                          u.nome||' '||u.cognome AS nome_insegnante, c.nome_competenza AS categoria
                   FROM lezione l JOIN utente u ON l.id_insegnante=u.id_utente
                   LEFT JOIN competenza c ON l.id_competenza=c.id_competenza
                   WHERE l.id_insegnante!=%s AND l.data_lezione>=CURRENT_DATE
                     AND l.id_lezione NOT IN (
                         SELECT id_lezione FROM prenotazione WHERE id_utente=%s AND stato!='Annullata')
                   ORDER BY l.data_lezione ASC LIMIT 3""",(uid,uid))
    cons = [dict(r) for r in cur.fetchall()]
    cur.execute("""SELECT c.nome_competenza,uc.livello,uc.tipo FROM utente_competenza uc
                   JOIN competenza c ON uc.id_competenza=c.id_competenza
                   WHERE uc.id_utente=%s ORDER BY c.nome_competenza""",(uid,))
    comps = [dict(r) for r in cur.fetchall()]
    cur.execute("SELECT id_competenza,nome_competenza FROM competenza ORDER BY nome_competenza")
    cl = [dict(r) for r in cur.fetchall()]
    cur.close()
    put_db(conn)
    return ok(stats={'lezioni_frequentate':freq,'punti':ins_n*50+freq*10,'media_feedback':media},
              lezioni_consigliate=cons, competenze=comps, competenze_list=cl)

# ─────────────────────────────────────────────────────────────────────────────
# API: LEZIONI (esempio, mantieni le tue route originali)
# Per brevità includo solo le route essenziali; tu puoi mantenere il tuo codice originale
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/api/lezioni')
def api_lezioni():
    cat=request.args.get('categoria','').strip(); q=request.args.get('q','').strip()
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    sql="""SELECT l.id_lezione,l.titolo,l.descrizione,l.data_lezione::text,l.orario::text,
                  l.durata,l.modalita,l.luogo,l.numero_massimo_partecipanti,l.id_insegnante,
                  u.nome||' '||u.cognome AS nome_insegnante,
                  c.nome_competenza AS categoria,c.id_competenza
           FROM lezione l JOIN utente u ON l.id_insegnante=u.id_utente
           LEFT JOIN competenza c ON l.id_competenza=c.id_competenza
           WHERE l.data_lezione>=CURRENT_DATE"""
    p=[]
    if cat: sql+=" AND c.nome_competenza=%s"; p.append(cat)
    if q:   sql+=" AND (l.titolo ILIKE %s OR l.descrizione ILIKE %s OR c.nome_competenza ILIKE %s)"; p+=[f'%{q}%']*3
    sql+=" ORDER BY c.nome_competenza ASC, l.data_lezione ASC LIMIT 100"
    cur.execute(sql,p)
    r=[dict(x) for x in cur.fetchall()]
    cur.close(); put_db(conn)
    return ok(lezioni=r)

@app.route('/api/lezioni/crea', methods=['POST'])
@login_required
def api_crea_lezione():
    d=request.get_json(); uid=session['user_id']
    if not d.get('titolo') or not d.get('data_lezione') or not d.get('orario'):
        return err('Titolo, data e orario obbligatori')
    if not d.get('id_competenza'): return err('Seleziona una competenza')
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""INSERT INTO lezione (titolo,descrizione,id_competenza,id_insegnante,
                       data_lezione,orario,modalita,luogo,numero_massimo_partecipanti,durata)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id_lezione""",
            (d['titolo'],d.get('descrizione',''),d['id_competenza'],uid,
             d['data_lezione'],d['orario'],d.get('modalita','Online'),
             d.get('luogo',''),int(d.get('numero_massimo_partecipanti') or 10),
             int(d.get('durata') or 60)))
        new_id=cur.fetchone()[0]
        conn.commit()
        cur.close(); put_db(conn)
        return ok(message='Lezione creata!',id_lezione=new_id)
    except Exception as e:
        conn.rollback()
        print(f'[CREA] {e}')
        return err('Errore creazione lezione')

# ... (inserisci qui tutte le altre route API: /api/lezioni/<int:id>, /api/mie-lezioni, /api/competenze, /api/profilo, /api/messaggi, ecc.)
# Per non appesantire, le allego nel messaggio successivo se necessario, oppure puoi mantenere le tue originali
# purché sostituiscano ogni `conn.close()` con `put_db(conn)` e usino `get_db()`.

# ENDPOINT KEEP-ALIVE
@app.route('/api/ping')
def ping():
    return ok(message='pong')

# ─────────────────────────────────────────────────────────────────────────────
# WEBSOCKET
# ─────────────────────────────────────────────────────────────────────────────
@socketio.on('connect')
def on_connect():
    if 'user_id' not in session:
        return False
    uid = session['user_id']
    join_room(f'user_{uid}')
    print(f'[WS] Utente {uid} connesso')

@socketio.on('disconnect')
def on_disconnect():
    uid = session.get('user_id')
    if uid:
        leave_room(f'user_{uid}')
        print(f'[WS] Utente {uid} disconnesso')

@socketio.on('messaggio_privato')
def on_messaggio_privato(data):
    uid = session.get('user_id')
    dest_id = data.get('destinatario_id')
    contenuto = (data.get('contenuto') or '').strip()
    if not uid or not dest_id or not contenuto:
        return
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT id_utente FROM utente WHERE id_utente=%s", (dest_id,))
        if not cur.fetchone():
            cur.close(); put_db(conn); return
        cur.execute(
            "INSERT INTO messaggio (id_mittente,id_destinatario,contenuto) VALUES (%s,%s,%s) RETURNING id_messaggio,TO_CHAR(data_invio,'HH24:MI') AS ora",
            (uid, dest_id, contenuto)
        )
        row_ = cur.fetchone()
        conn.commit()
        cur.close(); put_db(conn)
        msg_payload = {
            'id_messaggio': row_['id_messaggio'],
            'id_mittente': uid,
            'contenuto': contenuto,
            'ora': row_['ora'],
        }
        emit('nuovo_messaggio', {**msg_payload, 'out': True}, room=f'user_{uid}')
        emit('nuovo_messaggio', {**msg_payload, 'out': False}, room=f'user_{dest_id}')
    except Exception as e:
        print(f'[WS MSG] {e}')

if __name__ == '__main__':
    init_db()
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)