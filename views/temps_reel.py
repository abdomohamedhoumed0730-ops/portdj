import altair as alt
import pandas as pd
import pydeck as pdk
import streamlit as st

from lib import commun, direct
from lib.donnees import nb

st.title("📡 Temps réel : navires et météo")
nom = st.segmented_control("Zone", list(direct.ZONES), default="Long Beach / Los Angeles")
zone = direct.ZONES[nom]
COULEURS = {"Au mouillage": [232, 89, 12], "En route": [25, 113, 194], "Amarré": [47, 158, 68]}
# Dégradé orange pour les clusters (du clair au foncé = moins de navires → plus de navires)
DEGRADE = [[254, 240, 217], [253, 204, 138], [253, 141, 60], [227, 74, 51], [179, 0, 0], [103, 0, 13]]


def couches(nav: pd.DataFrame, mode: str) -> list:
    """Construit les couches pydeck selon le mode d'affichage choisi."""
    if mode == "Carte de chaleur":
        # zones où les navires se concentrent : plus c'est chaud, plus il y a de navires
        return [pdk.Layer("HeatmapLayer", data=nav, get_position="[lon, lat]", aggregation="SUM",
                          radius_pixels=55, intensity=1.2, threshold=0.04)]
    if mode == "Clusters":
        # regroupement en hexagones : chaque hexagone compte les navires qu'il contient
        return [pdk.Layer("HexagonLayer", data=nav, get_position="[lon, lat]", radius=1200, elevation_scale=40,
                          extruded=True, pickable=True, coverage=0.9, color_range=DEGRADE)]
    # par défaut : un point par navire, coloré par statut
    nav = nav.assign(couleur=nav.statut.map(lambda s: COULEURS.get(s, [134, 142, 150])))
    return [pdk.Layer("ScatterplotLayer", data=nav, get_position="[lon, lat]", get_fill_color="couleur",
                      get_radius=220, radius_min_pixels=4, pickable=True)]


@st.fragment(run_every="60s")
def carte():
    nav, msg, secours = commun.navires(nom)
    if not len(nav):
        st.warning(f"Aucun navire affiché pour le moment : {msg or 'aucun message reçu'}."
                   + (" La couverture AIS gratuite est faible à Djibouti : les navires apparaissent surtout "
                      "quand ils arrivent dans les approches du golfe d'Aden." if zone["cle"] == "dji" else ""))
        return
    nav = nav.dropna(subset=["lat", "lon"]).copy()
    mode = st.segmented_control("Affichage", ["Points", "Carte de chaleur", "Clusters"], default="Points",
                                key="mode_carte")
    mode = mode or "Points"
    tooltip = ({"text": "{elevationValue} navires dans cet hexagone"} if mode == "Clusters"
               else {"text": "{nom}\n{type} – {statut}\n{vitesse_noeuds} nœuds"})
    st.pydeck_chart(pdk.Deck(layers=couches(nav, mode), map_provider="carto", map_style=pdk.map_styles.CARTO_LIGHT,
                             initial_view_state=pdk.ViewState(latitude=zone["centre"][0], longitude=zone["centre"][1],
                                                               zoom=zone["zoom"], pitch=0 if mode != "Clusters" else 35),
                             tooltip=tooltip), height=480)
    legende = {
        "Points": "🟠 au mouillage · 🔵 en route · 🟢 amarré · ⚪ autre ou non transmis.",
        "Carte de chaleur": "Rouge = forte concentration de navires ; bleu = peu de navires.",
        "Clusters": "Chaque hexagone regroupe les navires proches ; sa hauteur et sa couleur indiquent leur nombre.",
    }[mode]
    st.caption(f"{legende} " + (f"⚠️ {msg}." if secours else
                                "Mise à jour toutes les minutes ; navires vus depuis moins de 20 min."))
    k = st.columns(4)
    k[0].metric("Navires", len(nav))
    k[1].metric("Au mouillage", int((nav.statut_code == 1).sum()))
    k[2].metric("En route", int((nav.statut_code == 0).sum()))
    k[3].metric("Amarrés", int((nav.statut_code == 5).sum()))
    with st.expander("Détail par type et statut"):
        st.dataframe(nav.groupby(["type", "statut"]).size().unstack(fill_value=0), width="stretch")


carte()

st.subheader("Météo")
m = commun.meteo(nom)
if not m["vent"]:
    st.error(f"Météo indisponible ({m['erreur']}) et aucun relevé de secours.")
else:
    if m["secours"]:
        st.warning(f"Open-Meteo ne répond pas ({m['erreur']}) : relevé du {m['releve']}.")
    cur, cm = m["vent"]["current"], (m["mer"] or {}).get("current", {})
    k = st.columns(3)
    k[0].metric("Vent", f"{nb(cur['wind_speed_10m'])} km/h")
    k[1].metric("Rafales", f"{nb(cur['wind_gusts_10m'])} km/h")
    k[2].metric("Vagues", f"{nb(cm.get('wave_height') or 0, 1)} m")
    h = m["vent"]["hourly"]
    df = pd.DataFrame({"heure": pd.to_datetime(h["time"]), "Vent": h["wind_speed_10m"], "Rafales": h["wind_gusts_10m"]})
    df = df.melt("heure", var_name="mesure", value_name="km/h")
    seuils = pd.DataFrame({"y": [direct.VIGILANCE_KMH, direct.ARRET_GRUES_KMH], "seuil": ["vigilance", "arrêt des grues"]})
    st.altair_chart((alt.Chart(df).mark_line().encode(x=alt.X("heure:T", title=None), y=alt.Y("km/h:Q"),
                                                      color=alt.Color("mesure:N", title=None))
                     + alt.Chart(seuils).mark_rule(strokeDash=[4, 4]).encode(
                         y="y:Q", color=alt.Color("seuil:N", scale=alt.Scale(range=["#e03131", "#e8590c"]), title="seuil")))
                    .properties(height=260, title="Vent et rafales, 72 h (heure locale)"), width="stretch")
    if (m["mer"] or {}).get("hourly"):
        vg = pd.DataFrame({"heure": pd.to_datetime(m["mer"]["hourly"]["time"]), "vagues": m["mer"]["hourly"]["wave_height"]})
        st.altair_chart(alt.Chart(vg).mark_area(opacity=0.5, color="#1098ad").encode(
            x=alt.X("heure:T", title=None), y=alt.Y("vagues:Q", title="m")).properties(height=160, title="Hauteur des vagues"),
            width="stretch")
    g = direct.fenetre_grues(m)
    texte = (f"🔴 {g['heures_arret']} h d'arrêt probable des grues" if g["heures_arret"] else
             f"🟠 {g['heures_vigilance']} h en vigilance" if g["heures_vigilance"] else "🟢 Pas de contrainte de vent")
    st.markdown(f"**{texte} sur 48 h** — rafales max {nb(g['rafales_max'])} km/h, vagues max {nb(g['vagues_max'], 1)} m. "
                f"Relevé : {m['releve']}.")
