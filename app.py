# CHIAVE DI RISOLUZIONE WEBSOCKET SU RENDER:
from gevent import monkey
monkey.patch_all()

"""
SkillBridge - app.py (Versione Presentazione Finale Certificata)
"""

import os
import re
import secrets
import hashlib
import random
from datetime import date, datetime, timedelta
from functools import wraps
from contextlib import contextmanager

from flask import Flask, send_from_directory, request, redirect, session, jsonify, make_response
from flask_socketio import SocketIO, emit, join_room, leave_room
import psycopg2
import psycopg2.extras
import smtplib as smtp
from email.mime.text import MIMEText
from email.header import Header

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = "chiave_segreta_skillbridge_2024"

socketio = SocketIO(app,
    cors_allowed_origins='*',
    async_mode='gevent',
    logger=False,
    engineio_logger=False
)

DB_URL = os.environ.get(
    'DB_URL',
    'postgresql://postgres:PASSWORD@HOST:6543/postgres'
)

# Vecchie Credenziali Configurate e Testate
MAIL_MITTENTE = "skillbridge.einaudi@gmail.com"
MAIL_PASSWORD  = "jwlu iret icve xuea"

PAROLACCE = [
    'cazzo','minchia','vaffanculo','stronzo','stronza','merda','coglione',
    'bastardo','bastarda','puttana','fanculo','frocio','troia','cagna',
    'negro','negra','cornuto','fuck','shit','bitch','asshole','bastard',
    'inappropriato','porno','allusioni_volgari','puttane'
]

@contextmanager
def db_conn():
    conn = psycopg2.connect(DB_URL)
    try:
        yield conn
    finally:
        conn.close()

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def is_valid_email(e):
    return re.search(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}$', e)

def is_valid_username(u):
    return re.match(r'^[a-zA-Z0-9_.]{3,30}$', u)

def contiene_inappropriato(testo):
    if not testo: return False
    testo_lower = testo.lower()
    for p in PAROLACCE:
        if p in testo_lower:
            return True
    return False

def censura(t):
    if not t: return t
    for p in PAROLACCE:
        t = re.sub(re.escape(p), p[0]+'*'*(len(p)-2)+p[-1], t, flags=re.IGNORECASE)
    return t

def genera_codice():
    h = secrets.token_hex(4).upper()
    return f"SB-{h[:4]}-{h[4:]}"

# CHIAVE DI RISOLUZIONE: SMTP Welcome Email con codifica UTF-8 sicura contro i crash
def send_welcome_email_smtp(dest, nome):
    try:
        msg = MIMEText(
            f"Ciao {nome},\n\n"
            f"Benvenuto in SkillBridge! Il tuo account e' stato creato con successo.\n"
            f"Puoi ora accedere, cercare lezioni, insegnare le tue competenze e molto altro.\n\n"
            f"Buon apprendimento!\n"
            f"Il team di SkillBridge",
            'plain', 'utf-8'
        )
        msg['Subject'] = Header("Benvenuto in SkillBridge!", 'utf-8')
        msg['From'] = MAIL_MITTENTE
        msg['To'] = dest

        server = smtp.SMTP("smtp.gmail.com", 587, timeout=10)
        server.starttls()
        server.login(MAIL_MITTENTE, MAIL_PASSWORD)
        server.sendmail(MAIL_MITTENTE, [dest], msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"[SMTP Welcome Errore] {e}")
        return False

def send_otp_email_smtp(dest, codice):
    try:
        msg = MIMEText(
            f"Il tuo codice di verifica OTP per reimpostare la password e': {codice}\n"
            f"Il codice e' valido per 15 minuti.\n\n"
            f"Se non hai richiesto tu il reset, ignora questa comunicazione.",
            'plain', 'utf-8'
        )
        msg['Subject'] = Header("SkillBridge - Codice di Reset Password", 'utf-8')
        msg['From'] = MAIL_MITTENTE
        msg['To'] = dest

        server = smtp.SMTP("smtp.gmail.com", 587, timeout=10)
        server.starttls()
        server.login(MAIL_MITTENTE, MAIL_PASSWORD)
        server.sendmail(MAIL_MITTENTE, [dest], msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"[SMTP OTP Errore] {e}")
        return False

# Decoratori Sicurezza
def login_required(f):
    @wraps(f)
    def d(*a, **kw):
        if 'user_id' not in session:
            return jsonify({'ok': False, 'error': 'Non autenticato'}), 401
        return f(*a, **kw)
    return d

def admin_required(f):
    @wraps(f)
    def d(*a, **kw):
        if 'user_id' not in session or session.get('user_username') != 'adminsskill':
            return jsonify({'ok': False, 'error': 'Accesso negato'}), 403
        return f(*a, **kw)
    return d

def page_guard(f):
    @wraps(f)
    def d(*a, **kw):
        if 'user_id' not in session:
            return redirect('/login')
        if session.get('user_username') == 'adminsskill':
            return redirect('/admin')
        return f(*a, **kw)
    return d

def ok(**kw):    return jsonify({'ok': True,  **kw})
def err(m, c=400): return jsonify({'ok': False, 'error': m}), c

# ─────────────────────────────────────────────────────────────────────────────
# SERVING FILE DI SFONDO SPLASH SCREEN DALLA ROOT
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/bg_splash.jpg')
@app.route('/static/bg_splash.jpg')
def serve_bg_splash():
    if os.path.exists('static/bg_splash.jpg'):
        return send_from_directory('static', 'bg_splash.jpg')
    return send_from_directory('.', 'bg_splash.jpg')

# ─────────────────────────────────────────────────────────────────────────────
# ROTTE WEB & PWA
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/manifest.json')
def manifest(): return send_from_directory('static', 'manifest.json')

@app.route('/sw.js')
def service_worker():
    resp = send_from_directory('static', 'sw.js')
    resp.headers['Service-Worker-Allowed'] = '/'
    resp.headers['Cache-Control'] = 'no-cache'
    return resp

@app.route('/favicon.ico')
def favicon(): return send_from_directory('static', 'favicon.ico')

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect('/admin' if session.get('user_username') == 'adminsskill' else '/dashboard')
    return redirect('/login')

@app.route('/login')
def login_page(): return send_from_directory('templates','skillbridge-login.html')

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

@app.route('/admin')
def admin_page():
    if 'user_id' not in session or session.get('user_username') != 'adminsskill':
        return redirect('/login')
    return send_from_directory('templates','skillbridge-admin.html')

# ─────────────────────────────────────────────────────────────────────────────
# API: AUTHENTICATION
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/api/login', methods=['POST'])
def api_login():
    d = request.get_json() or {}
    lid = (d.get('email') or '').strip().lower()
    pw  = d.get('password','')
    if not lid or not pw: return err('Email/username e password obbligatori')
    
    # ACCESSO ADMIN FAIL-SAFE
    if lid == 'adminsskill' and pw == 'AdminBridge4!':
        session.update({
            'user_id': 0,
            'user_name': 'Admin',
            'user_cognome': 'SkillBridge',
            'user_username': 'adminsskill'
        })
        return ok(user={
            'id': 0,
            'nome': 'Admin',
            'cognome': 'SkillBridge',
            'username': 'adminsskill'
        })

    with db_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM utente WHERE (LOWER(email)=%s OR LOWER(username)=%s) AND password=%s",
                (lid, lid, hash_pw(pw))
            )
            user = cur.fetchone()
            if not user: return err('Credenziali errate', 401)
            
            session.update({
                'user_id': user['id_utente'],
                'user_name': user['nome'],
                'user_cognome': user['cognome'],
                'user_username': user.get('username','')
            })
            return ok(user={
                'id': user['id_utente'],
                'nome': user['nome'],
                'cognome': user['cognome'],
                'username': user.get('username','')
            })

