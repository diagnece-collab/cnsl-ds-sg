import streamlit as st
import sqlite3
import random
import json
import os
import time  # Import ajouté pour le chrono
from datetime import datetime

# --- CONFIGURATION & STYLE SÉNÉGAL ---
st.set_page_config(page_title="Conseil des Sages - Web", page_icon="🇸🇳", layout="centered")

SENEGAL_VERT = "#00853f"
SENEGAL_JAUNE = "#fdef42"
SENEGAL_ROUGE = "#e31b23"

st.markdown(f"""
    <style>
    .stApp {{ background-color: #121212; color: white; }}
    
    button[kind="primary"], button[kind="secondary"] {{
        width: 100% !important;
        border-radius: 10px !important; 
        min-height: 3.5em !important; 
        background-color: {SENEGAL_VERT} !important; 
        color: white !important; 
        font-weight: bold !important; 
        border: none !important;
        white-space: normal !important;
        padding: 10px !important;
        display: block !important;
    }}
    
    .stButton {{ width: 100% !important; }}
    .stButton>button:hover {{ border: 2px solid {SENEGAL_JAUNE} !important; color: {SENEGAL_JAUNE} !important; }}

    .stProgress > div > div > div > div {{ 
        background-image: linear-gradient(to right, {SENEGAL_VERT}, {SENEGAL_JAUNE}, {SENEGAL_ROUGE}); 
    }}
    
    /* STYLE DU PERMIS DE VOTER */
    .permis-card {{
        border: 5px double {SENEGAL_JAUNE};
        background-color: #f9f9f9;
        color: #1a1a1a;
        padding: 30px;
        border-radius: 15px;
        text-align: center;
        margin: 20px 0;
        background-image: url('https://www.transparenttextures.com/patterns/natural-paper.png');
    }}
    .permis-header {{ color: {SENEGAL_VERT}; font-weight: bold; font-size: 24px; margin-bottom: 10px; }}
    .permis-pseudo {{ font-family: 'Courier New', Courier, monospace; font-size: 28px; font-weight: bold; border-bottom: 2px solid #333; display: inline-block; padding: 0 20px; }}
    
    .err-container {{
        padding: 15px; background-color: #1A1A1A; border-radius: 10px; 
        border: 1px solid #333333; margin-bottom: 10px;
    }}
    
    h1, h2, h3, p {{ text-align: center !important; color: white; }}
    h1, h2, h3 {{ color: {SENEGAL_JAUNE} !important; }}
    
    .stTextInput > div > div > input {{ text-align: center; }}
    </style>
    """, unsafe_allow_html=True)

# --- BASE DE DONNÉES ---
def init_db():
    conn = sqlite3.connect("scores.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leaderboard (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pseudo TEXT NOT NULL,
            score INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def get_leaderboard_data():
    try:
        conn = sqlite3.connect("scores.db", check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT pseudo, score FROM leaderboard ORDER BY score DESC LIMIT 10")
        rows = cursor.fetchall()
        conn.close()
        return rows
    except: return []

def add_score_data(pseudo, score):
    try:
        conn = sqlite3.connect("scores.db", check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO leaderboard (pseudo, score) VALUES (?, ?)", (pseudo, score))
        conn.commit()
        conn.close()
    except: pass

def charger_questions():
    if os.path.exists("questions.json"):
        try:
            with open("questions.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except: return []
    return []

# --- INITIALISATION ---
init_db()
if 'state' not in st.session_state:
    st.session_state.state = "MENU"
    st.session_state.pseudo = "Anonyme"
    st.session_state.score = 0
    st.session_state.idx = 0
    st.session_state.questions_partie = []
    st.session_state.erreurs_commises = []
    st.session_state.start_time = 0 # Initialisation du chrono

banque_complete = charger_questions()

# --- INTERFACE ---
if st.session_state.state == "MENU":
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/f/fd/Flag_of_Senegal.svg/1200px-Flag_of_Senegal.svg.png", width=100)
    
    st.title("CONSEIL DES SAGES")
    p_input = st.text_input("Votre Pseudo", placeholder="Entrez votre nom...")
    
    if st.button("ENTRER DANS LE CONSEIL"):
        if not p_input:
            st.error("Le Conseil exige un nom")
        elif not banque_complete:
            st.error("questions.json est vide ou introuvable.")
        else:
            st.session_state.pseudo = p_input
            st.session_state.score = 0
            st.session_state.idx = 0
            st.session_state.erreurs_commises = []
            st.session_state.questions_partie = random.sample(banque_complete, min(len(banque_complete), 20))
            st.session_state.state = "QUIZ"
            st.session_state.start_time = time.time() # On lance le chrono au début du quiz
            st.rerun()

    st.divider()
    st.subheader("🏆 TOP 10 DES SAGES")
    ld = get_leaderboard_data()
    for i, entry in enumerate(ld):
        st.markdown(f"<p style='text-align:center'><b>{i+1}. {entry[0]}</b> — {entry[1]} pts</p>", unsafe_allow_html=True)

elif st.session_state.state == "QUIZ":
    qs = st.session_state.questions_partie
    current_q = qs[st.session_state.idx]

    # --- LOGIQUE DU CHRONOMÈTRE (20 SECONDES) ---
    TEMPS_LIMITE = 20
    temps_ecoule = time.time() - st.session_state.start_time
    temps_restant = max(0, TEMPS_LIMITE - temps_ecoule)
    
    st.write(f"DIAGNOSTIC {st.session_state.idx + 1} / {len(qs)}")
    st.progress((st.session_state.idx + 1) / len(qs))
    
    # Affichage du temps restant
    st.write(f"⏱️ Temps restant : {int(temps_restant)}s")
    st.progress(temps_restant / TEMPS_LIMITE)

    # Si le temps est écoulé
    if temps_restant <= 0:
        st.session_state.erreurs_commises.append({
            "q": current_q["q"],
            "v": "TEMPS ÉCOULÉ",
            "t": current_q["reponse"],
            "e": "La réflexion a dépassé le temps imparti par le Conseil."
        })
        st.session_state.idx += 1
        st.session_state.start_time = time.time() # Reset pour la suivante
        if st.session_state.idx >= len(qs):
            st.session_state.state = "VERDICT"
        st.rerun()
    
    st.markdown(f"""<div style="padding:20px; border-radius:15px; background-color:#1E1E1E; border:1px solid #333333; text-align:center; margin-bottom:20px;">
        <h3>{current_q['q']}</h3></div>""", unsafe_allow_html=True)
    
    _, col_centrale, _ = st.columns([0.5, 4, 0.5])
    with col_centrale:
        for opt in current_q["options"]:
            if st.button(opt, key=f"q_{st.session_state.idx}_{opt}", use_container_width=True):
                if opt == current_q["reponse"]:
                    st.session_state.score += 1
                else:
                    st.session_state.erreurs_commises.append({
                        "q": current_q["q"],
                        "v": opt,
                        "t": current_q["reponse"],
                        "e": current_q.get("explication", "La vérité est établie par le Conseil.")
                    })
                st.session_state.idx += 1
                st.session_state.start_time = time.time() # Reset pour la suivante
                if st.session_state.idx >= len(qs):
                    st.session_state.state = "VERDICT"
                st.rerun()
    
    # Rafraîchir l'interface pour le décompte
    time.sleep(1)
    st.rerun()

elif st.session_state.state == "VERDICT":
    st.title("⚖️ VERDICT SOUVERAIN")
    
    if 'score_saved' not in st.session_state:
        add_score_data(st.session_state.pseudo, st.session_state.score)
        st.session_state.score_saved = True

    total = len(st.session_state.questions_partie)
    score_final = st.session_state.score
    admis = (score_final / total) >= 0.75 if total > 0 else False
    
    st.write(f"Citoyen **{st.session_state.pseudo}**, score : **{score_final} / {total}**")

    if admis:
        # --- GÉNÉRATION DU PERMIS ---
        date_jour = datetime.now().strftime("%d/%m/%Y")
        st.markdown(f"""
            <div class="permis-card">
                <div style="color:{SENEGAL_ROUGE}; font-weight:bold;">RÉPUBLIQUE DU SÉNÉGAL</div>
                <div class="permis-header">CARTE D'APTITUDE AU VOTE</div>
                <p>Le Conseil des Sages certifie que</p>
                <div class="permis-pseudo">{st.session_state.pseudo}</div>
                <p>est déclaré <b>APTE</b> à participer aux décisions de la Nation.</p>
                <div style="margin-top:20px; font-size:12px; border-top:1px solid #ccc; padding-top:10px;">
                    Délivré le {date_jour} • Sagesse, Justice, Unité
                </div>
            </div>
        """, unsafe_allow_html=True)
        st.success("Félicitations ! Vous avez prouvé votre sagesse.")
    else:
        st.markdown(f"""<div style="background-color:{SENEGAL_ROUGE}; padding:20px; border-radius:15px; text-align:center; font-weight:bold; font-size:22px; color:white; margin-bottom:20px;">
            CAPACITÉ REJETÉE</div>""", unsafe_allow_html=True)
        st.warning("Le Conseil estime que vos connaissances doivent être approfondies.")

    if st.session_state.erreurs_commises:
        with st.expander("VOIR LES ÉCARTS À RECTIFIER"):
            for err in st.session_state.erreurs_commises:
                st.markdown(f"""<div class="err-container">
                    <b>Question :</b> {err['q']}<br>
                    <span style="color:{SENEGAL_ROUGE}">✘ Réponse : {err['v']}</span><br>
                    <span style="color:{SENEGAL_VERT}">✔ Vérité : {err['t']}</span><br>
                    <small><i>Note : {err['e']}</i></small></div>""", unsafe_allow_html=True)

    if st.button("RETOUR AU MENU", use_container_width=True):
        if 'score_saved' in st.session_state: del st.session_state.score_saved
        st.session_state.state = "MENU"
        st.rerun()
