#!/usr/bin/env python
# coding: utf-8

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                         DEFIS Pharma — app.py                          ║
# ║              Analyse & Intelligence Marché — Streamlit                 ║
# ╚══════════════════════════════════════════════════════════════════════════╝

import io
import re
import unicodedata
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

# ══════════════════════════════════════════════════════════════════════════════
# 0.  CONFIG PAGE
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="DEFIS Pharma",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════════════
# 1.  CSS
# ══════════════════════════════════════════════════════════════════════════════
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
    .page-title   { font-size: 28px; font-weight: 800; color: #0f2744; margin-bottom: 4px; }
    .page-subtitle{ color: #6b7280; font-size: 14px; margin-bottom: 24px; }
    hr.thin { border: none; border-top: 1px solid #e5e7eb; margin: 20px 0; }

    #MainMenu {visibility: hidden;}
    footer    {visibility: hidden;}
    header    {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# 2.  CONSTANTES QUALITÉ  (source unique — utilisées dans toutes les pages)
# ══════════════════════════════════════════════════════════════════════════════

# ── SMR / SR ──────────────────────────────────────────────────────────────────
SMR_ORDER = ["Important", "Suffisant", "Modéré", "Faible", "Insuffisant",
             "Non chiffré", "Non précisé"]
SMR_COLORS = {
    "Important":   "#1a7f4b",
    "Suffisant":   "#52b788",
    "Modéré":      "#f4a835",
    "Faible":      "#e07b39",
    "Insuffisant": "#d94f3d",
    "Non chiffré": "#b0bec5",
    "Non précisé": "#cfd8dc",
}
SMR_NORM = {
    "Important":    "Important",
    "Modéré":       "Modéré",
    "Suffisant":    "Suffisant",
    "Faible":       "Faible",
    "Insuffisant":  "Insuffisant",
    "Commentaires": "Non chiffré",
    "Non précisé":  "Non précisé",
}
# SR = même palette (commission CNEDiMTS, même échelle)
SR_ORDER  = SMR_ORDER
SR_COLORS = SMR_COLORS

# ── ASMR / ASR ────────────────────────────────────────────────────────────────
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
ASMR_LEGEND = {
    "I":           "I — Majeure",
    "II":          "II — Importante",
    "III":         "III — Modérée",
    "IV":          "IV — Mineure",
    "V":           "V — Absente",
    "Non chiffré": "Non chiffré",
    "Non précisé": "Non précisé",
}
ASR_ORDER  = ASMR_ORDER
ASR_COLORS = ASMR_COLORS

# Labels courts pour les pages Recherche / Labo (compatibilité avec l'ancien code)
SMR_LABELS_SHORT = {
    "Important":   "SMR Important",
    "Modéré":      "SMR Modéré",
    "Faible":      "SMR Faible",
    "Insuffisant": "SMR Insuffisant",
}
SMR_COLORS_SHORT = {v: SMR_COLORS[k] for k, v in SMR_LABELS_SHORT.items()}
SR_LABELS_SHORT  = {
    "Important":   "SR Important",
    "Modéré":      "SR Modéré",
    "Faible":      "SR Faible",
    "Insuffisant": "SR Insuffisant",
}
SR_COLORS_SHORT = {v: SR_COLORS[k] for k, v in SR_LABELS_SHORT.items()}
ASMR_LABELS_SHORT = {
    "I":                      "I – Progrès majeur",
    "II":                     "II – Amélioration importante",
    "III":                    "III – Amélioration modérée",
    "IV":                     "IV – Amélioration mineure",
    "V":                      "V – Absence d'amélioration",
    "V.absence amélioration": "V – Absence d'amélioration",
    "NA":                     "Non applicable",
}
ASMR_COLORS_SHORT = {
    "I – Progrès majeur":           "#1a3a5c",
    "II – Amélioration importante": "#2563eb",
    "III – Amélioration modérée":   "#60a5fa",
    "IV – Amélioration mineure":    "#f59e0b",
    "V – Absence d'amélioration":   "#dc2626",
    "Non applicable":               "#d1d5db",
}
ASR_LABELS_SHORT = {
    "I":   "I – Amélioration substantielle",
    "II":  "II – Amélioration modérée",
    "III": "III – Amélioration faible",
    "IV":  "IV – Absence d'amélioration",
    "NA":  "Non applicable",
}
ASR_COLORS_SHORT = {
    "I – Amélioration substantielle": "#1a3a5c",
    "II – Amélioration modérée":      "#2563eb",
    "III – Amélioration faible":      "#f59e0b",
    "IV – Absence d'amélioration":    "#dc2626",
    "Non applicable":                 "#d1d5db",
}

# ── Colonnes de référence ─────────────────────────────────────────────────────
SMR_COL  = "Valeur du SMR"
ASMR_COL = "Valeur de l'ASMR"


# ══════════════════════════════════════════════════════════════════════════════
# 3.  UTILITAIRES GÉNÉRAUX
# ══════════════════════════════════════════════════════════════════════════════

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise les noms de colonnes (apostrophes, espaces insécables, tirets…)."""
    def clean(col: str) -> str:
        for ch in ['\u2019', '\u2018', '\u02bc', '\u0060', '\u00b4']:
            col = col.replace(ch, "'")
        col = col.replace('\u00a0', ' ').replace('\u2013', '-').replace('\u2014', '-')
        return unicodedata.normalize('NFKC', col).strip()
    df.columns = [clean(c) for c in df.columns]
    return df


def clean_illegal_characters(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Supprime les caractères de contrôle illégaux pour Excel."""
    illegal = re.compile(r"[\x00-\x08\x0B-\x0C\x0E-\x1F]")
    df_c = dataframe.copy()
    for col in df_c.columns:
        if df_c[col].dtype == "object":
            df_c[col] = df_c[col].astype(str).apply(lambda x: illegal.sub("", x))
    return df_c


def export_excel(dataframe: pd.DataFrame, sheet_name: str = "Export") -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        clean_illegal_characters(dataframe).to_excel(
            writer, index=False, sheet_name=sheet_name
        )
    return output.getvalue()


# ══════════════════════════════════════════════════════════════════════════════
# 4.  COMPOSANTS UI RÉUTILISABLES
# ══════════════════════════════════════════════════════════════════════════════

def kpi_card(label: str, value, delta=None, delta_label: str = "vs groupe 2"):
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


def section_header(title: str):
    st.markdown(f'<div class="section-header">{title}</div>', unsafe_allow_html=True)


def plot_pie(df_lab: pd.DataFrame, col_valeur: str, title: str,
             label_map=None, color_map=None, height: int = 380):
    """
    Camembert avec labels enrichis et couleurs sémantiques.
    - Pourcentage uniquement dans le camembert
    - Label complet dans la légende
    """
    df_c = df_lab.copy()
    df_c["pie_label"] = (
        df_c[col_valeur].fillna("Non renseigné").astype(str).str.strip()
    )
    if label_map:
        df_c["pie_label"] = df_c["pie_label"].apply(lambda x: label_map.get(x, x))

    pie_counts = df_c["pie_label"].value_counts().reset_index()
    pie_counts.columns = ["Valeur", "count"]

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
        margin=dict(t=50, b=20, l=20, r=160),
        height=height,
        legend=dict(orientation="v", yanchor="middle", y=0.5, x=1.02, font=dict(size=11)),
    )
    fig.update_traces(textposition="inside", textinfo="percent")
    st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# 5.  CHARGEMENT & NETTOYAGE DES DONNÉES
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(show_spinner="Chargement des données…")
def load_csv_from_drive(file_id: str, sep: str = "\t") -> pd.DataFrame:
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


# IDs Google Drive
ID_COMPACT   = "1y-vVibmmuKyBcMcSX6UopgP5YuVos-Xn"
ID_BIG10     = "1TDzeC3Ug3JSN9wI1ENlGks4dwWL64jMU"
ID_DISPO     = "1EUDSX1PJowZPQ949dzbyKLX_BTBZBe3q"
ID_MED_DISPO = "1LvHeyHG1PFC965nUn1XLE8O2u455jnsR"

df  = load_csv_from_drive(ID_COMPACT)
df1 = load_csv_from_drive(ID_BIG10)
df2 = load_csv_from_drive(ID_DISPO)
df3 = load_csv_from_drive(ID_MED_DISPO)

# ── Mapping laboratoires (appliqué sur df ET df1) ────────────────────────────
MAPPING_LABO = {
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
    " PFIZER (GRANDE BRETAGNE)": "PFIZER",
    " PFIZER EUROPE MA EEIG (BELGIQUE)": "PFIZER",
    " PFIZER EUROPE MA EEIG (BELGIQUE);PFIZER (GRANDE BRETAGNE)": "PFIZER",
    " PFIZER EUROPE MA EEIG (ROYAUME UNI)": "PFIZER",
    " PFIZER HOLDING FRANCE": "PFIZER",
    " PFIZER IRELAND PHARMACEUTICALS (IRLANDE)": "PFIZER",
    " PFIZER PFE FRANCE": "PFIZER",
    " ROCHE": "ROCHE", " ROCHE REGISTRATION": "ROCHE",
    " ROCHE REGISTRATION (ALLEMAGNE)": "ROCHE",
}

df["Titulaire(s)"]  = df["Titulaire(s)"].replace(MAPPING_LABO)
df1["Titulaire(s)"] = df1["Titulaire(s)"].replace(MAPPING_LABO)   # ← correction
df = df.drop_duplicates(subset=["Code CIS", "CIP13"], keep="first")


# ══════════════════════════════════════════════════════════════════════════════
# 6.  NORMALISATION QUALITÉ (pour df3 — page Portefeuille)
# ══════════════════════════════════════════════════════════════════════════════

ROMAN_TO_LABEL = {
    "I":   "I — Majeure",
    "II":  "II — Importante",
    "III": "III — Modérée",
    "IV":  "IV — Mineure",
    "V":   "V — Absente",
}

def normalize_smr(val) -> str:
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
      3. "Commentaires…" → Non chiffré
      4. Tout le reste → Non précisé
    """
    if pd.isna(val) or str(val).strip() == "":
        return ("Non précisé", "Non précisé", "Non précisé")
    v = str(val).strip()
    m = re.match(r'^(I{1,3}V?|VI{0,3}|IV|V)\.\s+', v)
    if m:
        roman = m.group(1)
        return (roman, ROMAN_TO_LABEL.get(roman, roman), "ASR")
    if v in ROMAN_TO_LABEL:
        source = "ASMR" if str(type_produit) == "medicament" else "ASR"
        return (v, ROMAN_TO_LABEL[v], source)
    if "commentaire" in v.lower():
        source = "ASMR" if str(type_produit) == "medicament" else "ASR"
        return ("Non chiffré", "Non chiffré", source)
    return ("Non précisé", "Non précisé", "Non précisé")


@st.cache_data(show_spinner=False)
def enrich_df3(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["_smr_norm"] = df["Valeur du SMR"].apply(normalize_smr)
    parsed = df.apply(
        lambda r: pd.Series(
            normalize_asmr_asr(r["Valeur de l'ASMR"], r["type_produit"]),
            index=["_roman", "_label_amr", "_source_amr"],
        ),
        axis=1,
    )
    return pd.concat([df, parsed], axis=1)


df3_enriched = enrich_df3(df3)   # variable séparée — ne pollue pas df3 global


# ══════════════════════════════════════════════════════════════════════════════
# 7.  HELPERS PAGE LABORATOIRE
# ══════════════════════════════════════════════════════════════════════════════

def compute_kpi(dataframe: pd.DataFrame):
    total  = len(dataframe)
    nb_med = int((dataframe["type_produit"] == "medicament").sum()) \
             if "type_produit" in dataframe.columns else 0
    nb_dm  = int((dataframe["type_produit"] == "dispositif_medical").sum()) \
             if "type_produit" in dataframe.columns else 0
    asmr_col = next((c for c in dataframe.columns if "asmr" in c.lower()), None)
    taux = dataframe[asmr_col].isin(["I", "II"]).mean() * 100 if asmr_col else 0.0
    return total, nb_med, nb_dm, taux


# ══════════════════════════════════════════════════════════════════════════════
# 8.  FUZZY MATCHING  (v3 — Jaccard pur, seuil 0.7, sans token_substring)
# ══════════════════════════════════════════════════════════════════════════════
#
# REMPLACE entièrement le bloc §8 de app_defis_pharma.py
#
# Changements vs v2 :
#   - token_substring() SUPPRIMÉ  → était la source des 310 faux positifs
#   - combined_score()  SUPPRIMÉ  → remplacé par token_jaccard() seul
#   - SEUIL_FUZZY passé de 0.5 → 0.70
#   - build_selectbox_options() : cas "aucun" liste groupe_racine + filiales
#   - find_candidates() : plus de call à token_substring
#
# Pourquoi Jaccard pur règle le problème :
#   "Laboratoires Servier" → tokens {"SERVIER"}          (LABORATOIRES = stopword)
#   "Laboratoires Alcon"   → tokens {"ALCON"}
#   "Laboratoires Alter"   → tokens {"ALTER"}
#   Jaccard("SERVIER", "ALCON") = 0 ∩ / {SERVIER,ALCON} = 0.0  → exclu ✓
#   Jaccard("SERVIER", "SERVIER INTERNATIONAL") = {SERVIER}/{SERVIER,INTERNATIONAL}
#                                               = 0.5 < 0.7    → exclu ✓
#   Jaccard("SERVIER", "SERVIER") = 1.0 ≥ 0.7               → retenu ✓
# ──────────────────────────────────────────────────────────────────────────────

STOPWORDS = {
    "LABORATORIES", "LABORATORY", "LABS", "PHARMA", "PHARMACEUTICALS",
    "PHARMACEUTICAL", "HEALTHCARE", "HEALTH", "HOLDING", "HOLDINGS",
    "FRANCE", "EUROPE", "EUROPEAN", "INTERNATIONAL", "WORLDWIDE", "GLOBAL",
    "GROUP", "GROUPE", "GMBH", "SARL", "SAS", "SA", "AG", "BV", "NV",
    "LIMITED", "LTD", "INC", "CORP", "CORPORATION", "COMPANY", "CO",
    "NORTH", "SOUTH", "EAST", "WEST", "AMERICA", "AMERICAS", "ASIA",
    "PACIFIC", "US", "USA", "UK", "EU",
    "LABORATOIRES", "LABORATOIRE",   # ← ajout clé
    "ET", "AND", "THE", "DE", "DU", "DES", "LE", "LA", "LES",
}

SEUIL_FUZZY = 0.70   # strict : seuls les noms vraiment proches matchent


def meaningful_tokens(label: str, min_len: int = 3) -> list[str]:
    """
    Extrait les tokens significatifs d'un label.
    - Découpe sur espaces, tirets, slashes, parenthèses, points, virgules
    - Exclut les stopwords et les tokens trop courts
    Exemple :
      "Laboratoires Servier SA"      → ["SERVIER"]
      "Bristol-Myers Squibb France"  → ["BRISTOL", "MYERS", "SQUIBB"]
      "Novo Nordisk (Danemark)"      → ["NOVO", "NORDISK"]
    """
    raw = re.split(r"[\s\-_/,\.\(\);]+", label.upper())
    return [t for t in raw if len(t) >= min_len and t not in STOPWORDS]


def token_jaccard(label: str, candidate: str) -> float:
    """
    Score de Jaccard sur les ensembles de tokens significatifs.

    Jaccard(A, B) = |A ∩ B| / |A ∪ B|

    Propriétés clés :
      - Symétrique
      - Insensible aux tokens génériques (stopwords exclus)
      - NE favorise PAS les chaînes longues qui partagent des mots communs
      - Retourne 0.0 si les deux ensembles sont vides (pas de division par zéro)

    Exemples avec SEUIL = 0.70 :
      "Servier" vs "Servier"                → 1.00  ✓ retenu
      "Servier" vs "Servier Laboratoires"   → 0.50  ✗ exclu  (token SERVIER / {SERVIER})
      "Servier" vs "Alcon"                  → 0.00  ✗ exclu
      "Bristol Myers" vs "Bristol Myers Squibb" → 0.67  ✗ exclu (strict)
      "Bristol Myers Squibb" vs "Bristol Myers Squibb" → 1.00 ✓ retenu
    """
    a = set(meaningful_tokens(label))
    b = set(meaningful_tokens(candidate))
    if not a and not b:
        return 0.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def find_candidates(
    label: str,
    ref: pd.DataFrame,
    set_titulaires: set,
    set_groupes: set,
    all_groupes: list,
) -> dict:
    """
    4 étapes ordonnées :
      1. Exact sur Titulaire(s)       → match_type = 'exact_tit'
      2. Exact sur groupe_racine      → match_type = 'exact_grp'
      3. Fuzzy Jaccard ≥ SEUIL_FUZZY  → match_type = 'fuzzy'
      4. Aucun                        → match_type = 'aucun'

    Étape 3 : on évalue séparément
      a) les groupe_racine   (score Jaccard label vs groupe)
      b) les Titulaire(s)    (score Jaccard label vs titulaire)
    et on retourne les 5 meilleurs toutes sources confondues,
    en évitant les doublons groupe/filiale.
    """
    # ── Étape 1 : exact titulaire ─────────────────────────────────────────────
    if label in set_titulaires:
        grp_parents = ref[ref["Titulaire(s)"] == label]["groupe_racine"].unique().tolist()
        return dict(match_type="exact_tit", tit_exact=label, grp_parents=grp_parents)

    # ── Étape 2 : exact groupe ────────────────────────────────────────────────
    if label in set_groupes:
        filiales = ref[ref["groupe_racine"] == label]["Titulaire(s)"].unique().tolist()
        return dict(match_type="exact_grp", grp_exact=label, filiales=filiales)

    # ── Étape 3 : fuzzy sur groupes ET titulaires ─────────────────────────────
    scored_groupes = [
        (g, token_jaccard(label, g))
        for g in all_groupes
    ]
    scored_groupes = [
        (g, sc) for g, sc in scored_groupes if sc >= SEUIL_FUZZY
    ]
    scored_groupes.sort(key=lambda x: x[1], reverse=True)

    all_titulaires_list = ref["Titulaire(s)"].unique().tolist()
    scored_tits = [
        (t, token_jaccard(label, t))
        for t in all_titulaires_list
    ]
    scored_tits = [
        (t, sc) for t, sc in scored_tits if sc >= SEUIL_FUZZY
    ]
    scored_tits.sort(key=lambda x: x[1], reverse=True)

    if scored_groupes or scored_tits:
        return dict(
            match_type="fuzzy",
            fuzzy_grp=scored_groupes[:5],
            fuzzy_tit=scored_tits[:5],
        )

    # ── Étape 4 : aucun ───────────────────────────────────────────────────────
    return dict(match_type="aucun")


def build_selectbox_options(
    c: dict,
    label: str,
    ref: pd.DataFrame,
    all_groupes: list,
) -> list:
    """
    Construit la liste (col_filter, val_filter, description_affichée).
    col_filter = None  →  option "Exclure" ou séparateur visuel (non sélectionnable).

    Cas 'aucun' : propose ❌ Exclure en tête,
                  puis TOUS les groupe_racine avec leurs filiales.
    """
    opts = []

    # ── exact titulaire ───────────────────────────────────────────────────────
    if c["match_type"] == "exact_tit":
        opts.append(("Titulaire(s)", label, f"🏭 Titulaire (exact) : {label}"))
        for g in c["grp_parents"]:
            opts.append(("groupe_racine", g, f"🏢 Groupe racine parent : {g}"))
            for t in ref[ref["groupe_racine"] == g]["Titulaire(s)"].unique():
                if t != label:
                    opts.append(("Titulaire(s)", t, f"   ↳ 🏭 Autre filiale : {t}"))

    # ── exact groupe ──────────────────────────────────────────────────────────
    elif c["match_type"] == "exact_grp":
        opts.append((
            "groupe_racine", label,
            f"🏢 Groupe racine (exact) : {label}  [{len(c['filiales'])} filiale(s)]",
        ))
        for t in c["filiales"]:
            opts.append(("Titulaire(s)", t, f"🏭 Filiale : {t}"))

    # ── fuzzy ─────────────────────────────────────────────────────────────────
    elif c["match_type"] == "fuzzy":
        seen_groupes = set()

        # Groupes fuzzy
        for g, score in c.get("fuzzy_grp", []):
            icon = "🟢" if score >= 0.85 else "🔶"
            filiales = ref[ref["groupe_racine"] == g]["Titulaire(s)"].unique().tolist()
            opts.append((
                "groupe_racine", g,
                f"{icon} Groupe ({score:.0%}) : {g}  [{len(filiales)} filiale(s)]",
            ))
            seen_groupes.add(g)
            for t in filiales:
                opts.append(("Titulaire(s)", t, f"   ↳ 🏭 Filiale : {t}"))

        # Titulaires fuzzy (si leur groupe n'est pas déjà listé)
        for t, score in c.get("fuzzy_tit", []):
            icon = "🟢" if score >= 0.85 else "🔶"
            grp = ref[ref["Titulaire(s)"] == t]["groupe_racine"].values
            grp_str = grp[0] if len(grp) else "?"
            if grp_str not in seen_groupes:
                opts.append((
                    "Titulaire(s)", t,
                    f"{icon} Filiale ({score:.0%}) : {t}  [groupe : {grp_str}]",
                ))

        opts.append((None, None, "❌ Exclure de l'analyse"))

    # ── aucun : ❌ en tête + référentiel complet ──────────────────────────────
    else:
        opts.append((None, None, "❌ Exclure (aucune correspondance automatique)"))
        opts.append((None, None, "─── Référentiel complet — choisir manuellement ───"))
        for g in sorted(all_groupes):
            filiales = ref[ref["groupe_racine"] == g]["Titulaire(s)"].unique().tolist()
            opts.append((
                "groupe_racine", g,
                f"🏢 {g}  [{len(filiales)} filiale(s)]",
            ))
            for t in sorted(filiales):
                opts.append(("Titulaire(s)", t, f"   ↳ 🏭 {t}"))

    return opts

# ══════════════════════════════════════════════════════════════════════════════
# 9.  SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding:16px 0 24px 0;">
        <div style="font-size:36px">💊</div>
        <div style="font-size:20px; font-weight:800; color:#e8f0fe; letter-spacing:1px;">DEFIS Pharma</div>
        <div style="font-size:11px; color:#94a3b8; margin-top:4px;">Analyse & Intelligence Marché</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    st.markdown(
        "<div style='font-size:11px; font-weight:700; letter-spacing:1.5px;"
        " color:#94a3b8; padding-bottom:8px;'>NAVIGATION</div>",
        unsafe_allow_html=True,
    )
    page = st.radio("", [
        "🔎  Recherche Produit",
        "🏢  Analyse Laboratoire",
        "💰  Chiffre d'Affaires",
        "📁  Portefeuille",
    ], label_visibility="collapsed")
    st.markdown("---")
    st.markdown(
        f"<div style='font-size:11px; color:#64748b; text-align:center;'>"
        f"Données au<br><strong style='color:#94a3b8;'>"
        f"{datetime.now().strftime('%d %b %Y')}</strong></div>",
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
# 10.  PAGE 1 — RECHERCHE PRODUIT
# ══════════════════════════════════════════════════════════════════════════════
def page_recherche():
    st.markdown('<div class="page-title">🔎 Recherche Produit</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Retrouvez les informations d\'un médicament ou d\'un dispositif médical</div>',
        unsafe_allow_html=True,
    )

    tab_med, tab_dm = st.tabs(["💊 Médicament", "🩺 Dispositif Médical"])

    with tab_med:
        col_opts, col_search = st.columns([1, 2], gap="large")
        with col_opts:
            section_header("Critère de recherche")
            option = st.radio("Rechercher par :", ["Dénomination", "Code CIS", "CIP13"],
                              label_visibility="collapsed")
        with col_search:
            section_header("Sélection")
            if option == "Code CIS":
                values, col_filter = sorted(df["Code CIS"].dropna().unique()), "Code CIS"
            elif option == "CIP13":
                values, col_filter = sorted(df["CIP13"].dropna().unique()), "CIP13"
            else:
                values, col_filter = (
                    sorted(df["Dénomination du médicament"].dropna().unique()),
                    "Dénomination du médicament",
                )
            search_value = st.selectbox(f"Sélectionner ({len(values)} disponibles) :", values)

        med_df = df[df[col_filter] == search_value]
        st.markdown("<hr class='thin'>", unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        with c1:
            kpi_card("Présentations", len(med_df))
        with c2:
            smr_col_found = next(
                (c for c in med_df.columns if "valeur" in c.lower() and "smr" in c.lower()), None
            )
            smr = (
                med_df[smr_col_found].dropna().values[0]
                if smr_col_found and not med_df[smr_col_found].dropna().empty
                else "–"
            )
            kpi_card("SMR", smr)
        with c3:
            asmr_col_found = next(
                (c for c in med_df.columns if "valeur" in c.lower() and "asmr" in c.lower()), None
            )
            asmr = (
                med_df[asmr_col_found].dropna().values[0]
                if asmr_col_found and not med_df[asmr_col_found].dropna().empty
                else "–"
            )
            kpi_card("ASMR", asmr)

        st.markdown("<hr class='thin'>", unsafe_allow_html=True)
        section_header("Données détaillées")
        st.dataframe(med_df, use_container_width=True, height=320)
        col_dl, _ = st.columns([1, 3])
        with col_dl:
            st.download_button(
                "📥 Exporter Excel",
                data=export_excel(med_df),
                file_name=f"medicament_{search_value}_{datetime.now().date()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

    with tab_dm:
        col_opts2, col_search2 = st.columns([1, 2], gap="large")
        with col_opts2:
            section_header("Critère de recherche")
            search_option = st.radio(
                "Rechercher par :", ["Nom du dispositif", "Code dossier HAS"],
                label_visibility="collapsed",
            )
        with col_search2:
            section_header("Sélection")
            if search_option == "Code dossier HAS":
                values_dm = sorted(df2["Code dossier"].dropna().astype(str).unique())
                col_dm = "Code dossier"
            else:
                values_dm = sorted(df2["Nom dispositif"].dropna().unique())
                col_dm = "Nom dispositif"
            search_dm = st.selectbox(f"Sélectionner ({len(values_dm)} disponibles) :", values_dm)

        dispo_df = (
            df2[df2[col_dm].astype(str) == search_dm]
            if search_option == "Code dossier HAS"
            else df2[df2[col_dm] == search_dm]
        )
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
                st.download_button(
                    "📥 Exporter Excel",
                    data=export_excel(dispo_df),
                    file_name=f"dispositif_{search_dm}_{datetime.now().date()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )


# ══════════════════════════════════════════════════════════════════════════════
# 11.  PAGE 2 — ANALYSE LABORATOIRE
# ══════════════════════════════════════════════════════════════════════════════
def page_laboratoire():
    st.markdown('<div class="page-title">🏢 Analyse Laboratoire</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Explorez le profil qualité d\'un groupe ou comparez deux groupes</div>',
        unsafe_allow_html=True,
    )

    groups = sorted(df3_enriched["groupe_racine"].dropna().unique())

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
                group_2 = st.selectbox(
                    "Comparer avec :", [g for g in groups if g != group_1],
                    label_visibility="collapsed",
                )
            else:
                st.selectbox("Comparer avec :", groups, disabled=True, label_visibility="collapsed")
                group_2 = None

    df_g1 = df3_enriched[df3_enriched["groupe_racine"] == group_1]
    df_g2 = df3_enriched[df3_enriched["groupe_racine"] == group_2] if compare_mode and group_2 else None

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    section_header("🔎 Filiales du groupe")

    groups_to_show = [group_1] + ([group_2] if compare_mode and group_2 else [])
    cols_exp = st.columns(len(groups_to_show), gap="large")
    for i, group in enumerate(groups_to_show):
        with cols_exp[i]:
            gdf = df3_enriched[df3_enriched["groupe_racine"] == group]
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
        with c1: kpi_card("Total", f"{total1} vs {total2}", delta=total1 - total2)
        with c2: kpi_card("💊 Médicaments", f"{nb_med1} vs {nb_med2}", delta=nb_med1 - nb_med2)
        with c3: kpi_card("🩺 Dispositifs", f"{nb_dm1} vs {nb_dm2}", delta=nb_dm1 - nb_dm2)
        with c4: kpi_card("% ASMR I-II", f"{taux1:.1f}% vs {taux2:.1f}%",
                          delta=round(taux1 - taux2, 1), delta_label="pts")

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    section_header("📊 Analyse qualitative")

    col_ind, _ = st.columns([2, 3])
    with col_ind:
        choix = st.radio("Indicateur :", ["SMR / SR", "ASMR / ASR"],
                         horizontal=True, label_visibility="collapsed")

    col_valeur = SMR_COL if choix == "SMR / SR" else ASMR_COL
    lbl_m  = "SMR"  if choix == "SMR / SR" else "ASMR"
    lbl_d  = "SR"   if choix == "SMR / SR" else "ASR"
    lmap_m = SMR_LABELS_SHORT  if choix == "SMR / SR" else ASMR_LABELS_SHORT
    lmap_d = SR_LABELS_SHORT   if choix == "SMR / SR" else ASR_LABELS_SHORT
    cmap_m = SMR_COLORS_SHORT  if choix == "SMR / SR" else ASMR_COLORS_SHORT
    cmap_d = SR_COLORS_SHORT   if choix == "SMR / SR" else ASR_COLORS_SHORT

    med_g1 = df_g1[df_g1["type_produit"] == "medicament"]
    dm_g1  = df_g1[df_g1["type_produit"] == "dispositif_medical"]

    if not compare_mode:
        col_left, col_right = st.columns(2, gap="large")
        with col_left:
            if not med_g1.empty:
                plot_pie(med_g1, col_valeur, f"{lbl_m} – Médicaments ({group_1})",
                         label_map=lmap_m, color_map=cmap_m)
            else:
                st.info("Aucun médicament pour ce groupe.")
        with col_right:
            if not dm_g1.empty:
                plot_pie(dm_g1, col_valeur, f"{lbl_d} – Dispositifs ({group_1})",
                         label_map=lmap_d, color_map=cmap_d)
            else:
                st.info("Aucun dispositif médical pour ce groupe.")
    else:
        med_g2 = df_g2[df_g2["type_produit"] == "medicament"]
        dm_g2  = df_g2[df_g2["type_produit"] == "dispositif_medical"]
        st.markdown(f"**Médicaments — {lbl_m}**")
        c1, c2 = st.columns(2, gap="large")
        with c1:
            if not med_g1.empty:
                plot_pie(med_g1, col_valeur, group_1, label_map=lmap_m, color_map=cmap_m)
        with c2:
            if not med_g2.empty:
                plot_pie(med_g2, col_valeur, group_2, label_map=lmap_m, color_map=cmap_m)
        st.markdown(f"**Dispositifs — {lbl_d}**")
        c3, c4 = st.columns(2, gap="large")
        with c3:
            if not dm_g1.empty:
                plot_pie(dm_g1, col_valeur, group_1, label_map=lmap_d, color_map=cmap_d)
        with c4:
            if not dm_g2.empty:
                plot_pie(dm_g2, col_valeur, group_2, label_map=lmap_d, color_map=cmap_d)

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    section_header("📥 Export")
    col_dl1, col_dl2, _ = st.columns([1, 1, 2])
    with col_dl1:
        st.download_button(
            f"📥 {group_1} (Excel)",
            data=export_excel(df_g1),
            file_name=f"export_{group_1}_{datetime.now().date()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    if compare_mode and df_g2 is not None:
        with col_dl2:
            st.download_button(
                f"📥 {group_2} (Excel)",
                data=export_excel(df_g2),
                file_name=f"export_{group_2}_{datetime.now().date()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )


# ══════════════════════════════════════════════════════════════════════════════
# 12.  PAGE 3 — CHIFFRE D'AFFAIRES
# ══════════════════════════════════════════════════════════════════════════════
def page_ca():
    st.markdown('<div class="page-title">💰 Chiffre d\'Affaires</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Ventilation du CA par médicament pour les laboratoires disponibles</div>',
        unsafe_allow_html=True,
    )
    st.info("ℹ️ Les données financières couvrent actuellement 10 groupes. "
            "D'autres pourront être ajoutées ultérieurement.")

    col_sel, _ = st.columns([2, 3])
    with col_sel:
        lab_name_ca = st.selectbox(
            "Choisir un laboratoire :",
            sorted(df1["Titulaire(s)"].dropna().unique()),
        )

    lab_ca_df = df1[df1["Titulaire(s)"] == lab_name_ca].copy()
    # Robustesse : on ne garde que les lignes avec Revenue_USD valide
    lab_ca_df = lab_ca_df.dropna(subset=["Revenue_USD"])
    lab_ca_df["Revenue_USD"] = pd.to_numeric(lab_ca_df["Revenue_USD"], errors="coerce")
    lab_ca_df = lab_ca_df.dropna(subset=["Revenue_USD"])

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    section_header("📌 Vue d'ensemble")

    if lab_ca_df.empty:
        st.warning("⚠️ Aucune donnée financière disponible pour ce laboratoire.")
        return

    total_ca = lab_ca_df["Revenue_USD"].sum()
    nb_meds  = lab_ca_df["Dénomination du médicament"].nunique()
    top_med  = lab_ca_df.loc[lab_ca_df["Revenue_USD"].idxmax(), "Dénomination du médicament"]

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
            x="Revenue_USD",
            y="Dénomination du médicament",
            orientation="h",
            color="Revenue_USD",
            color_continuous_scale="Blues",
            labels={"Revenue_USD": "CA (USD)", "Dénomination du médicament": ""},
        )
        fig_ca.update_coloraxes(showscale=False)
        fig_ca.update_layout(
            margin=dict(l=10, r=20, t=10, b=20), height=420, xaxis_tickformat="$,.0f"
        )
        st.plotly_chart(fig_ca, use_container_width=True)

    with col_pie:
        section_header("Poids dans le portefeuille")
        fig_p = px.pie(
            lab_ca_df,
            names="Dénomination du médicament",
            values="Revenue_USD",
            color_discrete_sequence=px.colors.qualitative.Set2,
            hole=0.4,
        )
        fig_p.update_traces(textposition="inside", textinfo="percent+label")
        fig_p.update_layout(
            margin=dict(l=10, r=10, t=10, b=60), height=420, showlegend=False
        )
        st.plotly_chart(fig_p, use_container_width=True)
    # ── Répartition SMR / ASMR pondérée par CA ───────────────────────────────
    # À insérer dans page_ca() après la section bar/pie existante,
    # avant la section "Profil SMR / ASMR du portefeuille"
    # ─────────────────────────────────────────────────────────────────────────

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    section_header("📊 Répartition SMR / ASMR pondérée par le CA")
    st.caption(
        "Chaque tranche représente la **part du chiffre d'affaires** "
        "portée par les médicaments de ce niveau SMR ou ASMR."
    )

    def pie_ca_weighted(df_ca: pd.DataFrame, col: str, label_map: dict,
                        color_map: dict, title: str, height: int = 380):
        """
        Camembert où chaque tranche = somme de Revenue_USD
        pour les médicaments d'un même niveau SMR/ASMR.
        """
        df_c = df_ca.copy()
        df_c["_label"] = (
            df_c[col]
            .fillna("Non renseigné")
            .astype(str)
            .str.strip()
            .map(lambda x: label_map.get(x, x))
        )

        # Agréger le CA par niveau
        agg = (
            df_c.groupby("_label")["Revenue_USD"]
            .sum()
            .reset_index()
            .rename(columns={"_label": "Niveau", "Revenue_USD": "CA (USD)"})
        )
        agg = agg[agg["CA (USD)"] > 0].sort_values("CA (USD)", ascending=False)

        if agg.empty:
            st.info("Aucune donnée disponible.")
            return

        color_seq = [color_map.get(n, "#cccccc") for n in agg["Niveau"]]

        fig = px.pie(
            agg,
            names="Niveau",
            values="CA (USD)",
            hole=0.4,
            title=title,
        )
        fig.update_traces(
            marker=dict(colors=color_seq),
            textposition="inside",
            textinfo="percent+label",
            hovertemplate="<b>%{label}</b><br>CA : $%{value:,.0f}<br>Part : %{percent}<extra></extra>",
        )
        fig.update_layout(
            margin=dict(t=50, b=20, l=20, r=160),
            height=height,
            showlegend=True,
            legend=dict(
                orientation="v", yanchor="middle", y=0.5, x=1.02, font=dict(size=11)
            ),
        )
        st.plotly_chart(fig, use_container_width=True)

        # Tableau détail
        agg["Part du CA"] = (agg["CA (USD)"] / agg["CA (USD)"].sum() * 100).round(1).astype(str) + "%"
        agg["CA (USD)"] = agg["CA (USD)"].apply(lambda x: f"${x:,.0f}")
        st.dataframe(agg, use_container_width=True, hide_index=True)

    # Vérifier que les colonnes SMR/ASMR existent dans df1
    smr_col_ca  = next((c for c in lab_ca_df.columns
                        if "valeur" in c.lower() and "smr" in c.lower()), None)
    asmr_col_ca = next((c for c in lab_ca_df.columns
                        if "valeur" in c.lower() and "asmr" in c.lower()), None)

    has_smr  = smr_col_ca  is not None and lab_ca_df[smr_col_ca].notna().any()
    has_asmr = asmr_col_ca is not None and lab_ca_df[asmr_col_ca].notna().any()

    if not has_smr and not has_asmr:
        st.info("ℹ️ Aucune donnée SMR/ASMR disponible pour ce laboratoire.")
    else:
        col_smr_pie, col_asmr_pie = st.columns(2, gap="large")

        with col_smr_pie:
            if has_smr:
                pie_ca_weighted(
                    lab_ca_df,
                    col=smr_col_ca,
                    label_map=SMR_LABELS_SHORT,
                    color_map=SMR_COLORS_SHORT,
                    title="SMR — Part du CA",
                )
            else:
                st.info("Aucune donnée SMR.")

        with col_asmr_pie:
            if has_asmr:
                pie_ca_weighted(
                    lab_ca_df,
                    col=asmr_col_ca,
                    label_map=ASMR_LABELS_SHORT,
                    color_map=ASMR_COLORS_SHORT,
                    title="ASMR — Part du CA",
                )
            else:
                st.info("Aucune donnée ASMR.")
    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    section_header("📋 Profil SMR / ASMR du portefeuille")
    cols_show = [c for c in [
        "Dénomination du médicament", "Valeur du SMR", "Libellé du SMR",
        "Valeur de l'ASMR", "Libellé de l'ASMR",
    ] if c in lab_ca_df.columns]
    st.dataframe(lab_ca_df[cols_show], use_container_width=True, height=280)

    col_dl, _ = st.columns([1, 3])
    with col_dl:
        st.download_button(
            "📥 Exporter Excel",
            data=export_excel(lab_ca_df),
            file_name=f"CA_{lab_name_ca}_{datetime.now().date()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )


# ══════════════════════════════════════════════════════════════════════════════
# 13.  PAGE 4 — PORTEFEUILLE
# ══════════════════════════════════════════════════════════════════════════════
def page_portefeuille():
    st.markdown('<div class="page-title">📁 Construction de Portefeuille</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Importez un fichier Excel (Titulaire(s) | Pondérations) '
        'et analysez la qualité du portefeuille</div>',
        unsafe_allow_html=True,
    )

    # ── Référentiel ────────────────────────────────────────────────────────────
    ref = (
        df3_enriched[["Titulaire(s)", "groupe_racine"]]
        .dropna(subset=["Titulaire(s)", "groupe_racine"])
        .drop_duplicates()
    )
    all_titulaires  = sorted(ref["Titulaire(s)"].unique())
    all_groupes     = sorted(ref["groupe_racine"].unique())
    set_titulaires  = set(all_titulaires)
    set_groupes     = set(all_groupes)

    # ── 1. Import Excel ────────────────────────────────────────────────────────
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
            st.error("❌ Le fichier est vide ou ne contient qu'une ligne d'en-tête.")
            st.stop()
        _headers = [str(c).strip() if c is not None else "" for c in _rows[0]]
        raw_import = pd.DataFrame(_rows[1:], columns=_headers)
    except Exception as e:
        st.error(f"❌ Impossible de lire le fichier : {e}")
        st.stop()

    if not {"Titulaire(s)", "Pondérations"}.issubset(set(raw_import.columns)):
        st.error(
            f"❌ Colonnes trouvées : `{raw_import.columns.tolist()}` — "
            "attendu : Titulaire(s) et Pondérations"
        )
        st.stop()

    raw_import = raw_import[["Titulaire(s)", "Pondérations"]].dropna()
    raw_import.columns = ["label_import", "poids"]
    raw_import["poids"] = pd.to_numeric(raw_import["poids"], errors="coerce").fillna(0)
    raw_import = raw_import[raw_import["poids"] > 0].reset_index(drop=True)

    if raw_import.empty:
        st.error("❌ Aucune pondération > 0 trouvée dans le fichier.")
        st.stop()

    # ── 2. Tableau de correspondance ───────────────────────────────────────────
    section_header("2️⃣ Correspondance Titulaire ↔ Groupe racine")
    st.caption(
        "Pour chaque entreprise importée, choisissez la correspondance la plus pertinente. "
        "Les scores indiquent la qualité du matching (🏢 exact, 🔶 approximatif, ❌ non trouvé). "
        "Quand aucune correspondance automatique n'existe, toutes les options du référentiel "
        "sont proposées pour une sélection manuelle."
    )

    resolved       = []
    unknown_labels = []
    fuzzy_labels   = []

    for _, row in raw_import.iterrows():
        label = row["label_import"]
        poids = row["poids"]

        c    = find_candidates(label, ref, set_titulaires, set_groupes, all_groupes)
        opts = build_selectbox_options(c, label, ref, all_groupes)

        badge_map = {
            "exact_tit": "✅ titulaire exact",
            "exact_grp": "✅ groupe exact",
            "fuzzy":     "🔶 approximatif",
            "aucun":     "❌ non trouvé",
        }
        badge = badge_map.get(c["match_type"], "")

        if c["match_type"] == "fuzzy":
            fuzzy_labels.append(label)
        if c["match_type"] == "aucun":
            unknown_labels.append(label)

        col_lbl, col_sel = st.columns([2, 4])
        with col_lbl:
            st.markdown(f"**{label}** &nbsp; `{poids}%` &nbsp; {badge}")
        with col_sel:
            # Désactiver les options "séparateur" (col_filter = None et description commence par ──)
            valid_indices = [
                i for i, o in enumerate(opts)
                if not (o[0] is None and o[2].startswith("──"))
            ]
            chosen_idx = st.selectbox(
                label=f"sel_{label}",
                options=valid_indices,
                format_func=lambda i, o=opts: o[i][2],
                key=f"sel_{label}",
                label_visibility="collapsed",
            )

        col_filter, val_filter, _ = opts[chosen_idx]

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

    # Rapport de couverture
    nb_importes = len(raw_import)
    nb_resolus  = len(resolved)
    nb_inconnus = len(set(unknown_labels))
    nb_fuzzy    = len(fuzzy_labels)
    pct_couvert = nb_resolus / nb_importes * 100 if nb_importes > 0 else 0

    st.markdown("---")
    st.markdown("**📊 Couverture de l'import**")
    cov1, cov2, cov3, cov4 = st.columns(4)
    with cov1: kpi_card("Entreprises importées",       nb_importes)
    with cov2: kpi_card("✅ Correspondances retenues",  nb_resolus)
    with cov3: kpi_card("❌ Exclues / non trouvées",    nb_inconnus)
    with cov4: kpi_card("📐 Couverture",                f"{pct_couvert:.1f}%")

    if nb_fuzzy:
        st.info(
            f"🔶 **{nb_fuzzy} correspondance(s) approximative(s)** — vérifiez les choix ci-dessus : "
            + ", ".join(f"`{l}`" for l in fuzzy_labels)
        )
    if unknown_labels:
        exclu_list = "  \n".join(f"- `{l}`" for l in set(unknown_labels))
        st.warning("⚠️ **" + str(nb_inconnus) + " entreprise(s) exclue(s) :\n" + exclu_list)

    if not resolved:
        st.error("❌ Aucune entreprise retenue. Vérifiez vos choix ci-dessus.")
        st.stop()

    # ── 3. Récapitulatif & normalisation ──────────────────────────────────────
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

    # ── 4. Construction du sous-dataframe portefeuille ─────────────────────────
    @st.cache_data(show_spinner=False)
    def build_portfolio(_df: pd.DataFrame, resolved_json: str) -> pd.DataFrame:
        """Cache stable : on sérialise resolved_list en JSON pour éviter
        les instabilités de hash sur les listes de dicts avec des floats."""
        import json
        resolved_list = json.loads(resolved_json)
        frames = []
        for r in resolved_list:
            sub = _df[_df[r["col_filter"]] == r["val_filter"]].copy()
            sub["__poids_norm__"] = r["poids_norm"]
            sub["__label__"]      = r["label_import"]
            frames.append(sub)
        return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

    import json
    resolved_list = resolved_df.to_dict("records")
    portfolio_df  = build_portfolio(
        df3_enriched,
        json.dumps(resolved_list, ensure_ascii=False, default=str),
    )

    if portfolio_df.empty:
        st.error("❌ Aucun produit trouvé pour ce portefeuille.")
        st.stop()

    meds = portfolio_df[portfolio_df["type_produit"] == "medicament"]
    dms  = portfolio_df[portfolio_df["type_produit"] == "dispositif_medical"]
    pct_meds = len(meds) / len(portfolio_df) * 100
    pct_dms  = len(dms)  / len(portfolio_df) * 100

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    section_header("📊 Aperçu global")
    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi_card("Total produits",   len(portfolio_df))
    with c2: kpi_card("💊 Médicaments",  f"{len(meds)} ({pct_meds:.0f}%)")
    with c3: kpi_card("🩺 Dispositifs",   f"{len(dms)} ({pct_dms:.0f}%)")
    with c4: kpi_card("Entités retenues", len(resolved_df))

    # ── 5. Calcul des profils pondérés ─────────────────────────────────────────
    def weighted_profile(sub_portfolio: pd.DataFrame, col: str,
                         order: list, r_list: list) -> pd.DataFrame:
        totals = {}
        total_poids_effectif = 0.0
        for r in r_list:
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

        result = pd.DataFrame(
            [(k, v / total_poids_effectif * 100) for k, v in totals.items()],
            columns=["Niveau", "Pourcentage (%)"],
        )
        order_map = {v: i for i, v in enumerate(order)}
        result["_ord"] = result["Niveau"].map(lambda x: order_map.get(x, 999))
        result = result.sort_values("_ord").drop(columns="_ord").reset_index(drop=True)
        result["Pourcentage (%)"] = result["Pourcentage (%)"].round(2)
        return result[result["Pourcentage (%)"] > 0]

    def make_pie(df_profile: pd.DataFrame, colors_map: dict, title: str,
                 legend_map=None, height: int = 380):
        if df_profile is None or df_profile.empty:
            st.info("Aucune donnée disponible pour ce graphique.")
            return
        df_p = df_profile.copy()
        df_p["Légende"] = df_p["Niveau"].map(lambda x: legend_map.get(x, x) if legend_map else x)
        color_seq = [colors_map.get(n, "#cccccc") for n in df_p["Niveau"]]
        fig = px.pie(df_p, values="Pourcentage (%)", names="Légende", hole=0.42, title=title)
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

    # ── 6. Camemberts SMR / SR ─────────────────────────────────────────────────
    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    section_header("5️⃣ Répartition qualitative pondérée")

    st.markdown("#### 💊 SMR — Médicaments &nbsp;|&nbsp; 🩺 SR — Dispositifs médicaux")
    st.caption(
        "Le **SMR** (Service Médical Rendu, HAS) et le **SR** (Service Rendu, CNEDiMTS) "
        "utilisent la même échelle qualitative mais s'appliquent à des populations distinctes."
    )

    smr_profile = weighted_profile(meds, "_smr_norm", SMR_ORDER, resolved_list)
    sr_profile  = weighted_profile(dms,  "_smr_norm", SR_ORDER,  resolved_list)

    col_smr, col_sr = st.columns(2, gap="large")
    with col_smr:
        if meds.empty:
            st.info("Aucun médicament dans ce portefeuille.")
        else:
            make_pie(smr_profile, SMR_COLORS,
                     f"SMR — Médicaments ({len(meds)} produits, {pct_meds:.0f}%)")
    with col_sr:
        if dms.empty:
            st.info("Aucun dispositif médical dans ce portefeuille.")
        else:
            make_pie(sr_profile, SR_COLORS,
                     f"SR — Dispositifs ({len(dms)} produits, {pct_dms:.0f}%)")

    col_t1, col_t2 = st.columns(2, gap="large")
    with col_t1:
        if not smr_profile.empty:
            st.dataframe(smr_profile, use_container_width=True, hide_index=True)
    with col_t2:
        if not sr_profile.empty:
            st.dataframe(sr_profile, use_container_width=True, hide_index=True)

    # ── 7. Camemberts ASMR / ASR ───────────────────────────────────────────────
    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("#### 💊 ASMR — Médicaments &nbsp;|&nbsp; 🩺 ASR — Dispositifs médicaux")
    st.caption(
        "**ASMR** (HAS) et **ASR** (CNEDiMTS) : même échelle I→V, commissions différentes. "
        "Les valeurs longues (`V. Absence d'amélioration`, etc.) sont identifiées comme ASR ; "
        "les valeurs courtes (`I`…`V`) sont attribuées selon le `type_produit`."
    )

    meds_asmr = portfolio_df[portfolio_df["_source_amr"] == "ASMR"]
    dms_asr   = portfolio_df[portfolio_df["_source_amr"] == "ASR"]

    asmr_profile = weighted_profile(meds_asmr, "_roman", ASMR_ORDER, resolved_list)
    asr_profile  = weighted_profile(dms_asr,   "_roman", ASR_ORDER,  resolved_list)

    col_asmr, col_asr = st.columns(2, gap="large")
    with col_asmr:
        if meds_asmr.empty:
            st.info("Aucune donnée ASMR dans ce portefeuille.")
        else:
            make_pie(asmr_profile, ASMR_COLORS,
                     f"ASMR — Médicaments ({len(meds_asmr)} évalués)",
                     legend_map=ASMR_LEGEND)
    with col_asr:
        if dms_asr.empty:
            st.info("Aucune donnée ASR dans ce portefeuille.")
        else:
            make_pie(asr_profile, ASR_COLORS,
                     f"ASR — Dispositifs ({len(dms_asr)} évalués)",
                     legend_map=ASMR_LEGEND)

    def enrich_profile_table(df_profile: pd.DataFrame, legend_map: dict) -> pd.DataFrame:
        if df_profile.empty:
            return df_profile
        df_profile = df_profile.copy()
        df_profile.insert(1, "Signification",
                          df_profile["Niveau"].map(lambda x: legend_map.get(x, x)))
        return df_profile

    col_t3, col_t4 = st.columns(2, gap="large")
    with col_t3:
        if not asmr_profile.empty:
            st.dataframe(enrich_profile_table(asmr_profile, ASMR_LEGEND),
                         use_container_width=True, hide_index=True)
    with col_t4:
        if not asr_profile.empty:
            st.dataframe(enrich_profile_table(asr_profile, ASMR_LEGEND),
                         use_container_width=True, hide_index=True)

    # ── 8. Export ──────────────────────────────────────────────────────────────
    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    section_header("6️⃣ Export")

    def profiles_to_excel(smr_p, sr_p, asmr_p, asr_p, legend_map) -> bytes:
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            for df_p, sheet in [(smr_p, "SMR"), (sr_p, "SR")]:
                if not df_p.empty:
                    df_p.to_excel(writer, sheet_name=sheet, index=False)
            for df_p, sheet in [(asmr_p, "ASMR"), (asr_p, "ASR")]:
                if not df_p.empty:
                    enrich_profile_table(df_p, legend_map).to_excel(
                        writer, sheet_name=sheet, index=False
                    )
        buf.seek(0)
        return buf.read()

    col_dl1, col_dl2, col_dl3, _ = st.columns([1, 1, 1, 1])
    export_cols = [c for c in portfolio_df.columns if not c.startswith("__") and not c.startswith("_")]

    with col_dl1:
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


# ══════════════════════════════════════════════════════════════════════════════
# 14.  ROUTEUR PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════
PAGES = {
    "🔎  Recherche Produit":   page_recherche,
    "🏢  Analyse Laboratoire": page_laboratoire,
    "💰  Chiffre d'Affaires":  page_ca,
    "📁  Portefeuille":        page_portefeuille,
}

PAGES[page]()




