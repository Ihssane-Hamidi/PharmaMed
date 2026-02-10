#!/usr/bin/env python
# coding: utf-8

# In[27]:


import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="DEFIS Pharma", layout="wide")

# =========================
# Fonction de chargement depuis Google Drive
# =========================
@st.cache_data
def load_csv_from_drive(file_id, sep="\t"):
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    # Essaie utf-8 d'abord
    try:
        df = pd.read_csv(url, sep=sep, engine="python", encoding="utf-8")
    except UnicodeDecodeError:
        # Si utf-8 échoue, essaye latin1
        df = pd.read_csv(url, sep=sep, engine="python", encoding="latin1")
    return df

# =========================
# IDs Google Drive
# =========================
ID_COMPACT = "1y-vVibmmuKyBcMcSX6UopgP5YuVos-Xn"
ID_BIG10 = "1TDzeC3Ug3JSN9wI1ENlGks4dwWL64jMU"

# =========================
# Chargement des données
# =========================
df = load_csv_from_drive(ID_COMPACT)
df1 = load_csv_from_drive(ID_BIG10)

# =========================
# Mapping laboratoires
# =========================
mapping_labo = {
    " ABBVIE": "ABBVIE",
    " ABBVIE DEUTSCHLAND (ALLEMAGNE)": "ABBVIE",
    " ASTRAZENECA": "ASTRAZENECA",
    " ASTRAZENECA AB": "ASTRAZENECA",
    " BAYER AG (ALLEMAGNE)": "BAYER",
    " BAYER HEALTHCARE": "BAYER",
    " BAYER PHARMA (ALLEMAGNE)": "BAYER",
    " BRISTOL MYERS SQUIBB": "BRISTOL MYERS SQUIBB",
    " BRISTOL MYERS SQUIBB PHARMA (GRANDE BRETAGNE)": "BRISTOL MYERS SQUIBB",
    " JOHNSON & JOHNSON SANTE BEAUTE FRANCE": "JOHNSON & JOHNSON",
    " NOVARTIS EUROPHARM (IRLANDE)": "NOVARTIS",
    " NOVARTIS EUROPHARM (ROYAUME-UNI)": "NOVARTIS",
    " NOVARTIS GENE THERAPIES EU (IRLANDE)": "NOVARTIS",
    " NOVARTIS PHARMA": "NOVARTIS",
    " NOVO NORDISK": "NOVO NORDISK",
    " NOVO NORDISK (DANEMARK)": "NOVO NORDISK",
    " PFIZER (GRANDE BRETAGNE)": "PFIZER",
    " PFIZER EUROPE MA EEIG (BELGIQUE)": "PFIZER",
    " PFIZER EUROPE MA EEIG (BELGIQUE);PFIZER (GRANDE BRETAGNE)": "PFIZER",
    " PFIZER EUROPE MA EEIG (ROYAUME UNI)": "PFIZER",
    " PFIZER HOLDING FRANCE": "PFIZER",
    " PFIZER IRELAND PHARMACEUTICALS (IRLANDE)": "PFIZER",
    " PFIZER PFE FRANCE": "PFIZER",
    " ROCHE": "ROCHE",
    " ROCHE REGISTRATION": "ROCHE",
    " ROCHE REGISTRATION (ALLEMAGNE)": "ROCHE"
}

df["Titulaire(s)"] = df["Titulaire(s)"].replace(mapping_labo)

# =========================
# Nettoyage
# =========================
df = df.drop_duplicates(subset=['Code CIS','CIP13'], keep="first")

# =========================
# Exemple Streamlit
# =========================


df1.columns
df.shape


# In[28]:


# =========================
# PAGE 1 : Recherche par médicament
# =========================
st.title(" Recherche par médicament")

option = st.radio(
    "Choisir le type de recherche :",
    ["Code CIS", "CIP13", "Dénomination"]
)

if option == "Code CIS":
    values = sorted(df["Code CIS"].dropna().unique())
elif option == "CIP13":
    values = sorted(df["CIP13"].dropna().unique())
else:
    values = sorted(df["Dénomination du médicament"].dropna().unique())

