-- ============================================================
-- SkillBridge — Database completo con dati reali
-- Versione: 2.0 | Data: Aprile 2026
-- Password di tutti gli utenti demo: 123456
-- ============================================================

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";
SET NAMES utf8mb4;

-- ============================================================
-- DATABASE
-- ============================================================
-- CREATE DATABASE IF NOT EXISTS `progetto_interdisciplinare`;
-- USE `progetto_interdisciplinare`;

-- ============================================================
-- DROP (ordine inverso per FK)
-- ============================================================
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS `feedback`;
DROP TABLE IF EXISTS `materiale`;
DROP TABLE IF EXISTS `prenotazione`;
DROP TABLE IF EXISTS `messaggio`;
DROP TABLE IF EXISTS `utente_competenza`;
DROP TABLE IF EXISTS `lezione`;
DROP TABLE IF EXISTS `competenza`;
DROP TABLE IF EXISTS `reset_password`;
DROP TABLE IF EXISTS `utente`;
SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================
-- TABELLA: utente
-- ============================================================
CREATE TABLE `utente` (
  `id_utente`           int(11)      NOT NULL AUTO_INCREMENT,
  `nome`                varchar(50)  NOT NULL,
  `cognome`             varchar(50)  NOT NULL,
  `email`               varchar(100) NOT NULL,
  `password`            varchar(255) NOT NULL,
  `data_registrazione`  date         DEFAULT NULL,
  `descrizione_profilo` text         DEFAULT NULL,
  `foto_profilo`        varchar(255) DEFAULT NULL,
  `username`            varchar(30)  DEFAULT NULL,
  `codice_univoco`      varchar(20)  DEFAULT NULL,
  PRIMARY KEY (`id_utente`),
  UNIQUE KEY `email`           (`email`),
  UNIQUE KEY `username`        (`username`),
  UNIQUE KEY `codice_univoco`  (`codice_univoco`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- password = 123456 per tutti
INSERT INTO `utente` VALUES
(14, 'Luca',           'Razzoli',    'razzoli.luca@einaudicorreggio.it',
 '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92',
 '2026-04-17', 'Appassionato di economia e finanza. Studio e insegno gestione aziendale.', NULL,
 'razzoli.luca', 'SB-A1B2-C3D4'),

(15, 'Michele',        'Saccani',    'saccani.michele@einaudicorreggio.it',
 '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92',
 '2026-04-17', 'Sviluppatore e musicista. Offro lezioni di programmazione e pianoforte.', NULL,
 'saccani.michele', 'SB-E5F6-G7H8'),

(16, 'Matteo',         'Casali',     'casali.matteo@einaudicorreggio.it',
 '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92',
 '2026-04-17', 'Sportivo e appassionato di baseball. Alleno giovani atleti nel tempo libero.', NULL,
 'casali.matteo', 'SB-I9J0-K1L2'),

(17, 'Angelo Christian','Arianiello', 'arianiello.angelochristian@einaudicorreggio.it',
 '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92',
 '2026-04-17', 'Appassionato di robotica, elettronica e svariati hobby creativi.', NULL,
 'arianiello.angel', 'SB-M3N4-O5P6'),

(18, 'Davide',         'Campani',    'campani.davide@einaudicorreggio.it',
 '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92',
 '2026-04-17', 'Insegnante di matematica e fisica. Preparo agli esami con metodo Feynman.', NULL,
 'campani.davide', 'SB-Q7R8-S9T0'),

(19, 'Sara',           'Verdi',      'verdi.sara@einaudicorreggio.it',
 '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92',
 '2026-04-17', 'Studentessa di lettere, offro ripetizioni di italiano e storia dell arte.', NULL,
 'verdi.sara', 'SB-U1V2-W3X4'),

(20, 'Marco',          'Ferretti',   'ferretti.marco@einaudicorreggio.it',
 '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92',
 '2026-04-17', 'Madrelingua inglese, offro conversazione e preparazione certificazioni.', NULL,
 'ferretti.marco', 'SB-Y5Z6-A7B8');

-- ============================================================
-- TABELLA: competenza
-- ============================================================
CREATE TABLE `competenza` (
  `id_competenza`   int(11)      NOT NULL AUTO_INCREMENT,
  `nome_competenza` varchar(100) NOT NULL,
  `descrizione`     text         DEFAULT NULL,
  `categoria`       varchar(50)  DEFAULT NULL,
  PRIMARY KEY (`id_competenza`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `competenza` (`id_competenza`, `nome_competenza`, `descrizione`, `categoria`) VALUES
-- Materie base
(1,  'Italiano',            'Grammatica, analisi del testo, letteratura italiana',             'Materie Base'),
(2,  'Storia',              'Storia moderna, contemporanea e locale',                          'Materie Base'),
(3,  'Matematica',          'Algebra, geometria, analisi e statistica',                        'Materie Base'),
(4,  'Inglese',             'Grammatica, conversazione e preparazione certificazioni',          'Materie Base'),
(5,  'Scienze',             'Biologia, chimica e scienze della terra',                         'Materie Base'),
(6,  'Fisica',              'Meccanica, termodinamica, elettromagnetismo',                     'Materie Base'),
(7,  'Arte',                'Storia dell arte, pittura e disegno tecnico',                     'Arte'),
-- Informatica
(8,  'Informatica',         'Fondamenti di informatica e uso del computer',                    'Informatica'),
(9,  'Programmazione',      'Sviluppo software: Python, JavaScript, Java, C++',                'Informatica'),
(10, 'Sistemi e Reti',      'Architetture di rete, TCP/IP, sicurezza informatica',             'Informatica'),
(11, 'Web Development',     'HTML, CSS, JavaScript, framework moderni',                        'Informatica'),
(12, 'Robotica',            'Arduino, Raspberry Pi, elettronica di base',                      'Informatica'),
-- Economia
(13, 'Economia',            'Microeconomia, macroeconomia, economia aziendale',                'Economia'),
(14, 'Gestione Economica',  'Contabilità, bilancio, finanza personale e aziendale',            'Economia'),
(15, 'Marketing',           'Strategie di marketing, social media, brand identity',            'Economia'),
-- Musica
(16, 'Pianoforte',          'Teoria musicale, tecnica pianistica, lettura spartiti',           'Musica'),
(17, 'Chitarra',            'Chitarra classica e moderna, accordi, improvvisazione',           'Musica'),
(18, 'Musica',              'Solfeggio, teoria musicale generale, ear training',               'Musica'),
-- Sport
(19, 'Baseball',            'Tecniche di lancio, battuta e difesa',                            'Sport'),
(20, 'Calcio',              'Tecnica individuale, tattica e preparazione atletica',            'Sport'),
(21, 'Basket',              'Fondamentali, tiro, difesa e gioco di squadra',                   'Sport'),
(22, 'Tennis',              'Tecnica di base, servizio e tattica di gioco',                    'Sport'),
(23, 'Nuoto',               'Stili di nuoto, respirazione, allenamento',                       'Sport');

-- ============================================================
-- TABELLA: utente_competenza
-- ============================================================
CREATE TABLE `utente_competenza` (
  `id_utente`    int(11)                        NOT NULL,
  `id_competenza` int(11)                       NOT NULL,
  `livello`      enum('Base','Intermedio','Avanzato') DEFAULT NULL,
  `tipo`         enum('Offerta','Richiesta')    NOT NULL,
  PRIMARY KEY (`id_utente`, `id_competenza`, `tipo`),
  KEY `id_competenza` (`id_competenza`),
  CONSTRAINT `uc_utente` FOREIGN KEY (`id_utente`)     REFERENCES `utente`     (`id_utente`)     ON DELETE CASCADE,
  CONSTRAINT `uc_comp`   FOREIGN KEY (`id_competenza`) REFERENCES `competenza` (`id_competenza`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `utente_competenza` VALUES
-- Luca Razzoli: insegna economia, studia programmazione
(14, 13, 'Avanzato',   'Offerta'),
(14, 14, 'Avanzato',   'Offerta'),
(14,  9, 'Base',       'Richiesta'),
-- Michele Saccani: insegna programmazione e pianoforte
(15,  9, 'Avanzato',   'Offerta'),
(15, 11, 'Avanzato',   'Offerta'),
(15, 16, 'Intermedio', 'Offerta'),
(15,  3, 'Base',       'Richiesta'),
-- Matteo Casali: insegna baseball, studia economia
(16, 19, 'Avanzato',   'Offerta'),
(16, 20, 'Intermedio', 'Offerta'),
(16, 14, 'Base',       'Richiesta'),
-- Angelo: insegna robotica e sistemi
(17, 12, 'Avanzato',   'Offerta'),
(17, 10, 'Intermedio', 'Offerta'),
(17,  9, 'Intermedio', 'Offerta'),
-- Davide: insegna matematica e fisica
(18,  3, 'Avanzato',   'Offerta'),
(18,  6, 'Avanzato',   'Offerta'),
(18,  5, 'Intermedio', 'Offerta'),
-- Sara: insegna italiano e storia
(19,  1, 'Avanzato',   'Offerta'),
(19,  2, 'Avanzato',   'Offerta'),
(19,  7, 'Intermedio', 'Offerta'),
-- Marco: insegna inglese
(20,  4, 'Avanzato',   'Offerta'),
(20, 15, 'Intermedio', 'Offerta');

-- ============================================================
-- TABELLA: lezione  (12 lezioni con date future dal 2026-05)
-- ============================================================
CREATE TABLE `lezione` (
  `id_lezione`                  int(11)                   NOT NULL AUTO_INCREMENT,
  `titolo`                      varchar(100)              NOT NULL,
  `descrizione`                 text                      DEFAULT NULL,
  `data_lezione`                date                      DEFAULT NULL,
  `orario`                      time                      DEFAULT NULL,
  `durata`                      int(11)                   DEFAULT NULL,
  `modalita`                    enum('Online','Presenza') DEFAULT NULL,
  `luogo`                       varchar(100)              DEFAULT NULL,
  `numero_massimo_partecipanti` int(11)                   DEFAULT NULL,
  `id_insegnante`               int(11)                   DEFAULT NULL,
  `id_competenza`               int(11)                   DEFAULT NULL,
  PRIMARY KEY (`id_lezione`),
  KEY `id_insegnante` (`id_insegnante`),
  KEY `id_competenza` (`id_competenza`),
  CONSTRAINT `lez_ins`  FOREIGN KEY (`id_insegnante`) REFERENCES `utente`     (`id_utente`)     ON DELETE CASCADE,
  CONSTRAINT `lez_comp` FOREIGN KEY (`id_competenza`) REFERENCES `competenza` (`id_competenza`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `lezione` (`titolo`,`descrizione`,`data_lezione`,`orario`,`durata`,`modalita`,`luogo`,`numero_massimo_partecipanti`,`id_insegnante`,`id_competenza`) VALUES
-- Michele Saccani (15) — Programmazione e Web
('Introduzione a Python',
 'Impara le basi di Python: variabili, cicli, funzioni. Perfetto per chi inizia da zero.',
 '2026-05-05','15:00',60,'Online','Google Meet',10,15,9),

('Basi di HTML e CSS',
 'Costruisci la tua prima pagina web da zero. Struttura HTML, stili CSS, box model.',
 '2026-05-12','16:00',90,'Online','Google Meet',8,15,11),

('Pianoforte per principianti',
 'Prima lezione di pianoforte: postura, scale di do maggiore, lettura delle note.',
 '2026-05-19','17:00',60,'Presenza','Aula Musica 2B',5,15,16),

-- Davide Campani (18) — Matematica e Fisica
('Algebra: equazioni di 2° grado',
 'Risoluzione completa di equazioni quadratiche, discriminante, casi particolari.',
 '2026-05-06','14:00',75,'Presenza','Aula 3A',12,18,3),

('Fisica: cinematica e moti',
 'Moto rettilineo uniforme, uniformemente accelerato, moto parabolico con esercizi.',
 '2026-05-14','15:30',90,'Presenza','Lab Fisica',10,18,6),

('Preparazione alla Maturità — Matematica',
 'Ripasso completo: analisi, derivate, integrali. Simulazione di seconda prova.',
 '2026-05-27','09:00',120,'Presenza','Aula Magna',20,18,3),

-- Sara Verdi (19) — Italiano e Storia
('Analisi del testo poetico',
 'Come affrontare la poesia: figure retoriche, metrica, commento. Esempi con Leopardi e Pascoli.',
 '2026-05-08','15:00',60,'Online','Google Meet',10,19,1),

('Storia del Novecento: le due guerre mondiali',
 'Prima e Seconda Guerra Mondiale: cause, sviluppi e conseguenze geopolitiche.',
 '2026-05-20','16:00',75,'Presenza','Aula 1B',15,19,2),

-- Luca Razzoli (14) — Economia
('Economia aziendale: il bilancio',
 'Stato patrimoniale, conto economico, rendiconto finanziario. Lettura e analisi.',
 '2026-05-09','14:30',90,'Presenza','Aula 4C',12,14,14),

('Gestione finanziaria personale',
 'Come gestire il budget, risparmio, investimenti basilari e prevenzione dei debiti.',
 '2026-05-22','17:00',60,'Online','Google Meet',15,14,13),

-- Matteo Casali (16) — Sport
('Baseball: tecnica di lancio',
 'Grip, windup, follow-through. Esercizi pratici per migliorare velocità e precisione.',
 '2026-05-10','10:00',90,'Presenza','Campo Sportivo',8,16,19),

-- Angelo Arianiello (17) — Robotica
('Arduino per principianti',
 'Installazione IDE, primo sketch Blink, sensori di distanza e LED. Porta il tuo laptop!',
 '2026-05-16','14:00',120,'Presenza','Lab Informatica',10,17,12);

-- ============================================================
-- TABELLA: prenotazione
-- ============================================================
CREATE TABLE `prenotazione` (
  `id_prenotazione`  int(11) NOT NULL AUTO_INCREMENT,
  `data_prenotazione` date   DEFAULT NULL,
  `stato`            enum('Confermata','Annullata','In attesa') DEFAULT NULL,
  `id_utente`        int(11) DEFAULT NULL,
  `id_lezione`       int(11) DEFAULT NULL,
  PRIMARY KEY (`id_prenotazione`),
  KEY `id_utente`  (`id_utente`),
  KEY `id_lezione` (`id_lezione`),
  CONSTRAINT `pren_utente`  FOREIGN KEY (`id_utente`)  REFERENCES `utente`  (`id_utente`)  ON DELETE CASCADE,
  CONSTRAINT `pren_lezione` FOREIGN KEY (`id_lezione`) REFERENCES `lezione` (`id_lezione`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `prenotazione` (`data_prenotazione`,`stato`,`id_utente`,`id_lezione`) VALUES
-- Luca si iscrive a Python e Pianoforte
('2026-04-20','Confermata',14,1),
('2026-04-20','Confermata',14,3),
-- Matteo si iscrive a Python e Algebra
('2026-04-21','Confermata',16,1),
('2026-04-21','Confermata',16,4),
-- Angelo si iscrive a Bilancio e Fisica
('2026-04-22','Confermata',17,5),
('2026-04-22','Confermata',17,9),
-- Sara si iscrive a Python
('2026-04-22','Confermata',19,1),
-- Marco si iscrive a Algebra e Storia Novecento
('2026-04-23','Confermata',20,4),
('2026-04-23','Confermata',20,8),
-- Michele si iscrive a Bilancio (studente qui)
('2026-04-23','Confermata',15,9);

-- ============================================================
-- TABELLA: feedback
-- ============================================================
CREATE TABLE `feedback` (
  `id_feedback`   int(11)  NOT NULL AUTO_INCREMENT,
  `voto`          int(11)  DEFAULT NULL CHECK (`voto` between 1 and 5),
  `commento`      text     DEFAULT NULL,
  `data_feedback` date     DEFAULT NULL,
  `id_lezione`    int(11)  DEFAULT NULL,
  `id_utente`     int(11)  DEFAULT NULL,
  PRIMARY KEY (`id_feedback`),
  KEY `id_lezione` (`id_lezione`),
  KEY `id_utente`  (`id_utente`),
  CONSTRAINT `fb_lezione` FOREIGN KEY (`id_lezione`) REFERENCES `lezione` (`id_lezione`) ON DELETE CASCADE,
  CONSTRAINT `fb_utente`  FOREIGN KEY (`id_utente`)  REFERENCES `utente`  (`id_utente`)  ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `feedback` (`voto`,`commento`,`data_feedback`,`id_lezione`,`id_utente`) VALUES
(5,'Lezione eccellente! Michele spiega in modo chiarissimo. Consiglio a tutti.','2026-04-18',1,14),
(5,'Ottimo insegnante, molto preparato e paziente. Tornerò sicuramente.','2026-04-18',1,16),
(4,'Buona lezione, qualche concetto andava approfondito ma nel complesso ottimo.','2026-04-19',4,20),
(5,'Davide è un professore fantastico. Con lui la matematica diventa semplice!','2026-04-19',4,16),
(4,'Sara spiega benissimo. L analisi del testo sembrava difficile, ora molto più chiara.','2026-04-20',7,20);

-- ============================================================
-- TABELLA: materiale
-- ============================================================
CREATE TABLE `materiale` (
  `id_materiale`     int(11)                          NOT NULL AUTO_INCREMENT,
  `id_lezione`       int(11)                          DEFAULT NULL,
  `tipo`             enum('pdf','doc','link_meet')    NOT NULL,
  `titolo`           varchar(100)                     DEFAULT NULL,
  `url_risorsa`      text                             DEFAULT NULL,
  `data_caricamento` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id_materiale`),
  KEY `id_lezione` (`id_lezione`),
  CONSTRAINT `mat_lezione` FOREIGN KEY (`id_lezione`) REFERENCES `lezione` (`id_lezione`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `materiale` (`id_lezione`,`tipo`,`titolo`,`url_risorsa`) VALUES
(1,'link_meet','Link Google Meet lezione Python','https://meet.google.com/abc-defg-hij'),
(2,'link_meet','Link Google Meet lezione Web','https://meet.google.com/klm-nopq-rst'),
(4,'pdf','Slide equazioni 2° grado','https://example.com/algebra.pdf'),
(7,'link_meet','Link Google Meet analisi testo','https://meet.google.com/uvw-xyz-123'),
(9,'pdf','Schema bilancio aziendale','https://example.com/bilancio.pdf');

-- ============================================================
-- TABELLA: messaggio
-- ============================================================
CREATE TABLE `messaggio` (
  `id_messaggio`    int(11) NOT NULL AUTO_INCREMENT,
  `id_mittente`     int(11) NOT NULL,
  `id_destinatario` int(11) NOT NULL,
  `contenuto`       text    NOT NULL,
  `data_invio`      datetime NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id_messaggio`),
  KEY `id_mittente`     (`id_mittente`),
  KEY `id_destinatario` (`id_destinatario`),
  CONSTRAINT `msg_mittente` FOREIGN KEY (`id_mittente`)     REFERENCES `utente` (`id_utente`) ON DELETE CASCADE,
  CONSTRAINT `msg_dest`     FOREIGN KEY (`id_destinatario`) REFERENCES `utente` (`id_utente`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `messaggio` (`id_mittente`,`id_destinatario`,`contenuto`,`data_invio`) VALUES
(14,15,'Ciao Michele! Ho visto la tua lezione di Python, quando è la prossima?','2026-04-18 10:15:00'),
(15,14,'Ciao Luca! Il 5 maggio alle 15:00 su Google Meet. Ti aspetto!','2026-04-18 10:20:00'),
(14,15,'Perfetto, ci sono! Devo portare qualcosa di specifico?','2026-04-18 10:25:00'),
(15,14,'Solo un computer con Python installato, ci penso io al resto.','2026-04-18 10:30:00'),
(16,18,'Ciao Davide, ho bisogno di aiuto con le equazioni quadratiche per la verifica.','2026-04-19 14:00:00'),
(18,16,'Certo Matteo! Ho una lezione il 6 maggio, iscriviti. Porterai gli esercizi dal libro?','2026-04-19 14:10:00'),
(16,18,'Sì, li porto! Grazie mille.','2026-04-19 14:15:00'),
(17,15,'Michele, come posso integrare Arduino con Python?','2026-04-20 09:00:00'),
(15,17,'Ottima domanda! Con la libreria PySerial. Te lo mostro a lezione!','2026-04-20 09:30:00');

-- ============================================================
-- TABELLA: reset_password  (per il 2FA via mail)
-- ============================================================
CREATE TABLE `reset_password` (
  `id`          int(11)      NOT NULL AUTO_INCREMENT,
  `id_utente`   int(11)      NOT NULL,
  `token`       varchar(64)  NOT NULL,
  `codice`      varchar(8)   NOT NULL,
  `scadenza`    datetime     NOT NULL,
  `usato`       tinyint(1)   DEFAULT 0,
  PRIMARY KEY (`id`),
  UNIQUE KEY `token` (`token`),
  KEY `id_utente` (`id_utente`),
  CONSTRAINT `rp_utente` FOREIGN KEY (`id_utente`) REFERENCES `utente` (`id_utente`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