@app.route('/api/register', methods=['POST'])
def api_register():
    d = request.get_json() or {}
    nome    = (d.get('nome')    or '').strip()
    cognome = (d.get('cognome') or '').strip()
    email   = (d.get('email')   or '').strip().lower()
    pw      = d.get('password','')
    bio     = (d.get('bio') or '').strip()
    username= (d.get('username') or '').strip().lower()

    if contiene_inappropriato(nome) or contiene_inappropriato(cognome) or contiene_inappropriato(bio) or contiene_inappropriato(username):
        return err('Il testo inserito contiene parole non consentite!')

    if not nome or not cognome: return err('Nome e cognome obbligatori')
    if not is_valid_email(email): return err('Email non valida')
    if len(pw) < 6: return err('Password minimo 6 caratteri')
    
    with db_conn() as conn:
        with conn.cursor() as cur:
            if username:
                if not is_valid_username(username):
                    return err('Username non valido (3-30 caratteri)')
                cur.execute("SELECT id_utente FROM utente WHERE username=%s", (username,))
                if cur.fetchone(): return err('Username già in uso')
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
                "INSERT INTO utente (nome,cognome,email,password,descrizione_profilo,username,codice_univoco,data_registrazione) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                (nome, cognome, email, hash_pw(pw), censura(bio), username, codice, date.today())
            )
            conn.commit()
            
            # Invio con SMTP originale
            send_welcome_email_smtp(email, nome)
            return ok(message=f'Registrazione completata!')

# ROTTA DI LOGOUT SICURA CON DISTRUZIONE CACHE
@app.route('/logout', methods=['GET', 'POST'])
@app.route('/api/logout', methods=['GET', 'POST'])
def api_logout():
    session.clear()
    resp = make_response(redirect('/login'))
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp

@app.route('/api/me')
def api_me():
    if 'user_id' not in session: return err('Non autenticato', 401)
    return ok(user={'id': session['user_id'], 'nome': session['user_name'],
                    'cognome': session.get('user_cognome',''), 'username': session.get('user_username','')})

# ─────────────────────────────────────────────────────────────────────────────
# API: RESET PASSWORD (OTP MOCKATO)
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/api/reset-password/richiedi', methods=['POST'])
def api_reset_richiedi():
    email = (request.get_json() or {}).get('email', '').strip().lower()
    if not email: return err('Email obbligatoria')
    
    with db_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT id_utente,nome FROM utente WHERE LOWER(email)=%s", (email,))
            user = cur.fetchone()
            if not user:
                return err("L'email inserita non è associata ad alcun utente.")
            
            cur.execute("UPDATE reset_password SET usato=TRUE WHERE id_utente=%s AND usato=FALSE", (user['id_utente'],))
            token = secrets.token_urlsafe(32)
            
            # Generatore a 6 cifre casuale robusto
            codice = str(random.randint(100000, 999999))
            
            scad = datetime.now() + timedelta(minutes=15)
            cur.execute("INSERT INTO reset_password (id_utente,token,codice,scadenza) VALUES (%s,%s,%s,%s)",
                        (user['id_utente'], token, codice, scad))
            conn.commit()
            
            # Spedisce con SMTP originale
            send_otp_email_smtp(email, codice)
            return ok(token=token, mock_otp=codice, message='Codice generato con successo per la demo!')

@app.route('/api/reset-password/verifica', methods=['POST'])
def api_reset_verifica():
    d = request.get_json() or {}
    token = (d.get('token') or '').strip()
    codice = (d.get('codice') or '').strip()
    if not token or not codice: return err('Dati mancanti')
    
    with db_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM reset_password WHERE token=%s AND usato=FALSE AND scadenza>NOW()", (token,))
            row_ = cur.fetchone()
            if not row_: return err('Token scaduto o non valido')
            if row_['codice'] != codice: return err('Codice errato')
            return ok(message='Codice corretto.')

@app.route('/api/reset-password/nuova', methods=['POST'])
def api_reset_nuova():
    d = request.get_json() or {}
    token = (d.get('token') or '').strip()
    codice = (d.get('codice') or '').strip()
    pw = d.get('password', '')
    if not token or not codice or not pw: return err('Dati mancanti')
    if len(pw) < 6: return err('Password minimo 6 caratteri')
    
    with db_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM reset_password WHERE token=%s AND usato=FALSE AND scadenza>NOW()", (token,))
            row_ = cur.fetchone()
            if not row_ or row_['codice'] != codice: return err('Token o codice non valido')
            cur.execute("UPDATE utente SET password=%s WHERE id_utente=%s", (hash_pw(pw), row_['id_utente']))
            cur.execute("UPDATE reset_password SET usato=TRUE WHERE token=%s", (token,))
            conn.commit()
            return ok(message='Password aggiornata!')

