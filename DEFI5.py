#!/usr/bin/env python
# coding: utf-8

# In[2]:


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
elif page == "📁  Portefeuille":
    st.markdown('<div class="page-title">📁 Construction de Portefeuille</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Composez un portefeuille multi-groupes avec pondération personnalisée</div>', unsafe_allow_html=True)

    groups = sorted(df3["groupe_racine"].dropna().unique())

    section_header("1️⃣ Sélection des groupes")
    selected_groups = st.multiselect("Groupes :", groups, placeholder="Chercher un groupe...", label_visibility="collapsed")

    if not selected_groups:
        st.info("👆 Sélectionnez au moins un groupe pour construire votre portefeuille.")
        st.stop()

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    section_header("2️⃣ Pondération")
    st.caption("Les poids sont normalisés automatiquement à 100%.")

    default_w = round(100 / len(selected_groups), 1)
    portfolio_df = pd.DataFrame({
        "Groupe": selected_groups,
        "Poids (%)": [default_w] * len(selected_groups),
        "Nb produits": [len(df3[df3["groupe_racine"] == g]) for g in selected_groups]
    })
    edited_df = st.data_editor(portfolio_df, num_rows="fixed", use_container_width=True,
        column_config={
            "Groupe": st.column_config.TextColumn("Groupe", disabled=True),
            "Poids (%)": st.column_config.NumberColumn("Poids (%)", min_value=0, max_value=100, step=0.5, format="%.1f"),
            "Nb produits": st.column_config.NumberColumn("Produits", disabled=True),
        })

    total_weight = edited_df["Poids (%)"].sum()
    col_w, _ = st.columns([1, 3])
    with col_w:
        if total_weight == 0:
            st.error("Les pondérations ne peuvent pas être nulles.")
            st.stop()
        elif abs(total_weight - 100) < 0.01:
            st.success(f"✅ Total : {total_weight:.1f}%")
        else:
            st.warning(f"⚠️ Total : {total_weight:.1f}% → normalisé à 100%")

    edited_df["Poids normalisé"] = edited_df["Poids (%)"] / total_weight

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    section_header("3️⃣ Analyse qualitative")
    col_ind, _ = st.columns([2, 3])
    with col_ind:
        choix = st.radio("Indicateur :", ["SMR / SR", "ASMR / ASR"], horizontal=True, label_visibility="collapsed")

    # col_selected et mappings définis APRÈS le radio
    col_selected = SMR_COL if choix == "SMR / SR" else ASMR_COL
    lmap_port = SMR_LABELS  if choix == "SMR / SR" else ASMR_LABELS
    cmap_port = SMR_COLORS  if choix == "SMR / SR" else ASMR_COLORS

    portfolio_filtered = df3[df3["groupe_racine"].isin(selected_groups)]
    total_p  = len(portfolio_filtered)
    nb_med_p = int((portfolio_filtered["type_produit"] == "medicament").sum())
    nb_dm_p  = int((portfolio_filtered["type_produit"] == "dispositif_medical").sum())
    high_v   = (portfolio_filtered[ASMR_COL].isin(["I", "II"]).mean() * 100
                if choix == "ASMR / ASR"
                else portfolio_filtered[SMR_COL].isin(["Important"]).mean() * 100)

    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi_card("Total produits", total_p)
    with c2: kpi_card("💊 Médicaments", nb_med_p)
    with c3: kpi_card("🩺 Dispositifs", nb_dm_p)
    with c4: kpi_card(f"% top niveau ({choix})", f"{high_v:.1f}%")

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    section_header("📊 Répartition pondérée")

    profile_series = compute_portfolio_profile(df3, edited_df, col_selected)

    if not profile_series.empty:
        # Applique le label_map sur l'index avant de construire le DataFrame
        profile_index_labeled = [lmap_port.get(str(k).strip(), k) for k in profile_series.index]
        profile_df = pd.DataFrame({
            "Valeur": profile_index_labeled,
            "Pourcentage": profile_series.values * 100
        })
        # Regroupe les éventuels doublons (ex: V et V.absence → même label)
        profile_df = profile_df.groupby("Valeur", as_index=False)["Pourcentage"].sum()

        col_graph, col_table = st.columns([3, 2], gap="large")
        with col_graph:
            fig = px.pie(
                profile_df,
                values="Pourcentage",
                names="Valeur",
                title=f"Répartition {choix} pondérée du portefeuille",
                color="Valeur",
                color_discrete_map=cmap_port,
                hole=0.4,
            )
            fig.update_traces(textposition="inside", textinfo="percent")
            fig.update_layout(
                margin=dict(t=50, b=40, l=20, r=180),
                height=420,
                legend=dict(orientation="v", yanchor="middle", y=0.5, x=1.02, font=dict(size=11))
            )
            st.plotly_chart(fig, use_container_width=True)

        with col_table:
            st.markdown("**Détail par niveau**")
            disp = profile_df.copy()
            disp["Pourcentage"] = disp["Pourcentage"].round(1)
            disp = disp.sort_values("Pourcentage", ascending=False)
            disp.columns = ["Niveau", "Poids (%)"]
            st.dataframe(disp, use_container_width=True, hide_index=True, height=300)
    else:
        st.info("Aucune donnée disponible pour cette sélection.")

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    section_header("📥 Export")
    col_dl1, col_dl2, _ = st.columns([1, 1, 2])
    with col_dl1:
        st.download_button("📥 Portefeuille complet (Excel)", data=export_excel(portfolio_filtered),
            file_name=f"portefeuille_{datetime.now().date()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True)
    if not profile_series.empty:
        with col_dl2:
            exp_df = pd.DataFrame({
                "Niveau": profile_index_labeled,
                "Pourcentage (%)": (profile_series.values * 100).round(1)
            })
            st.download_button(f"📥 Profil {choix} (Excel)", data=export_excel(exp_df),
                file_name=f"profil_{choix[:3]}_{datetime.now().date()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True)


# In[ ]:




