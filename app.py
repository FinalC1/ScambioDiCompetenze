# CHIAVE DI RISOLUZIONE WEBSOCKET SU RENDER:
# Eseguire il monkey patching all'inizio assoluto del programma.
from gevent import monkey
monkey.patch_all()

"""
SkillBridge - app.py
Backend Flask con:
  - Flask-SocketIO -> messaggi in tempo reale (Websocket)
  - PostgreSQL     -> database cloud Supabase (pooler)
  - Reset password -> 2FA via email con logging
"""

import os
import re
import secrets
import hashlib
import time
import smtplib as smtp
from datetime import date, datetime, timedelta
from functools import wraps

from flask import Flask, send_from_directory, request, redirect, session, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
import psycopg2
import psycopg2.extras
from psycopg2 import pool, OperationalError

from email.mime.text import MIMEText
from email.header import Header

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURAZIONE
# ─────────────────────────────────────────────────────────────────────────────
app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.environ.get('SECRET_KEY', 'skillbridge_secret_2024')

# WebSocket — usa gevent su Render
socketio = SocketIO(app,
    cors_allowed_origins='*',
    async_mode='gevent',
    logger=False,
    engineio_logger=False
)

# ── Database PostgreSQL (Supabase) ──────────────────────────────────────────
DB_URL = os.environ.get(
    'DB_URL',
    'postgresql://postgres:PASSWORD@HOST:6543/postgres'
)

# Configurazione del connection pooler per gestire connessioni concorrenti
try:
    db_pool = pool.SimpleConnectionPool(1, 10, dsn=DB_URL)
    print("[DB] Connection pool inizializzato con successo.")
except Exception as e:
    print(f"[DB ERROR] Errore inizializzazione pool: {e}")
    db_pool = None

# ── Email ───────────────────────────────────────────────────────────────────
MAIL_FROM = os.environ.get('MAIL_FROM', 'skillbridge.einaudi@gmail.com')
MAIL_PASS = os.environ.get('MAIL_PASS', 'jwlu iret icve xuea')

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
def get_db():
    if db_pool:
        return db_pool.getconn()
    return psycopg2.connect(DB_URL)

def release_db(conn):
    if db_pool:
        db_pool.putconn(conn)
    else:
        conn.close()

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

def send_email(dest, subject, body):
    try:
        msg = MIMEText(body, 'plain', 'utf-8')
        msg['Subject'] = Header(subject, 'utf-8')
        msg['From'] = MAIL_FROM
        msg['To'] = dest

        s = smtp.SMTP('smtp.gmail.com', 587, timeout=10)
        s.starttls()
        s.login(MAIL_FROM, MAIL_PASS)
        s.sendmail(MAIL_FROM, [dest], msg.as_string())
        s.quit()
        print(f"[MAIL] Email inviata con successo a {dest}")
    except Exception as e:
        print(f'[MAIL ERROR] {e}')

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
    d = request.get_json() or {}
    lid = (d.get('email') or '').strip().lower()
    pw  = d.get('password','')
    if not lid or not pw: return err('Email/username e password obbligatori')
    conn = None
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT * FROM utente WHERE (LOWER(email)=%s OR LOWER(username)=%s) AND password=%s",
            (lid, lid, hash_pw(pw))
        )
        user = cur.fetchone()
        cur.close()
        if not user:
            return err('Credenziali errate', 401)
        
        session.update({
            'user_id': user['id_utente'],
            'user_name': user['nome'],
            'user_cognome': user['cognome'],
            'user_username': user.get('username', '')
        })
        return ok(user={
            'id': user['id_utente'],
            'nome': user['nome'],
            'cognome': user['cognome'],
            'username': user.get('username', '')
        })
    except Exception as e:
        print(f'[LOGIN ERROR] {e}')
        return err('Errore durante l\'accesso')
    finally:
        if conn:
            release_db(conn)

@app.route('/api/register', methods=['POST'])
def api_register():
    d = request.get_json() or {}
    nome    = (d.get('nome')    or '').strip()
    cognome = (d.get('cognome') or '').strip()
    email   = (d.get('email')   or '').strip().lower()
    pw      = d.get('password','')
    bio     = censura((d.get('bio') or '').strip())
    username= (d.get('username') or '').strip().lower()

    if not nome or not cognome: return err('Nome e cognome obbligatori')
    if not is_valid_email(email): return err('Email non valida')
    if len(pw) < 6: return err('Password minimo 6 caratteri')
    
    conn = None
    try:
        conn = get_db()
        cur = conn.cursor()
        if username:
            if not is_valid_username(username):
                cur.close()
                return err('Username non valido (3-30 caratteri: lettere, numeri, _, .)')
            cur.execute("SELECT id_utente FROM utente WHERE username=%s", (username,))
            if cur.fetchone():
                cur.close()
                return err('Username già in uso')
        else:
            base = re.sub(r'[^a-z0-9_.]', '', (cognome + '.' + nome).lower())[:25] or 'user'
            username, i = base, 0
            while True:
                cur.execute("SELECT id_utente FROM utente WHERE username=%s", (username,))
                if not cur.fetchone(): break
                i += 1; username = f'{base}{i}'
                
        codice = genera_codice()
        while True:
            cur.execute("SELECT id_utente FROM utente WHERE codice_univoco=%s", (codice,))
            if not cur.fetchone(): break
            codice = genera_codice()
            
        cur.execute(
            "INSERT INTO utente (nome,cognome,email,password,descrizione_profilo,"
            "username,codice_univoco,data_registrazione) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            (nome, cognome, email, hash_pw(pw), bio, username, codice, date.today())
        )
        conn.commit()
        cur.close()
        
        send_email(email, 'Benvenuto in SkillBridge!',
            f'Ciao {nome},\n\nBenvenuto in SkillBridge!\n'
            f'Username: @{username}\nCodice univoco: {codice}\n\n'
            f'Il codice serve per farti trovare dagli altri studenti nella chat.\n\nIl team di SkillBridge')
        return ok(message='Registrazione completata!')
    except Exception as e:
        if conn: conn.rollback()
        print(f'[REGISTRATION ERROR] {e}')
        return err('Email o username già registrati')
    finally:
        if conn:
            release_db(conn)

@app.route('/api/logout', methods=['GET','POST'])
def api_logout():
    session.clear()
    return redirect('/login')

@app.route('/logout')
def logout_redirect():
    return redirect('/api/logout')

@app.route('/api/me')
def api_me():
    if 'user_id' not in session: return err('Non autenticato', 401)
    return ok(user={
        'id': session['user_id'],
        'nome': session['user_name'],
        'cognome': session.get('user_cognome', ''),
        'username': session.get('user_username', '')
    })

# ─────────────────────────────────────────────────────────────────────────────
# API: RESET PASSWORD (2FA mail)
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/api/reset-password/richiedi', methods=['POST'])
def api_reset_richiedi():
    data = request.get_json() or {}
    email = (data.get('email') or '').strip().lower()
    if not email: return err('Email obbligatoria')
    conn = None
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT id_utente,nome FROM utente WHERE LOWER(email)=%s", (email,))
        user = cur.fetchone()
        if not user:
            cur.close()
            return ok(message="Se l'email è registrata riceverai un codice.")
        
        cur.execute("UPDATE reset_password SET usato=TRUE WHERE id_utente=%s AND usato=FALSE", (user['id_utente'],))
        token = secrets.token_urlsafe(32)
        codice = str(secrets.randbelow(900000) + 100000)
        scad = datetime.now() + timedelta(minutes=15)
        cur.execute("INSERT INTO reset_password (id_utente,token,codice,scadenza) VALUES (%s,%s,%s,%s)",
                    (user['id_utente'], token, codice, scad))
        conn.commit()
        cur.close()
        
        send_email(email, 'SkillBridge — Codice verifica reset password',
            f"Ciao {user['nome']},\n\nCodice di verifica: {codice}\nValido 15 minuti.\n\n"
            f"Se non hai richiesto il reset, ignora questa mail.")
        return ok(token=token, message='Codice inviato!')
    except Exception as e:
        if conn: conn.rollback()
        print(f'[RESET REQ ERROR] {e}')
        return err('Errore durante la richiesta di reset')
    finally:
        if conn:
            release_db(conn)

@app.route('/api/reset-password/verifica', methods=['POST'])
def api_reset_verifica():
    d = request.get_json() or {}
    token = (d.get('token') or '').strip()
    codice = (d.get('codice') or '').strip()
    if not token or not codice: return err('Dati mancanti')
    conn = None
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM reset_password WHERE token=%s AND usato=FALSE AND scadenza>NOW()", (token,))
        row_ = cur.fetchone()
        cur.close()
        if not row_: return err('Token scaduto o non valido', 400)
        if row_['codice'] != codice: return err('Codice errato', 400)
        return ok(message='Codice corretto.')
    except Exception as e:
        print(f'[RESET VERIFY ERROR] {e}')
        return err('Errore durante la verifica')
    finally:
        if conn:
            release_db(conn)

@app.route('/api/reset-password/nuova', methods=['POST'])
def api_reset_nuova():
    d = request.get_json() or {}
    token = (d.get('token') or '').strip()
    codice = (d.get('codice') or '').strip()
    pw = d.get('password', '')
    if not token or not codice or not pw: return err('Dati mancanti')
    if len(pw) < 6: return err('Password minimo 6 caratteri')
    conn = None
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM reset_password WHERE token=%s AND usato=FALSE AND scadenza>NOW()", (token,))
        row_ = cur.fetchone()
        if not row_ or row_['codice'] != codice:
            cur.close()
            return err('Token o codice non valido', 400)
        cur.execute("UPDATE utente SET password=%s WHERE id_utente=%s", (hash_pw(pw), row_['id_utente']))
        cur.execute("UPDATE reset_password SET usato=TRUE WHERE token=%s", (token,))
        conn.commit()
        cur.close()
        return ok(message='Password aggiornata!')
    except Exception as e:
        if conn: conn.rollback()
        print(f'[RESET UPDATE ERROR] {e}')
        return err('Errore aggiornamento password')
    finally:
        if conn:
            release_db(conn)

# ─────────────────────────────────────────────────────────────────────────────
# API: DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/api/dashboard')
@login_required
def api_dashboard():
    uid = session['user_id']
    conn = None
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT COUNT(*) AS n FROM prenotazione WHERE id_utente=%s AND stato='Confermata'", (uid,))
        freq = cur.fetchone()['n'] or 0
        cur.execute("""SELECT COALESCE(ROUND(AVG(f.voto::numeric),1),0) AS m FROM feedback f
                       JOIN lezione l ON f.id_lezione=l.id_lezione WHERE l.id_insegnante=%s""", (uid,))
        media = float(cur.fetchone()['m'] or 0)
        cur.execute("SELECT COUNT(*) AS n FROM lezione WHERE id_insegnante=%s", (uid,))
        ins_n = cur.fetchone()['n'] or 0
        
        cur.execute("""SELECT l.id_lezione,l.titolo,l.descrizione,l.data_lezione::text,
                              l.orario::text,l.durata,l.modalita,l.luogo,l.numero_massimo_partecipanti,
                              u.nome||' '||u.cognome AS nome_insegnante, c.nome_competenza AS categoria
                       FROM lezione l JOIN utente u ON l.id_insegnante=u.id_utente
                       LEFT JOIN competenza c ON l.id_competenza=c.id_competenza
                       WHERE l.id_insegnante!=%s AND l.data_lezione>=CURRENT_DATE
                         AND l.id_lezione NOT IN (
                             SELECT id_lezione FROM prenotazione WHERE id_utente=%s AND stato!='Annullata')
                       ORDER BY l.data_lezione ASC LIMIT 3""", (uid, uid))
        cons = [dict(r) for r in (cur.fetchall() or [])]
        
        cur.execute("""SELECT c.nome_competenza,uc.livello,uc.tipo FROM utente_competenza uc
                       JOIN competenza c ON uc.id_competenza=c.id_competenza
                       WHERE uc.id_utente=%s ORDER BY c.nome_competenza""", (uid,))
        comps = [dict(r) for r in (cur.fetchall() or [])]
        
        cur.execute("SELECT id_competenza,nome_competenza FROM competenza ORDER BY nome_competenza")
        cl = [dict(r) for r in (cur.fetchall() or [])]
        cur.close()
        return ok(stats={'lezioni_frequentate': freq, 'punti': ins_n*50 + freq*10, 'media_feedback': media},
                  lezioni_consigliate=cons, competenze=comps, competenze_list=cl)
    except Exception as e:
        print(f'[DASHBOARD ERROR] {e}')
        return err('Errore caricamento dashboard')
    finally:
        if conn:
            release_db(conn)

# ─────────────────────────────────────────────────────────────────────────────
# API: LEZIONI
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/api/lezioni')
def api_lezioni():
    cat = request.args.get('categoria', '').strip()
    q = request.args.get('q', '').strip()
    conn = None
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        sql = """SELECT l.id_lezione,l.titolo,l.descrizione,l.data_lezione::text,l.orario::text,
                      l.durata,l.modalita,l.luogo,l.numero_massimo_partecipanti,l.id_insegnante,
                      u.nome||' '||u.cognome AS nome_insegnante,
                      c.nome_competenza AS categoria,c.id_competenza
               FROM lezione l JOIN utente u ON l.id_insegnante=u.id_utente
               LEFT JOIN competenza c ON l.id_competenza=c.id_competenza
               WHERE l.data_lezione>=CURRENT_DATE"""
        p = []
        if cat: sql += " AND c.nome_competenza=%s"; p.append(cat)
        if q:   sql += " AND (l.titolo ILIKE %s OR l.descrizione ILIKE %s OR c.nome_competenza ILIKE %s)"; p += [f'%{q}%'] * 3
        sql += " ORDER BY c.nome_competenza ASC, l.data_lezione ASC LIMIT 100"
        cur.execute(sql, p)
        r = [dict(x) for x in (cur.fetchall() or [])]
        cur.close()
        return ok(lezioni=r)
    except Exception as e:
        print(f'[LEZIONI LIST ERROR] {e}')
        return err('Errore caricamento lezioni')
    finally:
        if conn:
            release_db(conn)

@app.route('/api/lezioni/crea', methods=['POST'])
@login_required
def api_crea_lezione():
    d = request.get_json() or {}
    uid = session['user_id']
    if not d.get('titolo') or not d.get('data_lezione') or not d.get('orario'):
        return err('Titolo, data e orario obbligatori')
    if not d.get('id_competenza'): return err('Seleziona una competenza')
    conn = None
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""INSERT INTO lezione (titolo,descrizione,id_competenza,id_insegnante,
                       data_lezione,orario,modalita,luogo,numero_massimo_partecipanti,durata)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id_lezione""",
            (d['titolo'], d.get('descrizione', ''), d['id_competenza'], uid,
             d['data_lezione'], d['orario'], d.get('modalita', 'Online'),
             d.get('luogo', ''), int(d.get('numero_massimo_partecipanti') or 10),
             int(d.get('durata') or 60)))
        new_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        return ok(message='Lezione creata!', id_lezione=new_id)
    except Exception as e:
        if conn: conn.rollback()
        print(f'[CREATE LESSON ERROR] {e}')
        return err('Errore creazione lezione')
    finally:
        if conn:
            release_db(conn)

@app.route('/api/lezioni/<int:id>')
def api_lezione_detail(id):
    uid = session.get('user_id')
    conn = None
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""SELECT l.*,l.data_lezione::text,l.orario::text,
                              u.nome||' '||u.cognome AS nome_insegnante, u.id_utente AS id_ins,
                              c.nome_competenza AS categoria
                       FROM lezione l JOIN utente u ON l.id_insegnante=u.id_utente
                       LEFT JOIN competenza c ON l.id_competenza=c.id_competenza
                       WHERE l.id_lezione=%s""", (id,))
        l = cur.fetchone()
        if not l:
            cur.close()
            return err('Lezione non trovata', 404)
        l = dict(l)
        cur.execute("""SELECT u.id_utente,u.nome,u.cognome FROM prenotazione p
                       JOIN utente u ON p.id_utente=u.id_utente
                       WHERE p.id_lezione=%s AND p.stato='Confermata'""", (id,))
        part = [dict(r) for r in (cur.fetchall() or [])]
        
        cur.execute("SELECT id_materiale, id_lezione, tipo, titolo AS nome_materiale, url_risorsa, data_caricamento::text FROM materiale WHERE id_lezione=%s", (id,))
        mat = [dict(r) for r in (cur.fetchall() or [])]
        
        cur.execute("""SELECT f.voto,f.commento,f.data_feedback::text,u.nome,u.cognome
                       FROM feedback f JOIN utente u ON f.id_utente=u.id_utente
                       WHERE f.id_lezione=%s ORDER BY f.data_feedback DESC""", (id,))
        fb = [dict(r) for r in (cur.fetchall() or [])]
        cur.close()
        l['id_insegnante'] = l['id_ins']
        posti = max(0, (l['numero_massimo_partecipanti'] or 99) - len(part))
        return ok(lezione=l, partecipanti=part, materiali=mat, feedback=fb,
                  posti_disponibili=posti,
                  is_teacher=(uid == l['id_ins']),
                  is_booked=bool(uid and any(p['id_utente'] == uid for p in part)))
    except Exception as e:
        print(f'[LESSON DETAIL ERROR] {e}')
        return err('Errore caricamento dettagli lezione')
    finally:
        if conn:
            release_db(conn)

@app.route('/api/lezioni/<int:id>/prenota', methods=['POST'])
@login_required
def api_prenota(id):
    uid = session['user_id']
    conn = None
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT id_prenotazione FROM prenotazione WHERE id_lezione=%s AND id_utente=%s AND stato!='Annullata'", (id, uid))
        if cur.fetchone():
            cur.close()
            return err('Già prenotato')
        cur.execute("SELECT numero_massimo_partecipanti FROM lezione WHERE id_lezione=%s", (id,))
        lez = cur.fetchone()
        if not lez:
            cur.close()
            return err('Lezione non trovata', 404)
        cur.execute("SELECT COUNT(*) AS n FROM prenotazione WHERE id_lezione=%s AND stato='Confermata'", (id,))
        if cur.fetchone()['n'] >= (lez['numero_massimo_partecipanti'] or 99):
            cur.close()
            return err('Posti esauriti')
        cur.execute("INSERT INTO prenotazione (data_prenotazione,stato,id_utente,id_lezione) VALUES (%s,'Confermata',%s,%s)",
                    (date.today(), uid, id))
        conn.commit()
        cur.close()
        return ok(message='Prenotazione confermata!')
    except Exception as e:
        if conn: conn.rollback()
        print(f'[BOOK ERROR] {e}')
        return err('Errore prenotazione')
    finally:
        if conn:
            release_db(conn)

@app.route('/api/lezioni/<int:id>/annulla', methods=['POST'])
@login_required
def api_annulla(id):
    uid = session['user_id']
    conn = None
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE prenotazione SET stato='Annullata' WHERE id_lezione=%s AND id_utente=%s", (id, uid))
        conn.commit()
        cur.close()
        return ok(message='Prenotazione annullata.')
    except Exception as e:
        if conn: conn.rollback()
        print(f'[CANCEL BOOKING ERROR] {e}')
        return err('Errore annullamento prenotazione')
    finally:
        if conn:
            release_db(conn)

# ─────────────────────────────────────────────────────────────────────────────
# API: MIE LEZIONI
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/api/mie-lezioni')
@login_required
def api_mie_lezioni():
    uid = session['user_id']
    today = str(date.today())
    conn = None
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""SELECT l.id_lezione,l.titolo,l.data_lezione::text,l.orario::text,
                              l.modalita,l.luogo,l.numero_massimo_partecipanti,
                              u.nome||' '||u.cognome AS nome_insegnante, c.nome_competenza AS categoria
                       FROM prenotazione p JOIN lezione l ON p.id_lezione=l.id_lezione
                       JOIN utente u ON l.id_insegnante=u.id_utente
                       LEFT JOIN competenza c ON l.id_competenza=c.id_competenza
                       WHERE p.id_utente=%s AND p.stato='Confermata' ORDER BY l.data_lezione DESC""", (uid,))
        freq = [dict(r) for r in (cur.fetchall() or [])]
        cur.execute("""SELECT l.id_lezione,l.titolo,l.data_lezione::text,l.orario::text,
                              l.modalita,l.luogo,l.numero_massimo_partecipanti,
                              c.nome_competenza AS categoria
                       FROM lezione l LEFT JOIN competenza c ON l.id_competenza=c.id_competenza
                       WHERE l.id_insegnante=%s ORDER BY l.data_lezione DESC""", (uid,))
        ins = [dict(r) for r in (cur.fetchall() or [])]
        for l in ins:
            cur.execute("""SELECT u.nome,u.cognome,u.username FROM prenotazione p
                           JOIN utente u ON p.id_utente=u.id_utente
                           WHERE p.id_lezione=%s AND p.stato='Confermata'""", (l['id_lezione'],))
            l['partecipanti'] = [dict(r) for r in (cur.fetchall() or [])]
        cur.close()
        for r in freq + ins: r['passata'] = r['data_lezione'] < today
        return ok(frequentando=freq, insegnando=ins)
    except Exception as e:
        print(f'[MIE LEZIONI ERROR] {e}')
        return err('Errore caricamento mie lezioni')
    finally:
        if conn:
            release_db(conn)

# ─────────────────────────────────────────────────────────────────────────────
# API: COMPETENZE
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/api/competenze')
def api_competenze():
    q = request.args.get('q', '').strip()
    conn = None
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        if q:
            cur.execute("SELECT * FROM competenza WHERE nome_competenza ILIKE %s OR categoria ILIKE %s ORDER BY nome_competenza",
                        (f'%{q}%', f'%{q}%'))
        else:
            cur.execute("SELECT * FROM competenza ORDER BY nome_competenza")
        comps = [dict(r) for r in (cur.fetchall() or [])]
        cats = sorted({c['categoria'] for c in comps if c.get('categoria')})
        cur.close()
        return ok(competenze=comps, categorie=cats)
    except Exception as e:
        print(f'[COMPETENZE LIST ERROR] {e}')
        return err('Errore caricamento competenze')
    finally:
        if conn:
            release_db(conn)

@app.route('/api/competenze/aggiungi', methods=['POST'])
@login_required
def api_aggiungi_comp():
    d = request.get_json() or {}
    uid = session['user_id']
    if not d.get('id_competenza'): return err('Seleziona una competenza')
    conn = None
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO utente_competenza (id_utente,id_competenza,livello,tipo) VALUES (%s,%s,%s,%s)",
                    (uid, d['id_competenza'], d.get('livello', 'Intermedio'), d.get('tipo', 'Offerta')))
        conn.commit()
        cur.close()
    except psycopg2.errors.UniqueViolation:
        if conn: conn.rollback()
    except Exception as e:
        if conn: conn.rollback()
        print(f'[ADD COMP ERROR] {e}')
        return err('Errore aggiunta competenza')
    finally:
        if conn:
            release_db(conn)
    return ok(message='Competenza aggiunta!')

# ─────────────────────────────────────────────────────────────────────────────
# API: PROFILO
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/api/profilo')
@login_required
def api_profilo():
    uid = session['user_id']
    conn = None
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT id_utente,nome,cognome,email,descrizione_profilo,data_registrazione::text,username,codice_univoco FROM utente WHERE id_utente=%s", (uid,))
        user = dict(cur.fetchone() or {})
        if not user:
            cur.close()
            return err('Utente non trovato', 404)
        cur.execute("SELECT COUNT(*) AS n FROM lezione WHERE id_insegnante=%s", (uid,))
        ld = cur.fetchone()['n'] or 0
        cur.execute("SELECT COUNT(*) AS n FROM utente_competenza WHERE id_utente=%s", (uid,))
        nc = cur.fetchone()['n'] or 0
        cur.execute("""SELECT COALESCE(ROUND(AVG(f.voto::numeric),1),0) AS m FROM feedback f
                       JOIN lezione l ON f.id_lezione=l.id_lezione WHERE l.id_insegnante=%s""", (uid,))
        media = float(cur.fetchone()['m'] or 0)
        cur.execute("""SELECT l.id_lezione,l.titolo,l.data_lezione::text,l.orario::text,l.modalita,c.nome_competenza AS categoria
                       FROM lezione l LEFT JOIN competenza c ON l.id_competenza=c.id_competenza
                       WHERE l.id_insegnante=%s ORDER BY l.data_lezione DESC""", (uid,))
        lc = [dict(r) for r in (cur.fetchall() or [])]
        cur.execute("""SELECT c.nome_competenza,uc.livello,uc.tipo FROM utente_competenza uc
                       JOIN competenza c ON uc.id_competenza=c.id_competenza WHERE uc.id_utente=%s ORDER BY c.nome_competenza""", (uid,))
        comps = [dict(r) for r in (cur.fetchall() or [])]
        cur.execute("""SELECT f.voto,f.commento,f.data_feedback::text,u.nome,u.cognome FROM feedback f
                       JOIN lezione l ON f.id_lezione=l.id_lezione JOIN utente u ON f.id_utente=u.id_utente
                       WHERE l.id_insegnante=%s ORDER BY f.data_feedback DESC""", (uid,))
        fb = [dict(r) for r in (cur.fetchall() or [])]
        cur.execute("SELECT id_competenza,nome_competenza FROM competenza ORDER BY nome_competenza")
        cl = [dict(r) for r in (cur.fetchall() or [])]
        cur.close()
        return ok(user=user, stats={'lezioni_date': ld, 'competenze': nc, 'media_feedback': media},
                  lezioni_create=lc, competenze=comps, feedback=fb, competenze_list=cl)
    except Exception as e:
        print(f'[PROFILO ERROR] {e}')
        return err('Errore caricamento profilo')
    finally:
        if conn:
            release_db(conn)

@app.route('/api/profilo/aggiorna', methods=['POST'])
@login_required
def api_aggiorna_profilo():
    d = request.get_json() or {}
    uid = session['user_id']
    nome = (d.get('nome') or '').strip()
    cognome = (d.get('cognome') or '').strip()
    bio = censura((d.get('descrizione_profilo') or '').strip())
    username = (d.get('username') or '').strip().lower()
    if username and not is_valid_username(username): return err('Username non valido')
    conn = None
    try:
        conn = get_db()
        cur = conn.cursor()
        if username:
            cur.execute("UPDATE utente SET nome=%s,cognome=%s,descrizione_profilo=%s,username=%s WHERE id_utente=%s",
                        (nome, cognome, bio, username, uid))
        else:
            cur.execute("UPDATE utente SET nome=%s,cognome=%s,descrizione_profilo=%s WHERE id_utente=%s",
                        (nome, cognome, bio, uid))
        conn.commit()
        cur.close()
    except psycopg2.errors.UniqueViolation:
        if conn: conn.rollback()
        return err('Username già in uso')
    except Exception as e:
        if conn: conn.rollback()
        print(f'[PROFILO UPDATE ERROR] {e}')
        return err('Errore aggiornamento profilo')
    finally:
        if conn:
            release_db(conn)
    session['user_name'] = nome
    session['user_cognome'] = cognome
    if username: session['user_username'] = username
    return ok(message='Profilo aggiornato!')

# ─────────────────────────────────────────────────────────────────────────────
# API: MESSAGGI
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/api/utenti/cerca')
@login_required
def api_cerca_utente():
    q = (request.args.get('q') or '').strip()
    uid = session['user_id']
    if not q: return err('Inserisci codice o username')
    conn = None
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""SELECT id_utente,nome,cognome,username,codice_univoco,descrizione_profilo
                       FROM utente WHERE id_utente!=%s
                       AND (UPPER(codice_univoco)=%s OR LOWER(username)=%s) LIMIT 1""",
                    (uid, q.upper(), q.lower().lstrip('@')))
        u = cur.fetchone()
        cur.close()
        if not u: return err('Nessun utente trovato', 404)
        return ok(utente={'id': u['id_utente'], 'nome': u['nome'], 'cognome': u['cognome'],
                          'username': u.get('username', ''), 'descrizione': u.get('descrizione_profilo', '')})
    except Exception as e:
        print(f'[UTENTI SEARCH ERROR] {e}')
        return err('Errore ricerca utente')
    finally:
        if conn:
            release_db(conn)

@app.route('/api/messaggi/conversazioni')
@login_required
def api_conversazioni():
    uid = session['user_id']
    q = (request.args.get('q') or '').strip()
    conn = None
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        sql = """SELECT u.id_utente,u.nome,u.cognome,u.username,
                      (SELECT m.contenuto FROM messaggio m
                       WHERE (m.id_mittente=u.id_utente AND m.id_destinatario=%s)
                          OR (m.id_mittente=%s AND m.id_destinatario=u.id_utente)
                       ORDER BY m.data_invio DESC LIMIT 1) AS ultimo_msg,
                      (SELECT m.id_mittente FROM messaggio m
                       WHERE (m.id_mittente=u.id_utente AND m.id_destinatario=%s)
                          OR (m.id_mittente=%s AND m.id_destinatario=u.id_utente)
                       ORDER BY m.data_invio DESC LIMIT 1) AS ultimo_mittente_id,
                      (SELECT TO_CHAR(m.data_invio,'HH24:MI') FROM messaggio m
                       WHERE (m.id_mittente=u.id_utente AND m.id_destinatario=%s)
                          OR (m.id_mittente=%s AND m.id_destinatario=u.id_utente)
                       ORDER BY m.data_invio DESC LIMIT 1) AS ora
               FROM utente u WHERE u.id_utente!=%s
               AND u.id_utente IN (
                   SELECT id_mittente FROM messaggio WHERE id_destinatario=%s
                   UNION SELECT id_destinatario FROM messaggio WHERE id_mittente=%s)"""
        p = [uid, uid, uid, uid, uid, uid, uid, uid, uid]
        if q: sql += " AND (u.nome ILIKE %s OR u.cognome ILIKE %s OR u.username ILIKE %s)"; p += [f'%{q}%'] * 3
        sql += " ORDER BY ora DESC NULLS LAST"
        cur.execute(sql, p)
        r = [dict(x) for x in (cur.fetchall() or [])]
        cur.close()
        return ok(conversazioni=r)
    except Exception as e:
        print(f'[CONVERSATIONS ERROR] {e}')
        return err('Errore conversazioni')
    finally:
        if conn:
            release_db(conn)

@app.route('/api/messaggi/chat/<int:other_id>')
@login_required
def api_chat(other_id):
    uid = session['user_id']
    conn = None
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""SELECT id_messaggio,id_mittente,contenuto,
                              TO_CHAR(data_invio,'HH24:MI') AS ora
                       FROM messaggio
                       WHERE (id_mittente=%s AND id_destinatario=%s)
                          OR (id_mittente=%s AND id_destinatario=%s)
                       ORDER BY data_invio ASC LIMIT 100""", (uid, other_id, other_id, uid))
        msgs = [dict(r) for r in (cur.fetchall() or [])]
        for m in msgs: m['out'] = (m['id_mittente'] == uid)
        cur.execute("SELECT id_utente,nome,cognome,username FROM utente WHERE id_utente=%s", (other_id,))
        other = cur.fetchone()
        cur.close()
        if not other: return err('Utente non trovato', 404)
        last_id = msgs[-1]['id_messaggio'] if msgs else 0
        return ok(messaggi=msgs, interlocutore=dict(other), last_id=last_id, my_user_id=uid)
    except Exception as e:
        print(f'[CHAT LOAD ERROR] {e}')
        return err('Errore storico chat')
    finally:
        if conn:
            release_db(conn)

# ─────────────────────────────────────────────────────────────────────────────
# WEBSOCKET CHAT LOGIC (Gevent)
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

    conn = None
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT id_utente,nome,cognome FROM utente WHERE id_utente=%s", (dest_id,))
        dest_user = cur.fetchone()
        if not dest_user:
            cur.close()
            return

        cur.execute(
            "INSERT INTO messaggio (id_mittente,id_destinatario,contenuto) VALUES (%s,%s,%s) "
            "RETURNING id_messaggio, TO_CHAR(data_invio,'HH24:MI') AS ora",
            (uid, dest_id, contenuto)
        )
        row_ = cur.fetchone()
        conn.commit()
        cur.close()

        msg_payload = {
            'id_messaggio': row_['id_messaggio'],
            'id_mittente': uid,
            'contenuto': contenuto,
            'ora': row_['ora'],
        }

        emit('nuovo_messaggio', {**msg_payload, 'out': True}, room=f'user_{uid}')
        emit('nuovo_messaggio', {**msg_payload, 'out': False}, room=f'user_{dest_id}')
    except Exception as e:
        if conn: conn.rollback()
        print(f'[WS PRIVMSG ERROR] {e}')
    finally:
        if conn:
            release_db(conn)

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)