# ─────────────────────────────────────────────────────────────────────────────
# API: DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/api/dashboard')
@login_required
def api_dashboard():
    uid = session['user_id']
    with db_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
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
            return ok(stats={'lezioni_frequentate': freq, 'punti': ins_n*50 + freq*10, 'media_feedback': media},
                      lezioni_consigliate=cons, competenze=comps, competenze_list=cl)

# ─────────────────────────────────────────────────────────────────────────────
# API: LEZIONI
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/api/lezioni')
def api_lezioni():
    cat = request.args.get('categoria', '').strip()
    q = request.args.get('q', '').strip()
    with db_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
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
            return ok(lezioni=r)

@app.route('/api/lezioni/crea', methods=['POST'])
@login_required
def api_crea_lezione():
    d = request.get_json() or {}
    uid = session['user_id']
    titolo = d.get('titolo', '').strip()
    descrizione = d.get('descrizione', '').strip()
    luogo = d.get('luogo', '').strip()
    
    if contiene_inappropriato(titolo) or contiene_inappropriato(descrizione) or contiene_inappropriato(luogo):
        return err('Il testo inserito contiene termini non consentiti.')

    if not titolo or not d.get('data_lezione') or not d.get('orario'):
        return err('Titolo, data e orario obbligatori')
    
    try:
        data_lez = datetime.strptime(d['data_lezione'], '%Y-%m-%d').date()
        oggi = date.today()
        domani = oggi + timedelta(days=1)
        limite_anno = oggi + timedelta(days=365)
        if data_lez < domani:
            return err('La data della lezione deve essere almeno a partire da domani!')
        if data_lez > limite_anno:
            return err('Non puoi programmare lezioni oltre un anno da oggi!')
    except ValueError:
        return err('Formato data non valido')

    if not d.get('id_competenza'): return err('Seleziona una competenza')
    
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""INSERT INTO lezione (titolo,descrizione,id_competenza,id_insegnante,
                           data_lezione,orario,modalita,luogo,numero_massimo_partecipanti,durata)
                           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id_lezione""",
                (titolo, censura(descrizione), d['id_competenza'], uid,
                 d['data_lezione'], d['orario'], d.get('modalita','Online'),
                 censura(luogo), int(d.get('numero_massimo_partecipanti') or 10),
                 int(d.get('durata') or 60)))
            new_id = cur.fetchone()[0]
            conn.commit()
            return ok(message='Lezione creata!', id_lezione=new_id)

@app.route('/api/lezioni/<int:id>')
def api_lezione_detail(id):
    uid = session.get('user_id')
    with db_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""SELECT l.*,l.data_lezione::text,l.orario::text,
                                  u.nome||' '||u.cognome AS nome_insegnante, u.id_utente AS id_ins, u.codice_univoco AS codice_docente,
                                  c.nome_competenza AS categoria
                           FROM lezione l JOIN utente u ON l.id_insegnante=u.id_utente
                           LEFT JOIN competenza c ON l.id_competenza=c.id_competenza
                           WHERE l.id_lezione=%s""", (id,))
            l = cur.fetchone()
            if not l: return err('Lezione non trovata', 404)
            l = dict(l)
            
            cur.execute("""SELECT u.id_utente, u.username FROM prenotazione p
                           JOIN utente u ON p.id_utente=u.id_utente
                           WHERE p.id_lezione=%s AND p.stato='Confermata'""", (id,))
            part = [dict(r) for r in (cur.fetchall() or [])]
            
            cur.execute("SELECT id_materiale, id_lezione, tipo, titolo AS nome_materiale, url_risorsa, data_caricamento::text FROM materiale WHERE id_lezione=%s", (id,))
            mat = [dict(r) for r in (cur.fetchall() or [])]
            
            cur.execute("""SELECT f.voto,f.commento,f.data_feedback::text,u.nome,u.cognome
                           FROM feedback f JOIN utente u ON f.id_utente=u.id_utente
                           WHERE f.id_lezione=%s ORDER BY f.data_feedback DESC""", (id,))
            fb = [dict(r) for r in (cur.fetchall() or [])]
            
            posti = max(0, (l['numero_massimo_partecipanti'] or 99) - len(part))
            return ok(lezione=l, partecipanti=part, materiali=mat, feedback=fb,
                      posti_disponibili=posti,
                      is_teacher=(uid == l['id_ins']),
                      is_booked=bool(uid and any(p['id_utente'] == uid for p in part)))

@app.route('/api/lezioni/<int:id>/prenota', methods=['POST'])
@login_required
def api_prenota(id):
    uid = session['user_id']
    with db_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT id_prenotazione FROM prenotazione WHERE id_lezione=%s AND id_utente=%s AND stato!='Annullata'", (id, uid))
            if cur.fetchone(): return err('Già prenotato')
            cur.execute("SELECT numero_massimo_partecipanti FROM lezione WHERE id_lezione=%s", (id,))
            lez = cur.fetchone()
            if not lez: return err('Lezione non trovata', 404)
            cur.execute("SELECT COUNT(*) AS n FROM prenotazione WHERE id_lezione=%s AND stato='Confermata'", (id,))
            if cur.fetchone()['n'] >= (lez['numero_massimo_partecipanti'] or 99):
                return err('Posti esauriti')
            cur.execute("INSERT INTO prenotazione (data_prenotazione,stato,id_utente,id_lezione) VALUES (%s,'Confermata',%s,%s)",
                        (date.today(), uid, id))
            conn.commit()
            return ok(message='Prenotazione confermata!')

@app.route('/api/lezioni/<int:id>/annulla', methods=['POST'])
@login_required
def api_annulla(id):
    uid = session['user_id']
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE prenotazione SET stato='Annullata' WHERE id_lezione=%s AND id_utente=%s", (id, uid))
            conn.commit()
            return ok(message='Prenotazione annullata.')

# ─────────────────────────────────────────────────────────────────────────────
# API: MIE LEZIONI
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/api/mie-lezioni')
@login_required
def api_mie_lezioni():
    uid = session['user_id']
    today = str(date.today())
    with db_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""SELECT l.id_lezione,l.titolo,l.data_lezione::text,l.orario::text,
                                  l.modalita,l.luogo,l.numero_massimo_partecipanti,
                                  u.nome||' '||u.cognome AS nome_insegnante, c.nome_competenza AS categoria
                           FROM prenotazione p JOIN lezione l ON p.id_lezione = l.id_lezione
                           JOIN utente u ON l.id_insegnante = u.id_utente
                           LEFT JOIN competenza c ON l.id_competenza = c.id_competenza
                           WHERE p.id_utente = %s AND p.stato = 'Confermata' ORDER BY l.data_lezione DESC""", (uid,))
            freq = [dict(r) for r in (cur.fetchall() or [])]
            cur.execute("""SELECT l.id_lezione,l.titolo,l.data_lezione::text,l.orario::text,
                                  l.modalita,l.luogo,l.numero_massimo_partecipanti,
                                  c.nome_competenza AS categoria
                           FROM lezione l LEFT JOIN competenza c ON l.id_competenza = c.id_competenza
                           WHERE l.id_insegnante = %s ORDER BY l.data_lezione DESC""", (uid,))
            ins = [dict(r) for r in (cur.fetchall() or [])]
            for l in ins:
                cur.execute("""SELECT u.nome,u.cognome,u.username FROM prenotazione p
                               JOIN utente u ON p.id_utente = u.id_utente
                               WHERE p.id_lezione = %s AND p.stato = 'Confermata'""", (l['id_lezione'],))
                l['partecipanti'] = [dict(r) for r in (cur.fetchall() or [])]
            for r in freq + ins: r['passata'] = r['data_lezione'] < today
            return ok(frequentando=freq, insegnando=ins)

# ─────────────────────────────────────────────────────────────────────────────
# API: PROFILO & COMPETENZE UTENTE
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/api/profilo')
@login_required
def api_profilo():
    uid = session['user_id']
    with db_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT id_utente,nome,cognome,email,descrizione_profilo,data_registrazione::text,username,codice_univoco FROM utente WHERE id_utente=%s", (uid,))
            user = dict(cur.fetchone() or {})
            if not user: return err('Utente non trovato', 404)
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
            return ok(user=user, stats={'lezioni_date': ld, 'competenze': nc, 'media_feedback': media},
                      lezioni_create=lc, competenze=comps, feedback=fb, competenze_list=cl)

@app.route('/api/profilo/aggiorna', methods=['POST'])
@login_required
def api_aggiorna_profilo():
    d = request.get_json() or {}
    uid = session['user_id']
    nome = (d.get('nome') or '').strip()
    cognome = (d.get('cognome') or '').strip()
    bio = (d.get('descrizione_profilo') or '').strip()
    username = (d.get('username') or '').strip().lower()

    if contiene_inappropriato(nome) or contiene_inappropriato(cognome) or contiene_inappropriato(bio) or contiene_inappropriato(username):
        return err('Il testo inserito contiene espressioni non consentite!')

    if username and not is_valid_username(username): return err('Username non valido')
    
    with db_conn() as conn:
        with conn.cursor() as cur:
            try:
                if username:
                    cur.execute("UPDATE utente SET nome=%s,cognome=%s,descrizione_profilo=%s,username=%s WHERE id_utente=%s",
                                (nome, cognome, censura(bio), username, uid))
                else:
                    cur.execute("UPDATE utente SET nome=%s,cognome=%s,descrizione_profilo=%s WHERE id_utente=%s",
                                (nome, cognome, censura(bio), uid))
                conn.commit()
            except psycopg2.errors.UniqueViolation:
                conn.rollback()
                return err('Username già in uso')
    session['user_name'] = nome
    session['user_cognome'] = cognome
    if username: session['user_username'] = username
    return ok(message='Profilo aggiornato!')

# MAPPATURA LIVELLO COMPETENZE FAIL-SAFE
@app.route('/api/competenze/aggiungi', methods=['POST'])
@login_required
def api_aggiungi_comp():
    d = request.get_json() or {}
    uid = session['user_id']
    if not d.get('id_competenza'): return err('Seleziona una competenza')
    
    livello = d.get('livello', 'Intermedio')
    tipo = d.get('tipo', 'Offerta')
    
    # Conversione fail-safe per superare i Check Constraints
    if livello == 'Principiante': livello = 'Base'
    if livello == 'Esperto': livello = 'Avanzato'
    
    with db_conn() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute("INSERT INTO utente_competenza (id_utente,id_competenza,livello,tipo) VALUES (%s,%s,%s,%s)",
                            (uid, d['id_competenza'], livello, tipo))
                conn.commit()
            except psycopg2.errors.UniqueViolation:
                conn.rollback()
            except Exception as e:
                conn.rollback()
                print(f"[COMPETENZA INSERT EXCEPTION] {e}")
                return err('Errore nel salvataggio della competenza')
    return ok(message='Competenza salvata con successo!')

# ─────────────────────────────────────────────────────────────────────────────
# API: MESSAGGI (RICERCA E INVIO VIA HTTP ROBUSTO)
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/api/utenti/cerca')
@login_required
def api_cerca_utente():
    q = (request.args.get('q') or '').strip()
    uid = session['user_id']
    if not q: return err('Inserisci codice o username')
    
    with db_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""SELECT id_utente,nome,cognome,username,codice_univoco,descrizione_profilo
                           FROM utente WHERE id_utente!=%s
                           AND (UPPER(codice_univoco)=%s OR LOWER(username)=%s) LIMIT 1""",
                        (uid, q.upper(), q.lower().lstrip('@')))
            u = cur.fetchone()
            if not u: return err('Nessun utente trovato con questo codice o username', 404)
            return ok(utente={'id': u['id_utente'], 'nome': u['nome'] + ' ' + u['cognome'], 'codice_univoco': u['codice_univoco']})

@app.route('/api/messaggi/conversazioni')
@login_required
def api_conversazioni():
    uid = session['user_id']
    q = (request.args.get('q') or '').strip()
    with db_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
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
            return ok(conversazioni=r)

@app.route('/api/messaggi/chat/<int:other_id>')
@login_required
def api_chat(other_id):
    uid = session['user_id']
    with db_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
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
            if not other: return err('Utente non trovato', 404)
            last_id = msgs[-1]['id_messaggio'] if msgs else 0
            return ok(messaggi=msgs, interlocutore=dict(other), last_id=last_id, my_user_id=uid)

@app.route('/api/messaggi/invia', methods=['POST'])
@login_required
def api_invia_messaggio():
    uid = session['user_id']
    d = request.get_json() or {}
    dest_id = d.get('destinatario_id')
    contenuto = (d.get('contenuto') or '').strip()
    if not dest_id or not contenuto:
        return err('Dati mancanti')
    
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO messaggio (id_mittente,id_destinatario,contenuto) VALUES (%s,%s,%s) "
                "RETURNING id_messaggio, TO_CHAR(data_invio,'HH24:MI') AS ora",
                (uid, dest_id, contenuto)
            )
            row_ = cur.fetchone()
            conn.commit()
            
            msg_payload = {
                'id_messaggio': row_[0],
                'id_mittente': uid,
                'contenuto': contenuto,
                'ora': row_[1],
                'out': False
            }
            socketio.emit('nuovo_messaggio', msg_payload, room=f'user_{dest_id}')
            socketio.emit('nuovo_messaggio', {**msg_payload, 'out': True}, room=f'user_{uid}')
            
            return ok(messaggio={'id_messaggio': row_[0], 'ora': row_[1]})

# ─────────────────────────────────────────────────────────────────────────────
# GESTIONE ADMIN: ENDPOINTS CRUD
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/api/admin/utenti', methods=['GET'])
@admin_required
def api_admin_get_utenti():
    with db_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT id_utente, nome, cognome, email, username, codice_univoco FROM utente WHERE username != 'adminsskill' ORDER BY id_utente DESC")
            return ok(utenti=cur.fetchall() or [])

@app.route('/api/admin/utenti/<int:uid>', methods=['DELETE'])
@admin_required
def api_admin_delete_utente(uid):
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM utente WHERE id_utente=%s AND username != 'adminsskill'", (uid,))
            conn.commit()
            return ok(message="Utente rimosso dal sistema.")

@app.route('/api/admin/lezioni', methods=['GET'])
@admin_required
def api_admin_get_lezioni():
    with db_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""SELECT l.id_lezione, l.titolo, l.descrizione, l.data_lezione::text, l.orario::text, 
                                  u.nome || ' ' || u.cognome AS nome_insegnante 
                           FROM lezione l JOIN utente u ON l.id_insegnante = u.id_utente ORDER BY l.id_lezione DESC""")
            return ok(lezioni=cur.fetchall() or [])

@app.route('/api/admin/lezioni/<int:lid>', methods=['DELETE'])
@admin_required
def api_admin_delete_lezione(lid):
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM lezione WHERE id_lezione=%s", (lid,))
            conn.commit()
            return ok(message="Corso rimosso dal sistema.")

@app.route('/api/admin/competenze', methods=['GET', 'POST'])
@admin_required
def api_admin_competenze():
    with db_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            if request.method == 'GET':
                cur.execute("SELECT * FROM competenza ORDER BY id_competenza DESC")
                return ok(competenze=cur.fetchall() or [])
            else:
                d = request.get_json() or {}
                nome = d.get('nome_competenza','').strip()
                cat = d.get('categoria','').strip()
                desc = d.get('descrizione','').strip()
                if not nome or not cat: return err('Materia e categoria obbligatorie')
                cur.execute("INSERT INTO competenza (nome_competenza, categoria, descrizione) VALUES (%s,%s,%s)", (nome, cat, desc))
                conn.commit()
                return ok(message="Materia aggiunta al catalogo globale.")

@app.route('/api/admin/competenze/<int:cid>', methods=['DELETE'])
@admin_required
def api_admin_delete_competenza(cid):
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM competenza WHERE id_competenza=%s", (cid,))
            conn.commit()
            return ok(message="Materia rimossa con successo dal catalogo.")

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)