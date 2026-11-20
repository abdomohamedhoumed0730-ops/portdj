import altair as alt
import pandas as pd
import streamlit as st

from lib.donnees import cnuced, cppi

st.title("🌍 Long Beach face aux autres ports")
st.info("Deux sources qui ne mesurent pas la même chose, montrées séparément : le **CPPI** est un **score par port** "
        "(0 = port médian ; plus il est haut, plus les porte-conteneurs repartent vite) ; la **CNUCED** donne des "
        "**chiffres par pays** (escales, temps médian au port en jours).")

st.subheader("CPPI – Banque mondiale & S&P Global")
c = cppi().reset_index()
pente = c.melt(id_vars="port", value_vars=["cppi2024", "cppi2025"], var_name="edition", value_name="score")
pente["edition"] = pente.edition.str[-4:]
couleurs = alt.Scale(domain=list(c.port), range=["#1971c2", "#e8590c", "#2f9e44", "#7048e8", "#c2255c", "#868e96"])
lignes = alt.Chart(pente).mark_line(point=alt.OverlayMarkDef(size=80)).encode(
    x=alt.X("edition:O", title="édition", axis=alt.Axis(labelAngle=0)), y=alt.Y("score:Q", title="score CPPI"),
    color=alt.Color("port:N", scale=couleurs, title=None), tooltip=["port", "edition", alt.Tooltip("score:Q", format=".1f")])
etiquettes = alt.Chart(pente[pente.edition == "2025"]).mark_text(align="left", dx=8).encode(
    x="edition:O", y="score:Q", text="port:N", color=alt.Color("port:N", scale=couleurs, legend=None))
zero = alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(strokeDash=[4, 4], color="#868e96").encode(y="y:Q")
g, d = st.columns([3, 2])
with g:
    st.altair_chart((lignes + etiquettes + zero).properties(height=380, title="De l'édition 2024 à l'édition 2025"),
                    width="stretch")
with d:
    t = c[["port", "cppi2024", "rang2024", "cppi2025", "rang2025"]].sort_values("rang2025")
    t.columns = ["port", "score 2024", "rang 2024 (sur 403)", "score 2025", "rang 2025 (sur 400)"]
    st.dataframe(t.round(1), hide_index=True, width="stretch")
    st.caption("Vancouver et Prince Rupert : concurrents canadiens de la côte Pacifique. Busan : grand hub "
               f"transpacifique. Djibouti : {int(c.loc[c.port == 'Djibouti', 'rang2025'].iloc[0])}e en 2025 "
               f"contre {int(c.loc[c.port == 'Djibouti', 'rang2024'].iloc[0])}e en 2024.")
serie = c.melt(id_vars="port", value_vars=[f"cppi{a}" for a in range(2020, 2026)], var_name="annee", value_name="score")
serie["annee"] = serie.annee.str[-4:].astype(int)
st.altair_chart(alt.Chart(serie).mark_line(point=True).encode(
    x=alt.X("annee:O", title=None), y=alt.Y("score:Q", title="score"), color=alt.Color("port:N", scale=couleurs, title=None)
).properties(height=260, title="Série des scores 2020-2025 (annexe de l'édition 2025)"), width="stretch")

st.subheader("CNUCED – temps au port et escales, par pays")
marche = st.segmented_control("Navires", ["Tous navires", "Porte-conteneurs"], default="Tous navires")
u = cnuced()
u = u[u.marche == marche]
dern = u[u.annee == u.annee.max()]
g, d = st.columns(2)
with g:
    st.altair_chart(alt.Chart(dern).mark_bar().encode(
        x=alt.X("temps_median_j:Q", title="temps médian au port (jours)"), y=alt.Y("pays:N", sort="-x", title=None),
        color=alt.condition(alt.datum.pays == "États-Unis", alt.value("#e8590c"), alt.value("#1971c2")),
        tooltip=["pays", alt.Tooltip("temps_median_j:Q", format=".2f"), alt.Tooltip("escales:Q", format=",")]
    ).properties(height=260, title=f"{marche}, {int(u.annee.max())}"), width="stretch")
with d:
    st.altair_chart(alt.Chart(u).mark_line(point=True).encode(
        x=alt.X("annee:O", title=None), y=alt.Y("escales:Q", title="nombre d'escales"), color=alt.Color("pays:N", title=None)
    ).transform_filter(alt.datum.pays != "Monde").properties(height=260, title="Nombre d'escales (hors Monde)"),
        width="stretch")
st.warning("La base CNUCED en accès libre ne couvre que 22 économies et le Monde (mise à jour du 26/03/2024, "
           "années 2018-2023) : **Djibouti n'y figure pas**. Pour Djibouti, voir le CPPI ci-dessus.")
