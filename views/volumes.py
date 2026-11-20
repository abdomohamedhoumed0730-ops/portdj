import altair as alt
import pandas as pd
import streamlit as st

from lib.donnees import mois_fr, nb, serie, volumes
from lib.modeles import anomalies, prevoir, tester

st.title("📦 Volumes de Los Angeles et Long Beach")
port = st.segmented_control("Port", ["Long Beach", "Los Angeles"], default="Long Beach")
v = volumes()
d = v[v.port == port]

# 1) composition annuelle
an = d.assign(annee=d.mois.dt.year).groupby("annee")[["imports_pleins", "exports_pleins", "vides_export"]].sum()
an = an.rename(columns={"imports_pleins": "Importations (pleins)", "exports_pleins": "Exportations (pleins)",
                        "vides_export": "Vides à l'export"}).reset_index().melt("annee", var_name="flux", value_name="EVP")
dernier_mois = d.mois.max()
st.altair_chart(alt.Chart(an).mark_bar().encode(
    x=alt.X("annee:O", title=f"année ({dernier_mois.year} : jusqu'à {mois_fr(dernier_mois)})"),
    y=alt.Y("EVP:Q", title="EVP par an"),
    color=alt.Color("flux:N", scale=alt.Scale(range=["#1971c2", "#2f9e44", "#adb5bd"]), title=None),
    tooltip=["annee", "flux", alt.Tooltip("EVP:Q", format=",.0f")]).properties(height=280,
    title=f"{port} : composition des flux par an"), width="stretch")

# 2) série mensuelle, prévision à 3 mois et mois atypiques
y = serie(port).dropna()
prev = prevoir(y, 3)
test = tester(y, 12)
atyp = anomalies(y)
atyp = atyp[atyp.atypique].reset_index().rename(columns={"index": "mois"})
base = pd.DataFrame({"mois": y.index, "EVP": y.values})
reel = alt.Chart(base).mark_line(color="#495057").encode(x=alt.X("mois:T", title=None), y=alt.Y("EVP:Q", title="EVP par mois (total comparable)"))
b95 = alt.Chart(prev).mark_area(opacity=0.2, color="#1971c2").encode(x="mois:T", y="bas95:Q", y2="haut95:Q")
b80 = alt.Chart(prev).mark_area(opacity=0.35, color="#1971c2").encode(x="mois:T", y="bas80:Q", y2="haut80:Q")
ligne = alt.Chart(prev).mark_line(color="#1971c2", strokeDash=[5, 3], point=True).encode(
    x="mois:T", y="prevision:Q", tooltip=[alt.Tooltip("mois:T", format="%m/%Y"), alt.Tooltip("prevision:Q", format=",.0f"),
                                         alt.Tooltip("bas80:Q", format=",.0f"), alt.Tooltip("haut80:Q", format=",.0f")])
points = alt.Chart(atyp).mark_point(color="#e03131", size=120, shape="diamond", filled=True).encode(
    x="mois:T", y="valeur:Q", tooltip=[alt.Tooltip("mois:T", format="%m/%Y"), alt.Tooltip("var_an:Q", format="+.0%"),
                                       alt.Tooltip("var_mois:Q", format="+.0%")])
st.altair_chart((b95 + b80 + reel + ligne + points).properties(
    height=360, title=f"{port} : volumes mensuels, prévision à 3 mois (marges 80 et 95 %) et mois atypiques (◆)"),
    width="stretch")
st.caption(f"Prévision : décomposition STL + ARIMA(1,1,0) sur le logarithme. Test sur {mois_fr(test['debut'])} – "
           f"{mois_fr(test['fin'])} : erreur moyenne {nb(test['erreur_modele'], 1)} %, contre "
           f"{nb(test['erreur_naive'], 1)} % pour « même mois l'an dernier » ; {test['dans_marge80']} mois sur "
           f"{test['h']} dans la marge à 80 %.")
c1, c2 = st.columns(2)
with c1:
    st.markdown("**Prévision**")
    st.dataframe(prev.assign(mois=prev.mois.map(mois_fr)).set_index("mois").round(0), width="stretch")
with c2:
    st.markdown("**Mois atypiques** (forêt d'isolement, 5 % des mois)")
    st.dataframe(atyp.assign(mois=atyp.mois.map(mois_fr), **{"variation sur un an": (atyp.var_an * 100).round(0),
                                                              "variation sur un mois": (atyp.var_mois * 100).round(0)})
                 [["mois", "variation sur un an", "variation sur un mois"]], hide_index=True, width="stretch")

# 3) les deux ports côte à côte
st.altair_chart(alt.Chart(v).mark_line().encode(
    x=alt.X("mois:T", title=None), y=alt.Y("total:Q", title="EVP par mois"),
    color=alt.Color("port:N", scale=alt.Scale(domain=["Los Angeles", "Long Beach"], range=["#1971c2", "#e8590c"]), title=None)
).properties(height=260, title="Los Angeles et Long Beach (total comparable)"), width="stretch")
st.caption("Long Beach : chiffres du BTS (polb.com est inaccessible depuis Djibouti), jusqu'à septembre 2026, "
           "sans les vides à l'import ; juillet 2020 corrigé d'après le communiqué du port.")