search_value = st.selectbox("Choisir un médicament :", values)

# Filtrer le df
if option == "Code CIS":
    med_df = df[df["Code CIS"] == search_value]
elif option == "CIP13":
    med_df = df[df["CIP13"] == search_value]
else:
    med_df = df[df["Dénomination du médicament"] == search_value]

st.subheader("Informations du médicament")
st.dataframe(med_df, use_container_width=True)

# =========================
# PAGE 2 : Analyse laboratoire (SMR + ASMR)
# =========================
st.title("Analyse laboratoire")

labs = sorted(df["Titulaire(s)"].dropna().unique())
lab_name = st.selectbox("Choisir un laboratoire :", labs)

lab_df = df[df["Titulaire(s)"] == lab_name]

st.subheader("Médicaments du laboratoire")
st.dataframe(lab_df, use_container_width=True)

def plot_pie_dynamic(df_lab, col_valeur, col_libelle, title):
    """
    Camembert propre :
    - valeurs officielles uniquement
    - None / NaN regroupés sous **
    - renvoi en note vers le libellé SMR / ASMR
    """

    df_copy = df_lab.copy()

    # Colonne utilisée pour le camembert
    df_copy["pie_label"] = df_copy[col_valeur]

    # Masque des valeurs manquantes (None / NaN)
    missing_mask = df_copy["pie_label"].isna()

    # Les valeurs manquantes deviennent **
    df_copy.loc[missing_mask, "pie_label"] = "**"

    # =====================
    # CAMEMBERT
    # =====================
    pie_counts = (
        df_copy["pie_label"]
        .value_counts()
        .reset_index()
    )
    pie_counts.columns = ["Valeur", "count"]

    # Mettre "**" à la fin
    pie_counts = pie_counts.sort_values(
        "Valeur", key=lambda x: x.replace("**", "zzz")
    )

    fig = px.pie(
        pie_counts,
        names="Valeur",
        values="count",
        title=title
    )
    st.plotly_chart(fig, use_container_width=True)

    # =====================
    # NOTE POUR **
    # =====================
    if missing_mask.any():
        pct_missing = missing_mask.mean() * 100

        st.markdown(
            f"⭐ **Note (**)** : {pct_missing:.1f}% des médicaments "
            f"n'ont pas de valeur {col_valeur} renseignée."
        )

        for _, row in df_copy[missing_mask].iterrows():
            st.write(
                f"- **{row['Dénomination du médicament']}** : {row[col_libelle]}"
            )



# SMR
st.subheader("📊 Répartition SMR")
plot_pie_dynamic(lab_df, "Valeur du SMR", "Libellé du SMR", "Répartition SMR")

# ASMR
st.subheader("📊 Répartition ASMR")
plot_pie_dynamic(lab_df, "Valeur de l’ASMR", "Libellé de l’ASMR", "Répartition ASMR")


# =========================
# PAGE 3 : Analyse du CA
# =========================
st.title(" Analyse du chiffre d’affaires")

labs_ca = sorted(df1["Titulaire(s)"].dropna().unique())
lab_name_ca = st.selectbox("Choisir un laboratoire pour la ventilation du CA :", labs_ca)

lab_ca_df = df1[df1["Titulaire(s)"] == lab_name_ca]

# CA_groupe pour limiter l'axe Y
ca_groupe_max = lab_ca_df["CA_groupe"].max()

# Histogramme CA par médicament
fig_ca = px.bar(
    lab_ca_df,
    x="Dénomination du médicament",
    y="Revenue_USD",
    title="Ventilation du chiffre d'affaires par médicament",
    labels={"Revenue_USD": "Chiffre d'affaires (USD)"}
)
fig_ca.update_yaxes(range=[0, ca_groupe_max], tickformat=",.0f")
st.plotly_chart(fig_ca, use_container_width=True)

# Camembert poids des médicaments dans le portefeuille
st.subheader("📊 Poids des médicaments dans le portefeuille")
fig_portfolio = px.pie(
    lab_ca_df,
    names="Dénomination du médicament",
    values="Revenue_USD",
    title="Répartition du chiffre d'affaires par médicament"
)
st.plotly_chart(fig_portfolio, use_container_width=True)

# Optionnel : afficher tableau SMR/ASMR pour ces médicaments
st.subheader("📋 Détails SMR et ASMR pour les médicaments du portefeuille")
st.dataframe(
    lab_ca_df[["Dénomination du médicament", "Valeur du SMR", "Libellé du SMR", "Valeur de l’ASMR", "Libellé de l’ASMR"]],
    use_container_width=True
)


# In[ ]:





# In[29]:


import streamlit as st
import pandas as pd
import plotly.express as px

# Colonnes SMR / ASMR
SMR_COL = "Valeur du SMR"
ASMR_COL = "Valeur de l’ASMR"

# =========================
# FONCTIONS
# =========================

def compute_lab_profile(df, lab, col):
    """
    Retourne la répartition normalisée (pourcentage) des valeurs SMR ou ASMR
    pour un laboratoire donné.
    """
    lab_df = df[df["Titulaire(s)"] == lab]

    if lab_df.empty:
        return {}

    counts = lab_df[col].value_counts(normalize=True)
    return counts.to_dict()


def compute_portfolio_profile(df, portfolio_df, col):
    """
    Calcule la répartition SMR/ASMR pondérée par labo dans le portefeuille.
    """
    if portfolio_df is None or portfolio_df.empty:
        return pd.Series(dtype=float)

    profile_total = {}

    for _, row in portfolio_df.iterrows():
        lab = row["Laboratoire"]
        weight = row["Poids"]

        lab_profile = compute_lab_profile(df, lab, col)

        for k, v in lab_profile.items():
            profile_total[k] = profile_total.get(k, 0) + weight * v

    return pd.Series(profile_total).sort_index()


def build_portfolio(df):
    """
    Interface utilisateur pour sélectionner les laboratoires et leurs pondérations.
    """
    labs = sorted(df["Titulaire(s)"].dropna().unique())

    selected_labs = st.multiselect(
        "Choisissez les laboratoires du portefeuille",
        labs
    )

    if not selected_labs:
        return None

    portfolio = []
    total_weight = 0

    for lab in selected_labs:
        w = st.number_input(
            f"Pondération (%) – {lab}",
            min_value=0.0,
            max_value=100.0,
            step=1.0,
            key=f"w_{lab}"
        )
        portfolio.append({"Laboratoire": lab, "Poids": w / 100})
        total_weight += w

    if abs(total_weight - 100) > 1e-6:
        st.warning(f"⚠️ Somme des pondérations = {total_weight:.1f}% (doit être 100%)")
        return None

    portfolio_df = pd.DataFrame(portfolio)
    return portfolio_df

# =========================
# INTERFACE STREAMLIT
# =========================

st.title(" Qualité Portefeuille Laboratoires – Profil SMR / ASMR")

# Construire le portefeuille
portfolio_df = build_portfolio(df)

if portfolio_df is None:
    st.stop()

# Calculer le profil pondéré SMR / ASMR
smr_profile = compute_portfolio_profile(df, portfolio_df, SMR_COL)
asmr_profile = compute_portfolio_profile(df, portfolio_df, ASMR_COL)

# Afficher les pie charts
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 Répartition SMR du portefeuille")
    if not smr_profile.empty:
        fig_smr = px.pie(
            values=smr_profile.values,
            names=smr_profile.index,
            title="Répartition SMR pondérée"
        )
        st.plotly_chart(fig_smr, use_container_width=True)
    else:
        st.info("Aucune donnée SMR disponible pour le portefeuille.")

with col2:
    st.subheader("📊 Répartition ASMR du portefeuille")
    if not asmr_profile.empty:
        fig_asmr = px.pie(
            values=asmr_profile.values,
            names=asmr_profile.index,
            title="Répartition ASMR pondérée"
        )
        st.plotly_chart(fig_asmr, use_container_width=True)
    else:
        st.info("Aucune donnée ASMR disponible pour le portefeuille.")


# In[ ]:




