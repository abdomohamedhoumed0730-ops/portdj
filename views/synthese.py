import pandas as pd
import streamlit as st

from lib import commun, direct, regles
from lib.donnees import cnuced, mois_fr, nb

ZONE = "Long Beach / Los Angeles"

st.title("🏗️ Terminal de Long Beach : les jours et le mois qui viennent")
st.caption("Pour le chef des opérations d'un terminal à conteneurs du Port of Long Beach : dimensionner les équipes et "
           "les postes à quai, et situer Long Beach face à ses concurrents (Los Angeles, Vancouver, Prince Rupert), "
           "à Busan et à Djibouti.")

i = commun.indicateurs_historiques()
c, p1 = i["cppi"], i["prev"].iloc[0]
u = cnuced()
tn = u[u.marche == "Tous navires"].dropna(subset=["temps_median_j"])
an = int(tn.annee.max())
t_us = tn[(tn.pays == "États-Unis") & (tn.annee == an)].temps_median_j.iloc[0]
t_ca = tn[(tn.pays == "Canada") & (tn.annee == an)].temps_median_j.iloc[0]
il_y_a_un_an = i["dernier"] - pd.DateOffset(years=1)

st.subheader("Historique et comparaison")
col = st.columns(4)
commun.tuile(col[0], f"EVP Long Beach – {mois_fr(i['dernier'])}", f"{nb(i['lb'] / 1e3)} k",
             f"{(i['lb'] / i['lb_n1'] - 1) * 100:+.1f} % sur un an".replace(".", ","),
             f"{mois_fr(il_y_a_un_an)} : {nb(i['lb_n1'] / 1e3)} k EVP", i["maj"],
             aide="Total comparable = imports pleins + exports pleins + vides à l'export.")
commun.tuile(col[1], "Part de Long Beach dans San Pedro Bay (12 mois)", f"{nb(i['part'], 1)} %",
             f"{i['part'] - i['part19']:+.1f} pt vs 2019".replace(".", ","), f"2019 : {nb(i['part19'], 1)} %", i["maj"])
commun.tuile(col[2], f"Prévision Long Beach – {mois_fr(i['mois_prev'])}", f"{nb(p1.prevision / 1e3)} k",
             f"{(p1.prevision / i['ref_prev'] - 1) * 100:+.1f} % vs N-1".replace(".", ","),
             f"{mois_fr(i['mois_prev'] - pd.DateOffset(years=1))} réel : {nb(i['ref_prev'] / 1e3)} k ; "
             f"marge 80 % : {nb(p1.bas80 / 1e3)}–{nb(p1.haut80 / 1e3)} k",
             f"STL + ARIMA, erreur test {nb(i['test']['erreur_modele'], 1)} %")
commun.tuile(col[3], "Rang CPPI 2025 : Long Beach | Djibouti",
             f"{int(c.loc['Long Beach', 'rang2025'])} | {int(c.loc['Djibouti', 'rang2025'])}",
             f"LB {int(c.loc['Long Beach', 'rang2024'] - c.loc['Long Beach', 'rang2025']):+d} places vs 2024",
             f"Vancouver {int(c.loc['Vancouver', 'rang2025'])} · Prince Rupert {int(c.loc['Prince Rupert', 'rang2025'])} · "
             f"Busan {int(c.loc['Busan', 'rang2025'])}", "CPPI 2025 (400 ports)")

st.subheader("Temps réel et actions")


@st.fragment(run_every="60s")
def bloc_direct():
    nav, msg, secours = commun.navires(ZONE)
    n = None
    if len(nav):
        # en route (statut 0, vitesse > 0,5 nœud) ou au mouillage (statut 1) dans la zone portuaire
        n = int(((nav.statut_code == 1) | ((nav.statut_code == 0) & (nav.vitesse_noeuds.fillna(0) > 0.5))).sum())
    m = commun.meteo(ZONE)
    g = direct.fenetre_grues(m)
    col = st.columns(3)
    commun.tuile(col[0], f"Temps médian au port – États-Unis ({an})", f"{nb(t_us, 2)} j",
                 f"{nb((t_us - t_ca) * 24)} h de plus que le Canada", f"Canada : {nb(t_ca, 2)} j (tous navires)",
                 "CNUCED, mise à jour du 26/03/2024", inverse=True)
    commun.tuile(col[1], "Navires en route ou au mouillage (AIS)", "—" if n is None else f"{n}",
                 None if n is None else f"{n - direct.SEUIL_NAVIRES:+d} vs seuil", f"seuil : {direct.SEUIL_NAVIRES} navires",
                 msg or f"en direct, {len(nav)} navires vus depuis moins de 20 min", inverse=True)
    commun.tuile(col[2], "Heures d'arrêt probable des grues (48 h)", "—" if g is None else f"{g['heures_arret']} h",
                 None if g is None else f"{g['heures_vigilance']} h en vigilance",
                 f"rafales ≥ {direct.ARRET_GRUES_KMH:.0f} km/h (arrêt) ; ≥ {direct.VIGILANCE_KMH:.0f} km/h ou 2 m (vigilance)",
                 "Open-Meteo, " + (m["releve"] or "indisponible") + (" (relevé de secours)" if m["secours"] and m["releve"] else ""),
                 inverse=True)
    if m["secours"]:
        st.warning(f"Météo : source indisponible ({m['erreur']})." + (" Dernier relevé affiché." if m["vent"] else ""))
    if n is None:
        st.warning(f"AIS : {msg or 'aucune donnée'}.")
    elif secours:
        st.warning(f"AIS : {msg}.")

    st.markdown("**Recommandations**")
    ctx = {"prevision_vs_n1": (p1.prevision / i["ref_prev"] - 1) * 100, "mois_prev": mois_fr(i["mois_prev"]),
           "prevision": p1.prevision, "ref_prev": i["ref_prev"], "grues": g, "navires_attendus": n,
           "score_lb": c.loc["Long Beach", "cppi2025"], "score_la": c.loc["Los Angeles", "cppi2025"],
           "score_busan": c.loc["Busan", "cppi2025"]}
    for icone, action, pourquoi in regles.recommandations(ctx):
        st.markdown(f"{icone} **{action}**  \n<small>Déclencheur : {pourquoi}</small>", unsafe_allow_html=True)


bloc_direct()
