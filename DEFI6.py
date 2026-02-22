#!/usr/bin/env python
# coding: utf-8

# In[12]:


import streamlit as st
import pandas as pd
import plotly.express as px
import io
import re
from datetime import datetime
import unicodedata

# =========================
# CONFIG PAGE
# =========================
st.set_page_config(
    page_title="DEFIS Pharma",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# CSS CUSTOM
# =========================
st.markdown("""
<style>
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f2744 0%, #1a3a5c 100%);
    }
    [data-testid="stSidebar"] * { color: #e8f0fe !important; }

    .kpi-card {
        background: white;
        border-radius: 12px;
        padding: 20px;
        border-left: 5px solid #1a3a5c;
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        margin-bottom: 10px;
    }
    .kpi-label { color: #6b7280; font-size: 13px; font-weight: 600; text-transform: uppercase; }
    .kpi-value { color: #0f2744; font-size: 32px; font-weight: 700; margin-top: 4px; }
    .kpi-delta-pos { color: #16a34a; font-size: 13px; }
    .kpi-delta-neg { color: #dc2626; font-size: 13px; }

    .section-header {
        color: #0f2744; font-size: 18px; font-weight: 700;
        padding: 10px 0 6px 0; border-bottom: 2px solid #e5e7eb; margin-bottom: 20px;
    }
    .page-title { font-size: 28px; font-weight: 800; color: #0f2744; margin-bottom: 4px; }
    .page-subtitle { color: #6b7280; font-size: 14px; margin-bottom: 24px; }
    hr.thin { border: none; border-top: 1px solid #e5e7eb; margin: 20px 0; }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# =========================
# NORMALISATION COLONNES
# =========================
def normalize_columns(df):
    def clean(col):
        for char in ['\u2019', '\u2018', '\u02bc', '\u0060', '\u00b4']:
            col = col.replace(char, "'")
        col = col.replace('\u00a0', ' ').replace('\u2013', '-').replace('\u2014', '-')
        col = unicodedata.normalize('NFKC', col)
        return col.strip()
    df.columns = [clean(c) for c in df.columns]
    return df

# =========================
# CHARGEMENT DONNÉES
# =========================
@st.cache_data(show_spinner="Chargement des données...")
def load_csv_from_drive(file_id, sep="\t"):
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    for encoding in ["utf-8", "utf-8-sig", "latin-1"]:
        try:
            df = pd.read_csv(url, sep=sep, engine="python", encoding=encoding)
            " ".join(df.columns).encode("utf-8")
            return normalize_columns(df)
        except (UnicodeDecodeError, UnicodeEncodeError):
            continue
    df = pd.read_csv(url, sep=sep, engine="python", encoding="utf-8", errors="replace")
    return normalize_columns(df)

ID_COMPACT   = "1y-vVibmmuKyBcMcSX6UopgP5YuVos-Xn"
ID_BIG10     = "1TDzeC3Ug3JSN9wI1ENlGks4dwWL64jMU"
ID_DISPO     = "1EUDSX1PJowZPQ949dzbyKLX_BTBZBe3q"
ID_MED_DISPO = "1soEmF7Duey5LT_pfSGwkqZTzqaj7uj0N"

df  = load_csv_from_drive(ID_COMPACT)
df1 = load_csv_from_drive(ID_BIG10)
df2 = load_csv_from_drive(ID_DISPO)
df3 = load_csv_from_drive(ID_MED_DISPO)

# =========================
# MAPPING & NETTOYAGE
# =========================
mapping_labo = {
    " ABBVIE": "ABBVIE", " ABBVIE DEUTSCHLAND (ALLEMAGNE)": "ABBVIE",
    " ASTRAZENECA": "ASTRAZENECA", " ASTRAZENECA AB": "ASTRAZENECA",
    " BAYER AG (ALLEMAGNE)": "BAYER", " BAYER HEALTHCARE": "BAYER",
    " BAYER PHARMA (ALLEMAGNE)": "BAYER",
    " BRISTOL MYERS SQUIBB": "BRISTOL MYERS SQUIBB",
    " BRISTOL MYERS SQUIBB PHARMA (GRANDE BRETAGNE)": "BRISTOL MYERS SQUIBB",
    " JOHNSON & JOHNSON SANTE BEAUTE FRANCE": "JOHNSON & JOHNSON",
    " NOVARTIS EUROPHARM (IRLANDE)": "NOVARTIS",
    " NOVARTIS EUROPHARM (ROYAUME-UNI)": "NOVARTIS",
    " NOVARTIS GENE THERAPIES EU (IRLANDE)": "NOVARTIS",
    " NOVARTIS PHARMA": "NOVARTIS",
    " NOVO NORDISK": "NOVO NORDISK", " NOVO NORDISK (DANEMARK)": "NOVO NORDISK",
    " PFIZER (GRANDE BRETAGNE)": "PFIZER", " PFIZER EUROPE MA EEIG (BELGIQUE)": "PFIZER",
    " PFIZER EUROPE MA EEIG (BELGIQUE);PFIZER (GRANDE BRETAGNE)": "PFIZER",
    " PFIZER EUROPE MA EEIG (ROYAUME UNI)": "PFIZER",
    " PFIZER HOLDING FRANCE": "PFIZER",
    " PFIZER IRELAND PHARMACEUTICALS (IRLANDE)": "PFIZER",
    " PFIZER PFE FRANCE": "PFIZER",
    " ROCHE": "ROCHE", " ROCHE REGISTRATION": "ROCHE",
    " ROCHE REGISTRATION (ALLEMAGNE)": "ROCHE",
}
df["Titulaire(s)"] = df["Titulaire(s)"].replace(mapping_labo)
df = df.drop_duplicates(subset=["Code CIS", "CIP13"], keep="first")

SMR_COL  = "Valeur du SMR"
ASMR_COL = "Valeur de l'ASMR"

# =========================
# MAPPINGS LABELS & COULEURS
# ── fort score = bleu foncé → faible score = rouge
# =========================

# ASMR : I (majeur) → V (absence) + non applicable
ASMR_LABELS = {
    "I"                      : "I – Progrès majeur",
    "II"                     : "II – Amélioration importante",
    "III"                    : "III – Amélioration modérée",
    "IV"                     : "IV – Amélioration mineure",
    "V"                      : "V – Absence d'amélioration",
    "V.absence amélioration" : "V – Absence d'amélioration",
    "NA"                     : "Non applicable",
}
ASMR_COLORS = {
    "I – Progrès majeur"           : "#1a3a5c",   # bleu très foncé
    "II – Amélioration importante" : "#2563eb",   # bleu
    "III – Amélioration modérée"   : "#60a5fa",   # bleu clair
    "IV – Amélioration mineure"    : "#f59e0b",   # orange
    "V – Absence d'amélioration"   : "#dc2626",   # rouge
    "Non applicable"               : "#d1d5db",   # gris
}

# ASR (dispositifs) : I → IV + non applicable
ASR_LABELS = {
    "I"   : "I – Amélioration substantielle",
    "II"  : "II – Amélioration modérée",
    "III" : "III – Amélioration faible",
    "IV"  : "IV – Absence d'amélioration",
    "NA"  : "Non applicable",
}
ASR_COLORS = {
    "I – Amélioration substantielle" : "#1a3a5c",
    "II – Amélioration modérée"      : "#2563eb",
    "III – Amélioration faible"      : "#f59e0b",
    "IV – Absence d'amélioration"    : "#dc2626",
    "Non applicable"                 : "#d1d5db",
}

# SMR (médicaments)
SMR_LABELS = {
    "Important"   : "SMR Important",
    "Modéré"      : "SMR Modéré",
    "Faible"      : "SMR Faible",
    "Insuffisant" : "SMR Insuffisant",
}
SMR_COLORS = {
    "SMR Important"   : "#1a3a5c",
    "SMR Modéré"      : "#2563eb",
    "SMR Faible"      : "#f59e0b",
    "SMR Insuffisant" : "#dc2626",
}

# SR (dispositifs)
SR_LABELS = {
    "Important"   : "SR Important",
    "Modéré"      : "SR Modéré",
    "Faible"      : "SR Faible",
    "Insuffisant" : "SR Insuffisant",
}
SR_COLORS = {
    "SR Important"   : "#1a3a5c",
    "SR Modéré"      : "#2563eb",
    "SR Faible"      : "#f59e0b",
    "SR Insuffisant" : "#dc2626",
}

# =========================
# HELPERS
# =========================
def clean_illegal_characters(dataframe):
    illegal = re.compile(r"[\x00-\x08\x0B-\x0C\x0E-\x1F]")
    df_c = dataframe.copy()
    for col in df_c.columns:
        if df_c[col].dtype == "object":
            df_c[col] = df_c[col].astype(str).apply(lambda x: illegal.sub("", x))
    return df_c

def export_excel(dataframe, sheet_name="Export"):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        clean_illegal_characters(dataframe).to_excel(writer, index=False, sheet_name=sheet_name)
    return output.getvalue()

def kpi_card(label, value, delta=None, delta_label="vs groupe 2"):
    delta_html = ""
    if delta is not None:
        sign = "+" if delta >= 0 else ""
        css  = "kpi-delta-pos" if delta >= 0 else "kpi-delta-neg"
        delta_html = f'<div class="{css}">{sign}{delta} {delta_label}</div>'
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        {delta_html}
    </div>""", unsafe_allow_html=True)

def section_header(title):
    st.markdown(f'<div class="section-header">{title}</div>', unsafe_allow_html=True)

def plot_pie(df_lab, col_valeur, title, label_map=None, color_map=None, height=380):
    """
    Camembert avec labels enrichis et couleurs sémantiques.
    - label_map : dict {valeur_csv → label_affiché}
    - color_map : dict {label_affiché → couleur_hex}
    - Dans le camembert : % uniquement
    - Dans la légende  : label complet (évite la confusion V vs V.absence)
    """
    df_c = df_lab.copy()
    df_c["pie_label"] = (
        df_c[col_valeur]
        .fillna("Non renseigné")
        .astype(str)
        .str.strip()
    )
    if label_map:
        df_c["pie_label"] = df_c["pie_label"].apply(lambda x: label_map.get(x, x))

    pie_counts = df_c["pie_label"].value_counts().reset_index()
    pie_counts.columns = ["Valeur", "count"]

    # Couleurs dans le bon ordre
    if color_map:
        colors = [color_map.get(v, "#9ca3af") for v in pie_counts["Valeur"]]
    else:
        colors = px.colors.qualitative.Set2[:len(pie_counts)]

    fig = px.pie(
        pie_counts,
        names="Valeur",
        values="count",
        title=title,
        color="Valeur",
        color_discrete_map=color_map if color_map else {},
        hole=0.35,
    )
    fig.update_layout(
        margin=dict(t=50, b=20, l=20, r=160),   # r=160 → place pour légende verticale
        height=height,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            x=1.02,
            font=dict(size=11),
        )
    )
    # % dans le camembert, label complet dans la légende
    fig.update_traces(textposition="inside", textinfo="percent")
    st.plotly_chart(fig, use_container_width=True)

def compute_kpi(dataframe):
    total  = len(dataframe)
    nb_med = int((dataframe["type_produit"] == "medicament").sum()) if "type_produit" in dataframe.columns else 0
    nb_dm  = int((dataframe["type_produit"] == "dispositif_medical").sum()) if "type_produit" in dataframe.columns else 0
    asmr_col = next((c for c in dataframe.columns if "asmr" in c.lower()), None)
    taux = dataframe[asmr_col].isin(["I", "II"]).mean() * 100 if asmr_col else 0.0
    return total, nb_med, nb_dm, taux

def compute_group_profile(dataframe, group, col):
    gdf = dataframe[dataframe["groupe_racine"] == group]
    return gdf[col].value_counts(normalize=True).to_dict() if not gdf.empty else {}

def compute_portfolio_profile(dataframe, portfolio_df, col):
    total = {}
    for _, row in portfolio_df.iterrows():
        for k, v in compute_group_profile(dataframe, row["Groupe"], col).items():
            total[k] = total.get(k, 0) + row["Poids normalisé"] * v
    return pd.Series(total).sort_index()

# =========================
# SIDEBAR
# =========================
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding:16px 0 24px 0;">
        <div style="font-size:36px">💊</div>
        <div style="font-size:20px; font-weight:800; color:#e8f0fe; letter-spacing:1px;">DEFIS Pharma</div>
        <div style="font-size:11px; color:#94a3b8; margin-top:4px;">Analyse & Intelligence Marché</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("<div style='font-size:11px; font-weight:700; letter-spacing:1.5px; color:#94a3b8; padding-bottom:8px;'>NAVIGATION</div>", unsafe_allow_html=True)
    page = st.radio("", [
        "🔎  Recherche Produit",
        "🏢  Analyse Laboratoire",
        "💰  Chiffre d'Affaires",
        "📁  Portefeuille",
    ], label_visibility="collapsed")
    st.markdown("---")
    st.markdown(f"<div style='font-size:11px; color:#64748b; text-align:center;'>Données au<br><strong style='color:#94a3b8;'>{datetime.now().strftime('%d %b %Y')}</strong></div>", unsafe_allow_html=True)


# ============================================================
# PAGE 1 — RECHERCHE PRODUIT
# ============================================================
if page == "🔎  Recherche Produit":
    st.markdown('<div class="page-title">🔎 Recherche Produit</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Retrouvez les informations d\'un médicament ou d\'un dispositif médical</div>', unsafe_allow_html=True)

    tab_med, tab_dm = st.tabs(["💊 Médicament", "🩺 Dispositif Médical"])

    with tab_med:
        col_opts, col_search = st.columns([1, 2], gap="large")
        with col_opts:
            section_header("Critère de recherche")
            option = st.radio("Rechercher par :", ["Dénomination", "Code CIS", "CIP13"], label_visibility="collapsed")
        with col_search:
            section_header("Sélection")
            if option == "Code CIS":
                values, col_filter = sorted(df["Code CIS"].dropna().unique()), "Code CIS"
            elif option == "CIP13":
                values, col_filter = sorted(df["CIP13"].dropna().unique()), "CIP13"
            else:
                values, col_filter = sorted(df["Dénomination du médicament"].dropna().unique()), "Dénomination du médicament"
            search_value = st.selectbox(f"Sélectionner ({len(values)} disponibles) :", values)

        med_df = df[df[col_filter] == search_value]
        st.markdown("<hr class='thin'>", unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        with c1:
            kpi_card("Présentations", len(med_df))
        with c2:
            smr_col_found = next((c for c in med_df.columns if "valeur" in c.lower() and "smr" in c.lower()), None)
            smr = med_df[smr_col_found].dropna().values[0] if smr_col_found and not med_df[smr_col_found].dropna().empty else "–"
            kpi_card("SMR", smr)
        with c3:
            asmr_col_found = next((c for c in med_df.columns if "valeur" in c.lower() and "asmr" in c.lower()), None)
            asmr = med_df[asmr_col_found].dropna().values[0] if asmr_col_found and not med_df[asmr_col_found].dropna().empty else "–"
            kpi_card("ASMR", asmr)

        st.markdown("<hr class='thin'>", unsafe_allow_html=True)
        section_header("Données détaillées")
        st.dataframe(med_df, use_container_width=True, height=320)
        col_dl, _ = st.columns([1, 3])
        with col_dl:
            st.download_button("📥 Exporter Excel", data=export_excel(med_df),
                file_name=f"medicament_{search_value}_{datetime.now().date()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True)

    with tab_dm:
        col_opts2, col_search2 = st.columns([1, 2], gap="large")
        with col_opts2:
            section_header("Critère de recherche")
            search_option = st.radio("Rechercher par :", ["Nom du dispositif", "Code dossier HAS"], label_visibility="collapsed")
        with col_search2:
            section_header("Sélection")
            if search_option == "Code dossier HAS":
                values_dm, col_dm = sorted(df2["Code dossier"].dropna().astype(str).unique()), "Code dossier"
            else:
                values_dm, col_dm = sorted(df2["Nom dispositif"].dropna().unique()), "Nom dispositif"
            search_dm = st.selectbox(f"Sélectionner ({len(values_dm)} disponibles) :", values_dm)

        dispo_df = df2[df2[col_dm].astype(str) == search_dm] if search_option == "Code dossier HAS" else df2[df2[col_dm] == search_dm]
        st.markdown("<hr class='thin'>", unsafe_allow_html=True)

        if dispo_df.empty:
            st.warning("⚠️ Aucun dispositif trouvé.")
        else:
            kpi_card("Résultats trouvés", len(dispo_df))
            st.markdown("<hr class='thin'>", unsafe_allow_html=True)
            section_header("Données détaillées")
            st.dataframe(dispo_df, use_container_width=True, height=320)
            col_dl2, _ = st.columns([1, 3])
            with col_dl2:
                st.download_button("📥 Exporter Excel", data=export_excel(dispo_df),
                    file_name=f"dispositif_{search_dm}_{datetime.now().date()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True)


# ============================================================
# PAGE 2 — ANALYSE LABORATOIRE
# ============================================================
elif page == "🏢  Analyse Laboratoire":
    st.markdown('<div class="page-title">🏢 Analyse Laboratoire</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Explorez le profil qualité d\'un groupe ou comparez deux groupes</div>', unsafe_allow_html=True)

    groups = sorted(df3["groupe_racine"].dropna().unique())

    with st.expander("⚙️ Configuration de l'analyse", expanded=True):
        col_g1, col_mode, col_g2 = st.columns([2, 1, 2], gap="large")
        with col_g1:
            st.markdown("**Groupe principal**")
            group_1 = st.selectbox("Groupe principal :", groups, label_visibility="collapsed")
        with col_mode:
            st.markdown("**Mode**")
            compare_mode = st.toggle("Comparer", value=False)
        with col_g2:
            st.markdown("**Groupe de comparaison**")
            if compare_mode:
                group_2 = st.selectbox("Comparer avec :", [g for g in groups if g != group_1], label_visibility="collapsed")
            else:
                st.selectbox("Comparer avec :", groups, disabled=True, label_visibility="collapsed")
                group_2 = None

    df_g1 = df3[df3["groupe_racine"] == group_1]
    df_g2 = df3[df3["groupe_racine"] == group_2] if compare_mode and group_2 else None

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    section_header("🔎 Filiales du groupe")

    groups_to_show = [group_1] + ([group_2] if compare_mode and group_2 else [])
    cols_exp = st.columns(len(groups_to_show), gap="large")
    for i, group in enumerate(groups_to_show):
        with cols_exp[i]:
            gdf = df3[df3["groupe_racine"] == group]
            with st.expander(f"**{group}** — {len(gdf)} produits"):
                for t in sorted(gdf["Titulaire(s)"].dropna().unique()):
                    st.markdown(f"- {t}")

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    section_header("📌 Indicateurs clés")

    total1, nb_med1, nb_dm1, taux1 = compute_kpi(df_g1)
    if not compare_mode:
        c1, c2, c3, c4 = st.columns(4)
        with c1: kpi_card("Total produits", total1)
        with c2: kpi_card("💊 Médicaments", nb_med1)
        with c3: kpi_card("🩺 Dispositifs", nb_dm1)
        with c4: kpi_card("% ASMR I-II", f"{taux1:.1f}%")
    else:
        total2, nb_med2, nb_dm2, taux2 = compute_kpi(df_g2)
        c1, c2, c3, c4 = st.columns(4)
        with c1: kpi_card("Total", f"{total1} vs {total2}", delta=total1-total2)
        with c2: kpi_card("💊 Médicaments", f"{nb_med1} vs {nb_med2}", delta=nb_med1-nb_med2)
        with c3: kpi_card("🩺 Dispositifs", f"{nb_dm1} vs {nb_dm2}", delta=nb_dm1-nb_dm2)
        with c4: kpi_card("% ASMR I-II", f"{taux1:.1f}% vs {taux2:.1f}%", delta=round(taux1-taux2, 1), delta_label="pts")

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    section_header("📊 Analyse qualitative")

    col_ind, _ = st.columns([2, 3])
    with col_ind:
        choix = st.radio("Indicateur :", ["SMR / SR", "ASMR / ASR"], horizontal=True, label_visibility="collapsed")

    col_valeur = SMR_COL if choix == "SMR / SR" else ASMR_COL
    lbl_m = "SMR" if choix == "SMR / SR" else "ASMR"
    lbl_d = "SR"  if choix == "SMR / SR" else "ASR"
    lmap_m = SMR_LABELS  if choix == "SMR / SR" else ASMR_LABELS
    lmap_d = SR_LABELS   if choix == "SMR / SR" else ASR_LABELS
    cmap_m = SMR_COLORS  if choix == "SMR / SR" else ASMR_COLORS
    cmap_d = SR_COLORS   if choix == "SMR / SR" else ASR_COLORS

    med_g1 = df_g1[df_g1["type_produit"] == "medicament"]
    dm_g1  = df_g1[df_g1["type_produit"] == "dispositif_medical"]

    if not compare_mode:
        col_left, col_right = st.columns(2, gap="large")
        with col_left:
            if not med_g1.empty:
                plot_pie(med_g1, col_valeur, f"{lbl_m} – Médicaments ({group_1})", label_map=lmap_m, color_map=cmap_m)
            else:
                st.info("Aucun médicament pour ce groupe.")
        with col_right:
            if not dm_g1.empty:
                plot_pie(dm_g1, col_valeur, f"{lbl_d} – Dispositifs ({group_1})", label_map=lmap_d, color_map=cmap_d)
            else:
                st.info("Aucun dispositif médical pour ce groupe.")
    else:
        med_g2 = df_g2[df_g2["type_produit"] == "medicament"]
        dm_g2  = df_g2[df_g2["type_produit"] == "dispositif_medical"]
        st.markdown(f"**Médicaments — {lbl_m}**")
        c1, c2 = st.columns(2, gap="large")
        with c1:
            if not med_g1.empty: plot_pie(med_g1, col_valeur, group_1, label_map=lmap_m, color_map=cmap_m)
        with c2:
            if not med_g2.empty: plot_pie(med_g2, col_valeur, group_2, label_map=lmap_m, color_map=cmap_m)
        st.markdown(f"**Dispositifs — {lbl_d}**")
        c3, c4 = st.columns(2, gap="large")
        with c3:
            if not dm_g1.empty: plot_pie(dm_g1, col_valeur, group_1, label_map=lmap_d, color_map=cmap_d)
        with c4:
            if not dm_g2.empty: plot_pie(dm_g2, col_valeur, group_2, label_map=lmap_d, color_map=cmap_d)

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    section_header("📥 Export")
    col_dl1, col_dl2, _ = st.columns([1, 1, 2])
    with col_dl1:
        st.download_button(f"📥 {group_1} (Excel)", data=export_excel(df_g1),
            file_name=f"export_{group_1}_{datetime.now().date()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True)
    if compare_mode and df_g2 is not None:
        with col_dl2:
            st.download_button(f"📥 {group_2} (Excel)", data=export_excel(df_g2),
                file_name=f"export_{group_2}_{datetime.now().date()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True)


# ============================================================
# PAGE 3 — CHIFFRE D'AFFAIRES
# ============================================================
elif page == "💰  Chiffre d'Affaires":
    st.markdown('<div class="page-title">💰 Chiffre d\'Affaires</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Ventilation du CA par médicament pour les laboratoires disponibles</div>', unsafe_allow_html=True)
    st.info("ℹ️ Les données financières couvrent actuellement 10 groupes. D'autres pourront être ajoutées ultérieurement.")

    col_sel, _ = st.columns([2, 3])
    with col_sel:
        lab_name_ca = st.selectbox("Choisir un laboratoire :", sorted(df1["Titulaire(s)"].dropna().unique()))

    lab_ca_df = df1[df1["Titulaire(s)"] == lab_name_ca]
    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    section_header("📌 Vue d'ensemble")

    total_ca = lab_ca_df["Revenue_USD"].sum()
    nb_meds  = lab_ca_df["Dénomination du médicament"].nunique()
    top_med  = lab_ca_df.loc[lab_ca_df["Revenue_USD"].idxmax(), "Dénomination du médicament"] if not lab_ca_df.empty else "–"

    c1, c2, c3 = st.columns(3)
    with c1: kpi_card("CA Total (USD)", f"${total_ca:,.0f}")
    with c2: kpi_card("Médicaments", nb_meds)
    with c3: kpi_card("🏆 Top médicament", top_med)

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)

    col_bar, col_pie = st.columns(2, gap="large")
    with col_bar:
        section_header("Ventilation par médicament")
        fig_ca = px.bar(
            lab_ca_df.sort_values("Revenue_USD", ascending=True),
            x="Revenue_USD", y="Dénomination du médicament", orientation="h",
            color="Revenue_USD", color_continuous_scale="Blues",
            labels={"Revenue_USD": "CA (USD)", "Dénomination du médicament": ""}
        )
        fig_ca.update_coloraxes(showscale=False)
        fig_ca.update_layout(margin=dict(l=10, r=20, t=10, b=20), height=420, xaxis_tickformat="$,.0f")
        st.plotly_chart(fig_ca, use_container_width=True)

    with col_pie:
        section_header("Poids dans le portefeuille")
        fig_p = px.pie(lab_ca_df, names="Dénomination du médicament", values="Revenue_USD",
                       color_discrete_sequence=px.colors.qualitative.Set2, hole=0.4)
        fig_p.update_traces(textposition="inside", textinfo="percent+label")
        fig_p.update_layout(margin=dict(l=10, r=10, t=10, b=60), height=420, showlegend=False)
        st.plotly_chart(fig_p, use_container_width=True)

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    section_header("📋 Profil SMR / ASMR du portefeuille")
    cols_show = [c for c in [
        "Dénomination du médicament", "Valeur du SMR", "Libellé du SMR",
        "Valeur de l'ASMR", "Libellé de l'ASMR"
    ] if c in lab_ca_df.columns]
    st.dataframe(lab_ca_df[cols_show], use_container_width=True, height=280)

    col_dl, _ = st.columns([1, 3])
    with col_dl:
        st.download_button("📥 Exporter Excel", data=export_excel(lab_ca_df),
            file_name=f"CA_{lab_name_ca}_{datetime.now().date()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True)


# ============================================================
# PAGE 4 — PORTEFEUILLE
# ============================================================
# ============================================================
# PAGE — PORTEFEUILLE  (v2 — normalisation ASMR/ASR correcte)
# ============================================================

# ============================================================
# PAGE — PORTEFEUILLE  (v2 — normalisation ASMR/ASR correcte)
# ============================================================

elif page == "📁  Portefeuille":

    import io
    import re
    import numpy as np
    import plotly.express as px

    st.markdown('<div class="page-title">📁 Construction de Portefeuille</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Importez un fichier Excel (Titulaire(s) | Pondérations) '
        'et analysez la qualité du portefeuille</div>',
        unsafe_allow_html=True,
    )

    # ══════════════════════════════════════════════════════════════════════════
    # 0.  CONSTANTES & FONCTIONS DE NORMALISATION
    # ══════════════════════════════════════════════════════════════════════════

    # ── SMR / SR ──────────────────────────────────────────────────────────────
    SMR_NORM = {
        "Important":   "Important",
        "Modéré":      "Modéré",
        "Suffisant":   "Suffisant",
        "Faible":      "Faible",
        "Insuffisant": "Insuffisant",
        "Commentaires":"Non chiffré",
        "Non précisé": "Non précisé",
    }
    SMR_ORDER = ["Important", "Suffisant", "Modéré", "Faible", "Insuffisant", "Non chiffré", "Non précisé"]
    SMR_COLORS = {
        "Important":   "#1a7f4b",
        "Suffisant":   "#52b788",
        "Modéré":      "#f4a835",
        "Faible":      "#e07b39",
        "Insuffisant": "#d94f3d",
        "Non chiffré": "#b0bec5",
        "Non précisé": "#cfd8dc",
    }
    # SR = même palette / ordre (commission différente mais même échelle)
    SR_ORDER  = SMR_ORDER
    SR_COLORS = SMR_COLORS

    # ── ASMR / ASR ────────────────────────────────────────────────────────────
    ROMAN_TO_LABEL = {
        "I":   "I — Majeure",
        "II":  "II — Importante",
        "III": "III — Modérée",
        "IV":  "IV — Mineure",
        "V":   "V — Absente",
    }
    ASMR_ORDER = ["I", "II", "III", "IV", "V", "Non chiffré", "Non précisé"]
    ASMR_COLORS = {
        "I":           "#1a237e",
        "II":          "#283593",
        "III":         "#3949ab",
        "IV":          "#7986cb",
        "V":           "#c5cae9",
        "Non chiffré": "#b0bec5",
        "Non précisé": "#cfd8dc",
    }
    ASR_ORDER  = ASMR_ORDER
    ASR_COLORS = ASMR_COLORS

    def normalize_smr(val):
        """Normalise Valeur du SMR vers un niveau canonique."""
        if pd.isna(val):
            return "Non précisé"
        return SMR_NORM.get(str(val).strip(), "Non précisé")

    def normalize_asmr_asr(val, type_produit):
        """
        Retourne (roman, label_qualitatif, source)
          roman  : 'I'..'V' | 'Non chiffré' | 'Non précisé'
          source : 'ASMR' | 'ASR' | 'Non précisé'
        Règles :
          1. Forme longue "III. Amélioration modérée" → ASR (format CNEDiMTS)
          2. Forme courte "III" → ASMR si medicament, ASR si dispositif_medical
          3. "Commentaires sans chiffrage…" → Non chiffré
          4. Tout le reste → Non précisé
        """
        if pd.isna(val) or str(val).strip() == "":
            return ("Non précisé", "Non précisé", "Non précisé")

        v = str(val).strip()

        # Cas 1 : forme longue (ASR CNEDiMTS)
        m = re.match(r'^(I{1,3}V?|VI{0,3}|IV|V)\.\s+', v)
        if m:
            roman = m.group(1)
            return (roman, ROMAN_TO_LABEL.get(roman, roman), "ASR")

        # Cas 2 : forme courte — chiffre romain seul
        if v in ROMAN_TO_LABEL:
            source = "ASMR" if str(type_produit) == "medicament" else "ASR"
            return (v, ROMAN_TO_LABEL[v], source)

        # Cas 3 : commentaire sans chiffrage
        if "commentaire" in v.lower():
            source = "ASMR" if str(type_produit) == "medicament" else "ASR"
            return ("Non chiffré", "Non chiffré", source)

        return ("Non précisé", "Non précisé", "Non précisé")

    # Pré-calcul sur df3 entier (une seule fois grâce au cache)
    @st.cache_data(show_spinner=False)
    def enrich_df(df):
        df = df.copy()
        df["_smr_norm"] = df["Valeur du SMR"].apply(normalize_smr)
        parsed = df.apply(
            lambda r: pd.Series(
                normalize_asmr_asr(r["Valeur de l'ASMR"], r["type_produit"]),
                index=["_roman", "_label_amr", "_source_amr"]
            ), axis=1
        )
        return pd.concat([df, parsed], axis=1)

    df3 = enrich_df(df3)

    # ══════════════════════════════════════════════════════════════════════════
    # 1.  IMPORT EXCEL
    # ══════════════════════════════════════════════════════════════════════════
    section_header("1️⃣ Import du fichier de pondérations")

    template_buf = io.BytesIO()
    with pd.ExcelWriter(template_buf, engine="openpyxl") as writer:
        pd.DataFrame({
            "Titulaire(s)": ["Exemple Pharma SA", "Autre Biotech"],
            "Pondérations":  [60.0, 40.0],
        }).to_excel(writer, index=False)
    template_buf.seek(0)

    st.caption(
        "Format attendu : deux colonnes — **Titulaire(s)** et **Pondérations** "
        "(valeurs > 0, pas forcément normalisées à 100)."
    )
    st.download_button(
        "📥 Télécharger le template Excel",
        data=template_buf,
        file_name="template_pondérations.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    uploaded_file = st.file_uploader(
        "Importer le fichier Excel complété",
        type=["xlsx", "xls"],
        label_visibility="visible",
    )

    if uploaded_file is None:
        st.info("📂 Importez votre fichier Excel pour continuer.")
        st.stop()

    try:
        import openpyxl as _openpyxl
        _wb = _openpyxl.load_workbook(uploaded_file, read_only=True, data_only=True)
        _ws = _wb.active
        _rows = list(_ws.iter_rows(values_only=True))
        _wb.close()
        if not _rows or len(_rows) < 2:
            st.error("❌ Le fichier est vide ou ne contient qu une ligne d en-tête.")
            st.stop()
        _headers = [str(c).strip() if c is not None else "" for c in _rows[0]]
        raw_import = pd.DataFrame(_rows[1:], columns=_headers)
    except Exception as e:
        st.error(f"❌ Impossible de lire le fichier : {e}")
        st.stop()

    if not {"Titulaire(s)", "Pondérations"}.issubset(set(raw_import.columns)):
        st.error(f"❌ Colonnes trouvées : `{raw_import.columns.tolist()}` — attendu : Titulaire(s) et Pondérations")
        st.stop()

    raw_import = raw_import[["Titulaire(s)", "Pondérations"]].dropna()
    raw_import.columns = ["label_import", "poids"]
    raw_import["poids"] = pd.to_numeric(raw_import["poids"], errors="coerce").fillna(0)
    raw_import = raw_import[raw_import["poids"] > 0].reset_index(drop=True)

    if raw_import.empty:
        st.error("❌ Aucune pondération > 0 trouvée dans le fichier.")
        st.stop()

    # ══════════════════════════════════════════════════════════════════════════
    # 2.  TABLEAU DE CORRESPONDANCE  filiale ↔ groupe_racine
    # ══════════════════════════════════════════════════════════════════════════
    section_header("2️⃣ Correspondance Titulaire ↔ Groupe racine")

    from difflib import SequenceMatcher

    # ── Référentiel complet filiale / groupe ──────────────────────────────────
    ref = (
        df3[["Titulaire(s)", "groupe_racine"]]
        .dropna(subset=["Titulaire(s)", "groupe_racine"])
        .drop_duplicates()
    )
    all_titulaires = sorted(ref["Titulaire(s)"].unique())
    all_groupes    = sorted(ref["groupe_racine"].unique())
    set_titulaires = set(all_titulaires)
    set_groupes    = set(all_groupes)
    # Juste après la construction de ref, ajoutez :
    test_grp = "PFIZER"  # remplacez par un groupe de votre fichier
    filiales_test = ref[ref["groupe_racine"] == test_grp]["Titulaire(s)"].unique().tolist()
    st.write(f"Filiales de {test_grp} :", filiales_test)

    # ── Stopwords pharma : tokens trop génériques pour le matching ────────────
    STOPWORDS = {
        "LABORATORIES", "LABORATORY", "LABS", "PHARMA", "PHARMACEUTICALS",
        "PHARMACEUTICAL", "HEALTHCARE", "HEALTH", "HOLDING", "HOLDINGS",
        "FRANCE", "EUROPE", "EUROPEAN", "INTERNATIONAL", "WORLDWIDE", "GLOBAL",
        "GROUP", "GROUPE", "GMBH", "SARL", "SAS", "SA", "AG", "BV", "NV",
        "LIMITED", "LTD", "INC", "CORP", "CORPORATION", "COMPANY", "CO",
        "NORTH", "SOUTH", "EAST", "WEST", "AMERICA", "AMERICAS", "ASIA",
        "PACIFIC", "US", "USA", "UK", "EU",
    }

    def sim(a, b):
        """Score SequenceMatcher entre deux chaînes (insensible à la casse)."""
        return SequenceMatcher(None, a.upper(), b.upper()).ratio()

    def meaningful_tokens(label, min_len=3):
        """
        Extrait les tokens significatifs d'un label :
        - longueur >= min_len
        - non présents dans STOPWORDS
        Ex: "Abbott Laboratories France" → ["ABBOTT"]
            "Roche Holding US"           → ["ROCHE"]
            "Bristol-Myers Squibb"       → ["BRISTOL", "MYERS", "SQUIBB"]
        """
        raw = re.split(r"[\s\-_/,\.]+", label.upper())
        return [t for t in raw if len(t) >= min_len and t not in STOPWORDS]

    def token_score(label, candidate):
        """
        Score de matching par tokens :
        - 1.0  si un token du label correspond EXACTEMENT à tout le candidate
        - 0.85 si un token du label est CONTENU dans le candidate (ou vice-versa)
        - 0.0  sinon
        Retourne le meilleur score trouvé parmi tous les tokens.
        """
        tokens = meaningful_tokens(label)
        cand_up = candidate.upper()
        cand_tokens = meaningful_tokens(candidate)
        best = 0.0
        for tok in tokens:
            if tok == cand_up:
                best = max(best, 1.0)       # token = candidate entier
            elif tok in cand_up:
                best = max(best, 0.85)      # token contenu dans candidate
            elif any(ct == tok for ct in cand_tokens):
                best = max(best, 0.85)      # token = un token du candidate
        return best

    def combined_score(label, candidate):
        """
        Score final = max(SequenceMatcher, token_score).
        Cela permet de capturer :
          - les variantes orthographiques (SequenceMatcher)
          - les noms longs avec suffixes (token_score)
        """
        return max(sim(label, candidate), token_score(label, candidate))

    SEUIL = 0.5   # seuil minimum pour le fuzzy (assez bas car token_score = 0.85 pour bons matchs)

    def find_candidates(label):
        """
        4 étapes ordonnées :
          1. Exact Titulaire(s)  → match_type = 'exact_tit'
          2. Exact groupe_racine → match_type = 'exact_grp'
          3. Fuzzy (combined_score >= SEUIL) sur groupe_racine → match_type = 'fuzzy'
          4. Aucun               → match_type = 'aucun'
        """
        # Étape 1 — exact titulaire
        if label in set_titulaires:
            grp_parents = ref[ref["Titulaire(s)"] == label]["groupe_racine"].unique().tolist()
            return dict(match_type="exact_tit",
                        tit_exact=label,
                        grp_parents=grp_parents,
                        fuzzy_grp=[])

        # Étape 2 — exact groupe
        if label in set_groupes:
            filiales = ref[ref["groupe_racine"] == label]["Titulaire(s)"].unique().tolist()
            return dict(match_type="exact_grp",
                        grp_exact=label,
                        filiales=filiales,
                        fuzzy_grp=[])

        # Étape 3 — fuzzy sur groupe_racine avec combined_score
        scored = []
        for g in all_groupes:
            sc = combined_score(label, g)
            if sc >= SEUIL:
                scored.append((g, sc))
        scored = sorted(scored, key=lambda x: x[1], reverse=True)[:5]

        if scored:
            return dict(match_type="fuzzy",
                        fuzzy_grp=scored)

        # Étape 4 — aucun
        return dict(match_type="aucun")

    st.caption(
        "Pour chaque entreprise importée, choisissez la correspondance la plus pertinente. "
        "Les scores indiquent la qualité du matching (🏢 exact, 🔶 approximatif). "
        "Vous pouvez toujours choisir **❌ Exclure** si aucune option ne convient."
    )

    resolved       = []
    unknown_labels = []
    fuzzy_labels   = []

    for _, row in raw_import.iterrows():
        label = row["label_import"]
        poids = row["poids"]
        c     = find_candidates(label)

        # ── Construction des options du selectbox ─────────────────────────────
        # Structure : (col_filter, val_filter, description_affichée)
        # col_filter = None signifie "exclure"
        opts = []

        if c["match_type"] == "exact_tit":
            # 1. Titulaire exact
            opts.append(("Titulaire(s)", label,
                         f"🏭 Titulaire (exact) : {label}"))
            # 2. Groupe(s) racine parent(s) + leurs filiales
            for g in c["grp_parents"]:
                opts.append(("groupe_racine", g,
                             f"🏢 Groupe racine parent : {g}"))
                filiales_du_groupe = ref[ref["groupe_racine"] == g]["Titulaire(s)"].unique().tolist()
                for t in filiales_du_groupe:
                    if t != label:  # ne pas redoublonner le titulaire lui-même
                        opts.append(("Titulaire(s)", t,
                                     f"   ↳ 🏭 Autre filiale : {t}"))

        elif c["match_type"] == "exact_grp":
            # 1. Groupe racine exact (toutes filiales confondues)
            opts.append(("groupe_racine", label,
                         f"🏢 Groupe racine (exact) : {label}  [{len(c['filiales'])} filiale(s)]"))
            # 2. Chaque filiale individuellement
            for t in c["filiales"]:
                opts.append(("Titulaire(s)", t,
                             f"🏭 Filiale : {t}"))

        elif c["match_type"] == "fuzzy":
            fuzzy_labels.append(label)
            # Pour chaque groupe fuzzy : proposer le groupe ET ses filiales
            for g, score in c["fuzzy_grp"]:
                icon = "🟢" if score >= 0.85 else "🔶"
                filiales_fuzzy = ref[ref["groupe_racine"] == g]["Titulaire(s)"].unique().tolist()
                opts.append(("groupe_racine", g,
                             f"{icon} Groupe racine ({score:.0%}) : {g}  [{len(filiales_fuzzy)} filiale(s)]"))
                for t in filiales_fuzzy:
                    opts.append(("Titulaire(s)", t,
                                 f"   ↳ 🏭 Filiale : {t}"))
            # Toujours proposer l'exclusion en dernier
            opts.append((None, None, "❌ Exclure de l'analyse"))

        else:  # aucun
            unknown_labels.append(label)
            opts.append((None, None,
                         f"❌ Aucune correspondance — Exclure : {label}"))

        # Badge résumé
        badge_map = {
            "exact_tit": "✅ titulaire exact",
            "exact_grp": "✅ groupe exact",
            "fuzzy":     "🔶 approximatif",
            "aucun":     "❌ non trouvé",
        }
        badge = badge_map.get(c["match_type"], "")

        col_lbl, col_sel = st.columns([2, 4])
        with col_lbl:
            st.markdown(f"**{label}** &nbsp; `{poids}%` &nbsp; {badge}")
        with col_sel:
            chosen_idx = st.selectbox(
                label=f"sel_{label}",
                options=range(len(opts)),
                format_func=lambda i, o=opts: o[i][2],
                key=f"sel_{label}",
                label_visibility="collapsed",
            )

        col_filter, val_filter, _ = opts[chosen_idx]

        # Si l'utilisateur choisit "Exclure", on n'ajoute pas à resolved
        if col_filter is None:
            if label not in unknown_labels:
                unknown_labels.append(label)
            continue

        resolved.append({
            "label_import": label,
            "poids":        poids,
            "col_filter":   col_filter,
            "val_filter":   val_filter,
            "match_type":   c["match_type"],
        })


    # ── Rapport de couverture ─────────────────────────────────────────────────
    nb_importes = len(raw_import)
    nb_resolus  = len(resolved)
    nb_inconnus = len(unknown_labels)
    nb_fuzzy    = len(fuzzy_labels)
    pct_couvert = nb_resolus / nb_importes * 100 if nb_importes > 0 else 0

    st.markdown("---")
    st.markdown("**📊 Couverture de l'import**")
    cov1, cov2, cov3, cov4 = st.columns(4)
    with cov1: kpi_card("Entreprises importées",      nb_importes)
    with cov2: kpi_card("✅ Correspondances retenues", nb_resolus)
    with cov3: kpi_card("❌ Exclues / non trouvées",   nb_inconnus)
    with cov4: kpi_card("📐 Couverture",               f"{pct_couvert:.1f}%")

    if nb_fuzzy:
        st.info(
            f"🔶 **{nb_fuzzy} correspondance(s) approximative(s)** — vérifiez les choix ci-dessus : "
            + ", ".join(f"`{l}`" for l in fuzzy_labels)
        )

    if unknown_labels:
        exclu_list = "  \n".join(f"- `{l}`" for l in unknown_labels)
        st.warning(
            "⚠️ **" + str(nb_inconnus) + " entreprise(s) exclue(s) de l'analyse :\n" + exclu_list
        )


    if not resolved:
        st.error("❌ Aucune entreprise retenue. Vérifiez vos choix ci-dessus.")
        st.stop()

    # ══════════════════════════════════════════════════════════════════════════
    # 3.  RÉCAPITULATIF & NORMALISATION DES POIDS
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    section_header("3️⃣ Récapitulatif du portefeuille")

    resolved_df = pd.DataFrame(resolved)
    total_weight = resolved_df["poids"].sum()
    resolved_df["poids_norm"] = resolved_df["poids"] / total_weight

    recap_display = resolved_df.copy()
    recap_display["Poids normalisé (%)"] = (resolved_df["poids_norm"] * 100).round(2)
    recap_display = recap_display.rename(columns={
        "label_import": "Importé",
        "col_filter":   "Niveau",
        "val_filter":   "Entité retenue",
        "poids":        "Poids (%)",
    })[["Importé", "Niveau", "Entité retenue", "Poids (%)", "Poids normalisé (%)"]]

    col_w, _ = st.columns([1, 3])
    with col_w:
        if abs(total_weight - 100) < 0.01:
            st.success(f"✅ Total : {total_weight:.1f}% — déjà normalisé")
        else:
            st.warning(f"⚠️ Total importé : {total_weight:.1f}% → normalisé à 100%")

    st.dataframe(recap_display, use_container_width=True, hide_index=True)

    # ══════════════════════════════════════════════════════════════════════════
    # 4.  CONSTRUCTION DU SOUS-DATAFRAME PORTEFEUILLE
    # ══════════════════════════════════════════════════════════════════════════
    @st.cache_data(show_spinner=False)
    def build_portfolio(df, resolved_list):
        frames = []
        for r in resolved_list:
            sub = df[df[r["col_filter"]] == r["val_filter"]].copy()
            sub["__poids_norm__"] = r["poids_norm"]
            sub["__label__"]      = r["label_import"]
            frames.append(sub)
        return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

    portfolio_df = build_portfolio(df3, resolved_df.to_dict("records"))

    if portfolio_df.empty:
        st.error("❌ Aucun produit trouvé pour ce portefeuille.")
        st.stop()

    # Populations
    meds = portfolio_df[portfolio_df["type_produit"] == "medicament"]
    dms  = portfolio_df[portfolio_df["type_produit"] == "dispositif_medical"]
    pct_meds = len(meds) / len(portfolio_df) * 100
    pct_dms  = len(dms)  / len(portfolio_df) * 100

    # KPIs globaux
    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    section_header("📊 Aperçu global")
    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi_card("Total produits",    len(portfolio_df))
    with c2: kpi_card("💊 Médicaments",   f"{len(meds)} ({pct_meds:.0f}%)")
    with c3: kpi_card("🩺 Dispositifs",    f"{len(dms)} ({pct_dms:.0f}%)")
    with c4: kpi_card("Entités retenues",  len(resolved_df))

    # ══════════════════════════════════════════════════════════════════════════
    # 5.  FONCTIONS DE CALCUL DES PROFILS PONDÉRÉS
    # ══════════════════════════════════════════════════════════════════════════

    def weighted_profile(sub_portfolio, col, order, resolved_list):
        """
        Distribution pondérée d'une colonne normalisée sur une sous-population.
        Chaque entité contribue selon son poids_norm × la distribution interne
        de ses produits (équipondération intra-entité).
        Retourne un DataFrame [Niveau, Pourcentage (%)].
        """
        totals = {}
        total_poids_effectif = 0.0

        for r in resolved_list:
            sub = sub_portfolio[sub_portfolio["__label__"] == r["label_import"]]
            if sub.empty:
                continue
            poids = r["poids_norm"]
            total_poids_effectif += poids
            counts = sub[col].value_counts(normalize=True)
            for val, prop in counts.items():
                totals[val] = totals.get(val, 0) + prop * poids

        if not totals or total_poids_effectif == 0:
            return pd.DataFrame(columns=["Niveau", "Pourcentage (%)"])

        # Renormaliser par le poids effectif (si certaines entités n'ont que meds ou DM)
        result = pd.DataFrame(
            [(k, v / total_poids_effectif * 100) for k, v in totals.items()],
            columns=["Niveau", "Pourcentage (%)"]
        )
        # Ordonner
        order_map = {v: i for i, v in enumerate(order)}
        result["_ord"] = result["Niveau"].map(lambda x: order_map.get(x, 999))
        result = (result.sort_values("_ord")
                        .drop(columns="_ord")
                        .reset_index(drop=True))
        result["Pourcentage (%)"] = result["Pourcentage (%)"].round(2)
        return result[result["Pourcentage (%)"] > 0]

    def make_pie(df_profile, colors_map, title, legend_map=None, height=380):
        """Génère un camembert Plotly à partir d'un profil pondéré."""
        if df_profile is None or df_profile.empty:
            st.info("Aucune donnée disponible pour ce graphique.")
            return

        df_p = df_profile.copy()
        # Remplacer les clés par les labels de légende si fourni
        if legend_map:
            df_p["Légende"] = df_p["Niveau"].map(lambda x: legend_map.get(x, x))
        else:
            df_p["Légende"] = df_p["Niveau"]

        color_seq = [colors_map.get(n, "#cccccc") for n in df_p["Niveau"]]

        fig = px.pie(
            df_p,
            values="Pourcentage (%)",
            names="Légende",
            hole=0.42,
            title=title,
        )
        fig.update_traces(
            marker=dict(colors=color_seq),
            textposition="inside",
            textinfo="percent+label",
        )
        fig.update_layout(
            margin=dict(t=55, b=20, l=10, r=160),
            height=height,
            showlegend=True,
            legend=dict(orientation="v", yanchor="middle", y=0.5, x=1.02, font=dict(size=10)),
        )
        st.plotly_chart(fig, use_container_width=True)

    resolved_list = resolved_df.to_dict("records")

    # ══════════════════════════════════════════════════════════════════════════
    # 6.  CAMEMBERTS — SMR (médicaments) / SR (dispositifs)
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    section_header("5️⃣ Répartition qualitative pondérée")

    # ── Bloc SMR / SR ─────────────────────────────────────────────────────────
    st.markdown("#### 💊 SMR — Médicaments &nbsp;|&nbsp; 🩺 SR — Dispositifs médicaux")
    st.caption(
        "Le **SMR** (Service Médical Rendu, HAS) et le **SR** (Service Rendu, CNEDiMTS) "
        "utilisent la même échelle qualitative mais s'appliquent à des populations distinctes. "
        "Ils sont présentés séparément pour éviter toute confusion."
    )

    smr_profile = weighted_profile(meds, "_smr_norm", SMR_ORDER, resolved_list)
    sr_profile  = weighted_profile(dms,  "_smr_norm", SR_ORDER,  resolved_list)

    col_smr, col_sr = st.columns(2, gap="large")
    with col_smr:
        if meds.empty:
            st.info("Aucun médicament dans ce portefeuille.")
        else:
            make_pie(
                smr_profile, SMR_COLORS,
                f"SMR — Médicaments ({len(meds)} produits, {pct_meds:.0f}% du portefeuille)"
            )
    with col_sr:
        if dms.empty:
            st.info("Aucun dispositif médical dans ce portefeuille.")
        else:
            make_pie(
                sr_profile, SR_COLORS,
                f"SR — Dispositifs ({len(dms)} produits, {pct_dms:.0f}% du portefeuille)"
            )

    # Tableaux détail SMR/SR
    col_t1, col_t2 = st.columns(2, gap="large")
    with col_t1:
        if not smr_profile.empty:
            st.dataframe(smr_profile, use_container_width=True, hide_index=True)
    with col_t2:
        if not sr_profile.empty:
            st.dataframe(sr_profile, use_container_width=True, hide_index=True)

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)

    # ── Bloc ASMR / ASR ───────────────────────────────────────────────────────
    st.markdown("#### 💊 ASMR — Médicaments &nbsp;|&nbsp; 🩺 ASR — Dispositifs médicaux")
    st.caption(
        "**ASMR** (Amélioration du Service Médical Rendu, HAS) et **ASR** (Amélioration du Service Rendu, CNEDiMTS) : "
        "même échelle I→V, mais commissions et populations différentes. "
        "Les valeurs longues de la colonne brute (`V. Absence d'amélioration`, etc.) ont été identifiées comme ASR ; "
        "les valeurs courtes (`I`…`V`) ont été attribuées selon le `type_produit`."
    )

    # Légende commune pour les deux camemberts
    ASMR_LEGEND = {
        "I":           "I — Majeure",
        "II":          "II — Importante",
        "III":         "III — Modérée",
        "IV":          "IV — Mineure",
        "V":           "V — Absente",
        "Non chiffré": "Non chiffré",
        "Non précisé": "Non précisé",
    }

    # Filtrer par source détectée (champ _source_amr)
    meds_asmr = portfolio_df[portfolio_df["_source_amr"] == "ASMR"]
    dms_asr   = portfolio_df[portfolio_df["_source_amr"] == "ASR"]

    asmr_profile = weighted_profile(meds_asmr, "_roman", ASMR_ORDER, resolved_list)
    asr_profile  = weighted_profile(dms_asr,   "_roman", ASR_ORDER,  resolved_list)

    col_asmr, col_asr = st.columns(2, gap="large")
    with col_asmr:
        if meds_asmr.empty:
            st.info("Aucune donnée ASMR dans ce portefeuille.")
        else:
            make_pie(
                asmr_profile, ASMR_COLORS,
                f"ASMR — Médicaments ({len(meds_asmr)} produits évalués)",
                legend_map=ASMR_LEGEND,
            )
    with col_asr:
        if dms_asr.empty:
            st.info("Aucune donnée ASR dans ce portefeuille.")
        else:
            make_pie(
                asr_profile, ASR_COLORS,
                f"ASR — Dispositifs ({len(dms_asr)} produits évalués)",
                legend_map=ASMR_LEGEND,
            )

    # Tableaux détail ASMR/ASR avec libellé complet
    col_t3, col_t4 = st.columns(2, gap="large")

    def enrich_profile_table(df_profile, legend_map):
        if df_profile.empty:
            return df_profile
        df_profile = df_profile.copy()
        df_profile.insert(1, "Signification", df_profile["Niveau"].map(lambda x: legend_map.get(x, x)))
        return df_profile

    with col_t3:
        if not asmr_profile.empty:
            st.dataframe(
                enrich_profile_table(asmr_profile, ASMR_LEGEND),
                use_container_width=True, hide_index=True
            )
    with col_t4:
        if not asr_profile.empty:
            st.dataframe(
                enrich_profile_table(asr_profile, ASMR_LEGEND),
                use_container_width=True, hide_index=True
            )

    # ══════════════════════════════════════════════════════════════════════════
    # 7.  EXPORT
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    section_header("6️⃣ Export")

    def profiles_to_excel(smr_p, sr_p, asmr_p, asr_p, legend_map):
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            for df_p, sheet in [(smr_p, "SMR"), (sr_p, "SR")]:
                if not df_p.empty:
                    df_p.to_excel(writer, sheet_name=sheet, index=False)
            for df_p, sheet in [(asmr_p, "ASMR"), (asr_p, "ASR")]:
                if not df_p.empty:
                    enrich_profile_table(df_p, legend_map).to_excel(writer, sheet_name=sheet, index=False)
        buf.seek(0)
        return buf.read()

    col_dl1, col_dl2, col_dl3, _ = st.columns([1, 1, 1, 1])

    with col_dl1:
        export_cols = [c for c in portfolio_df.columns if not c.startswith("__") and not c.startswith("_")]
        st.download_button(
            "📥 Portefeuille complet (Excel)",
            data=export_excel(portfolio_df[export_cols]),
            file_name=f"portefeuille_{datetime.now().date()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    with col_dl2:
        st.download_button(
            "📥 Profils SMR/SR/ASMR/ASR (Excel)",
            data=profiles_to_excel(smr_profile, sr_profile, asmr_profile, asr_profile, ASMR_LEGEND),
            file_name=f"profils_qualite_{datetime.now().date()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    with col_dl3:
        st.download_button(
            "📥 Correspondances retenues (Excel)",
            data=export_excel(recap_display),
            file_name=f"correspondances_{datetime.now().date()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )


# In[ ]:




