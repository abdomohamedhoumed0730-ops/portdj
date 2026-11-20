"""
Tableau de bord portuaire – vu depuis un terminal de Long Beach.
Lancer :  streamlit run app.py
Clé aisstream.io : dans .streamlit/secrets.toml (local) ou dans Settings → Secrets (Streamlit Cloud),
sous le nom AISSTREAM_API_KEY. Elle n'est jamais écrite dans le code.
"""
import streamlit as st

st.set_page_config(page_title="Terminal Long Beach – tableau de bord", page_icon="⚓",
                   layout="wide", initial_sidebar_state="expanded")

# ---- Habillage : palette bleu marine / sarcelle, cartes, bannière ----
st.markdown("""
<style>
h1, h2, h3 { color: #0B3C5D; letter-spacing: -0.3px; }
h2 { border-bottom: 2px solid #D5E3EA; padding-bottom: 4px; margin-top: 1.2rem; }

.hero {
    background: linear-gradient(120deg, #0B3C5D 0%, #0B7285 100%);
    color: #FFFFFF; border-radius: 18px; padding: 22px 28px; margin-bottom: 18px;
    box-shadow: 0 4px 14px rgba(11, 60, 93, 0.25);
}
.hero-titre { font-size: 1.85rem; font-weight: 800; line-height: 1.2; }
.hero-sous { font-size: 1rem; opacity: 0.92; margin-top: 4px; }
.hero-chips { margin-top: 12px; }
.hero-chips span {
    display: inline-block; background: rgba(255, 255, 255, 0.16); border-radius: 999px;
    padding: 3px 12px; margin: 0 6px 6px 0; font-size: 0.85rem; font-weight: 600;
}

[data-testid="stMetric"] {
    background: #FFFFFF; border-radius: 14px; padding: 14px 16px;
    box-shadow: 0 1px 4px rgba(11, 60, 93, 0.12); border-top: 4px solid #0B7285;
}
[data-testid="stMetricValue"] { color: #0B3C5D; font-weight: 700; }
[data-testid="stMetricLabel"] p { color: #4A6572; font-weight: 600; }
[data-testid="stAlert"] { border-radius: 10px; }
[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; }
[data-testid="stSidebar"] { background: #EAF2F5; }
[data-testid="stSidebar"] h3 { color: #0B3C5D; }
</style>
""", unsafe_allow_html=True)

# ---- Barre latérale : comment lire le tableau, en clair ----
with st.sidebar:
    st.markdown("### 🧭 Comment lire ce tableau")
    st.markdown(
        "1. **Synthèse** : les indicateurs clés et les recommandations du moment.\n"
        "2. **Volumes LA & LB** : l'historique, la prévision à 3 mois et les mois atypiques.\n"
        "3. **Comparaison mondiale** : Long Beach face aux autres ports, dont Djibouti.\n"
        "4. **Temps réel** : navires et météo, mis à jour chaque minute.\n"
        "5. **Sources & méthode** : d'où viennent les chiffres, et leurs limites."
    )
    st.info("Chaque tuile indique sa **valeur**, sa **référence**, sa **tendance** et sa **date de mise à jour**.")
    st.caption("Projet M2 IAMD · Université de Djibouti")

# ---- Bannière d'en-tête (affichée sur toutes les pages) ----
st.markdown("""
<div class="hero">
  <div class="hero-titre">⚓ Terminal de Long Beach</div>
  <div class="hero-sous">Tableau de bord portuaire · San Pedro Bay, ses concurrents et Djibouti</div>
  <div class="hero-chips">
    <span>EVP mensuels</span><span>CPPI</span><span>CNUCED</span><span>AIS en direct</span><span>Météo</span>
  </div>
</div>
""", unsafe_allow_html=True)

pages = [
    st.Page("views/synthese.py", title="Synthèse", icon="📋", default=True),
    st.Page("views/volumes.py", title="Volumes LA & LB", icon="📦"),
    st.Page("views/benchmark.py", title="Comparaison mondiale", icon="🌍"),
    st.Page("views/temps_reel.py", title="Temps réel", icon="📡"),
    st.Page("views/sources.py", title="Sources & méthode", icon="📚"),
]
st.navigation(pages).run()
