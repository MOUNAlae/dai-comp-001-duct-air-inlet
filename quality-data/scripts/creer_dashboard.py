import csv
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

DOSSIER_RESULTATS = BASE_DIR / "results"

ENTREE_CONFORMITE = (
    DOSSIER_RESULTATS
    / "DAI_COMP_001_Synthese_Conformite.csv"
)

ENTREE_PARETO = (
    DOSSIER_RESULTATS
    / "DAI_COMP_001_Pareto_Defauts.csv"
)

ENTREE_MSA = (
    DOSSIER_RESULTATS
    / "DAI_COMP_001_MSA_Synthese.csv"
)

ENTREE_SPC = (
    DOSSIER_RESULTATS
    / "DAI_COMP_001_SPC_Synthese.csv"
)

ENTREE_CAPABILITE = (
    DOSSIER_RESULTATS
    / "DAI_COMP_001_Capabilite_Synthese.csv"
)

SORTIE_DASHBOARD = (
    DOSSIER_RESULTATS
    / "DAI_COMP_001_Dashboard_KPI.csv"
)

SORTIE_SYNTHESE = (
    DOSSIER_RESULTATS
    / "DAI_COMP_001_Synthese_Finale.csv"
)


# ============================================================
# FONCTIONS
# ============================================================

def nombre_fr(texte: str) -> float:
    """Convertit un nombre français en float."""

    return float(str(texte).replace(",", "."))


def decimal_fr(
    valeur: float,
    chiffres: int = 2,
) -> str:
    """Formate un nombre avec une virgule décimale."""

    return f"{valeur:.{chiffres}f}".replace(".", ",")


def lire_csv(
    chemin: Path,
) -> list[dict[str, str]]:
    """Lit un fichier CSV français."""

    if not chemin.exists():
        raise FileNotFoundError(
            f"Fichier introuvable : {chemin}"
        )

    with chemin.open(
        mode="r",
        newline="",
        encoding="utf-8-sig",
    ) as fichier:

        lecteur = csv.DictReader(
            fichier,
            delimiter=";",
        )

        return list(lecteur)


def exporter_csv(
    chemin: Path,
    colonnes: list[str],
    lignes: list[dict[str, object]],
) -> None:
    """Exporte un CSV français."""

    with chemin.open(
        mode="w",
        newline="",
        encoding="utf-8-sig",
    ) as fichier:

        writer = csv.DictWriter(
            fichier,
            fieldnames=colonnes,
            delimiter=";",
            extrasaction="raise",
            lineterminator="\n",
        )

        writer.writeheader()
        writer.writerows(lignes)


def ligne_par_cle(
    lignes: list[dict[str, str]],
    colonne: str,
    valeur: str,
) -> dict[str, str]:
    """Recherche une ligne selon une valeur unique."""

    correspondances = [
        ligne
        for ligne in lignes
        if ligne.get(colonne) == valeur
    ]

    if len(correspondances) != 1:
        raise ValueError(
            f"Une ligne attendue pour "
            f"{colonne}={valeur}, "
            f"{len(correspondances)} trouvée(s)."
        )

    return correspondances[0]


# ============================================================
# LECTURE DES RÉSULTATS
# ============================================================

conformite = lire_csv(ENTREE_CONFORMITE)
pareto = lire_csv(ENTREE_PARETO)
msa = lire_csv(ENTREE_MSA)
spc = lire_csv(ENTREE_SPC)
capabilite = lire_csv(ENTREE_CAPABILITE)

conf_initial = ligne_par_cle(
    conformite,
    "SCENARIO",
    "INITIAL",
)

conf_ameliore = ligne_par_cle(
    conformite,
    "SCENARIO",
    "AMELIORE",
)

spc_initial = ligne_par_cle(
    spc,
    "SCENARIO",
    "INITIAL",
)

spc_ameliore = ligne_par_cle(
    spc,
    "SCENARIO",
    "AMELIORE",
)

cap_initial = ligne_par_cle(
    capabilite,
    "SCENARIO",
    "INITIAL",
)

cap_ameliore = ligne_par_cle(
    capabilite,
    "SCENARIO",
    "AMELIORE",
)


# ============================================================
# RÉSULTATS MSA
# ============================================================

msa_par_indicateur = {
    ligne["INDICATEUR"]: ligne["VALEUR"]
    for ligne in msa
}

indicateurs_msa_obligatoires = {
    "POURCENTAGE_GRR_STUDY",
    "POURCENTAGE_GRR_TOLERANCE",
    "NDC",
    "DECISION_MSA",
    "AUTORISATION_SPC_CAPABILITE",
}

manquants_msa = (
    indicateurs_msa_obligatoires
    - set(msa_par_indicateur)
)

if manquants_msa:
    raise ValueError(
        "Indicateurs MSA manquants : "
        + ", ".join(sorted(manquants_msa))
    )


# ============================================================
# TABLEAU DE BORD KPI
# ============================================================

def creer_ligne_dashboard(
    scenario: str,
    conformite_ligne: dict[str, str],
    spc_ligne: dict[str, str],
    cap_ligne: dict[str, str],
) -> dict[str, object]:

    alertes_total = (
        int(spc_ligne["NB_ALERTES_I"])
        + int(spc_ligne["NB_ALERTES_MR"])
    )

    return {
        "SCENARIO": scenario,
        "TAUX_CONFORMITE_PCT": (
            conformite_ligne["TAUX_CONFORMITE_PCT"]
        ),
        "TAUX_NON_CONFORMITE_PCT": (
            conformite_ligne["TAUX_NON_CONFORMITE_PCT"]
        ),
        "NB_PIECES_NON_CONFORMES": (
            conformite_ligne["PIECES_NON_CONFORMES"]
        ),
        "MOYENNE_PLANEITE_ENTREE_MM": (
            spc_ligne["MOYENNE_I_MM"]
        ),
        "CPK_UNILATERAL": (
            cap_ligne["CPK_UNILATERAL"]
        ),
        "PPK_UNILATERAL": (
            cap_ligne["PPK_UNILATERAL"]
        ),
        "SEUIL_CAPABILITE": (
            cap_ligne["SEUIL_CIBLE"]
        ),
        "NB_HORS_SPEC": (
            cap_ligne["NB_HORS_SPEC"]
        ),
        "NB_ALERTES_SPC_TOTAL": alertes_total,
        "STABILITE_SPC": (
            spc_ligne["DECISION_SPC"]
        ),
        "DECISION_CAPABILITE": (
            cap_ligne["DECISION_CAPABILITE"]
        ),
        "TYPE_DONNEES": "SYNTHETIQUES",
    }


lignes_dashboard = [
    creer_ligne_dashboard(
        "INITIAL",
        conf_initial,
        spc_initial,
        cap_initial,
    ),
    creer_ligne_dashboard(
        "AMELIORE",
        conf_ameliore,
        spc_ameliore,
        cap_ameliore,
    ),
]


# ============================================================
# CALCUL DES GAINS
# ============================================================

taux_conf_initial = nombre_fr(
    conf_initial["TAUX_CONFORMITE_PCT"]
)

taux_conf_ameliore = nombre_fr(
    conf_ameliore["TAUX_CONFORMITE_PCT"]
)

gain_conformite = (
    taux_conf_ameliore
    - taux_conf_initial
)

nb_nc_initial = int(
    conf_initial["PIECES_NON_CONFORMES"]
)

nb_nc_ameliore = int(
    conf_ameliore["PIECES_NON_CONFORMES"]
)

reduction_nc_pct = (
    100
    * (nb_nc_initial - nb_nc_ameliore)
    / nb_nc_initial
)

moyenne_initiale = nombre_fr(
    spc_initial["MOYENNE_I_MM"]
)

moyenne_amelioree = nombre_fr(
    spc_ameliore["MOYENNE_I_MM"]
)

reduction_planeite_pct = (
    100
    * (moyenne_initiale - moyenne_amelioree)
    / moyenne_initiale
)


# ============================================================
# PARETO
# ============================================================

if not pareto:
    raise ValueError(
        "Le fichier Pareto est vide."
    )

pareto_trie = sorted(
    pareto,
    key=lambda ligne: int(ligne["RANG"]),
)

defaut_1 = pareto_trie[0]
defaut_2 = pareto_trie[1]


# ============================================================
# SYNTHÈSE FINALE
# ============================================================

lignes_synthese = [
    {
        "SECTION": "PERFORMANCE",
        "INDICATEUR": "GAIN_CONFORMITE",
        "VALEUR": decimal_fr(
            gain_conformite,
            2,
        ),
        "UNITE": "points",
        "INTERPRETATION": (
            "Passage de 52 % à 94 % de pièces conformes."
        ),
    },
    {
        "SECTION": "PERFORMANCE",
        "INDICATEUR": "REDUCTION_PIECES_NON_CONFORMES",
        "VALEUR": decimal_fr(
            reduction_nc_pct,
            2,
        ),
        "UNITE": "%",
        "INTERPRETATION": (
            "Passage de 24 à 3 pièces non conformes."
        ),
    },
    {
        "SECTION": "PERFORMANCE",
        "INDICATEUR": "REDUCTION_MOYENNE_PLANEITE",
        "VALEUR": decimal_fr(
            reduction_planeite_pct,
            2,
        ),
        "UNITE": "%",
        "INTERPRETATION": (
            "Réduction de la moyenne de planéité d’entrée."
        ),
    },
    {
        "SECTION": "PARETO",
        "INDICATEUR": "DEFAUT_PRINCIPAL_1",
        "VALEUR": defaut_1["DEFAUT_PRINCIPAL"],
        "UNITE": "-",
        "INTERPRETATION": (
            f"{defaut_1['NOMBRE_PIECES']} pièces, "
            f"{defaut_1['POURCENTAGE_PCT']} % des NC."
        ),
    },
    {
        "SECTION": "PARETO",
        "INDICATEUR": "DEFAUT_PRINCIPAL_2",
        "VALEUR": defaut_2["DEFAUT_PRINCIPAL"],
        "UNITE": "-",
        "INTERPRETATION": (
            f"{defaut_2['NOMBRE_PIECES']} pièces, "
            f"cumul {defaut_2['CUMUL_PCT']} %."
        ),
    },
    {
        "SECTION": "MSA",
        "INDICATEUR": "POURCENTAGE_GRR_STUDY",
        "VALEUR": (
            msa_par_indicateur[
                "POURCENTAGE_GRR_STUDY"
            ]
        ),
        "UNITE": "%",
        "INTERPRETATION": (
            "Inférieur à 10 %, système de mesure acceptable."
        ),
    },
    {
        "SECTION": "MSA",
        "INDICATEUR": "POURCENTAGE_GRR_TOLERANCE",
        "VALEUR": (
            msa_par_indicateur[
                "POURCENTAGE_GRR_TOLERANCE"
            ]
        ),
        "UNITE": "%",
        "INTERPRETATION": (
            "Indicateur complémentaire unilatéral."
        ),
    },
    {
        "SECTION": "MSA",
        "INDICATEUR": "NDC",
        "VALEUR": msa_par_indicateur["NDC"],
        "UNITE": "catégories",
        "INTERPRETATION": (
            "Supérieur au minimum pédagogique de 5."
        ),
    },
    {
        "SECTION": "MSA",
        "INDICATEUR": "DECISION_MSA",
        "VALEUR": (
            msa_par_indicateur["DECISION_MSA"]
        ),
        "UNITE": "-",
        "INTERPRETATION": (
            "SPC et capabilité autorisés."
        ),
    },
    {
        "SECTION": "SPC",
        "INDICATEUR": "STABILITE_INITIAL",
        "VALEUR": spc_initial["DECISION_SPC"],
        "UNITE": "-",
        "INTERPRETATION": (
            "Deux alertes statistiques détectées."
        ),
    },
    {
        "SECTION": "SPC",
        "INDICATEUR": "STABILITE_AMELIORE",
        "VALEUR": spc_ameliore["DECISION_SPC"],
        "UNITE": "-",
        "INTERPRETATION": (
            "Aucune alerte sur les cartes I-MR."
        ),
    },
    {
        "SECTION": "CAPABILITE",
        "INDICATEUR": "CAPABILITE_INITIAL",
        "VALEUR": (
            cap_initial["DECISION_CAPABILITE"]
        ),
        "UNITE": "-",
        "INTERPRETATION": (
            "Indices indicatifs uniquement, procédé instable."
        ),
    },
    {
        "SECTION": "CAPABILITE",
        "INDICATEUR": "CAPABILITE_AMELIORE",
        "VALEUR": (
            cap_ameliore["DECISION_CAPABILITE"]
        ),
        "UNITE": "-",
        "INTERPRETATION": (
            "Cpk 1,59 et Ppk 1,79, supérieurs à 1,33."
        ),
    },
    {
        "SECTION": "CONCLUSION",
        "INDICATEUR": "RESULTAT_GLOBAL",
        "VALEUR": "AMELIORATION VALIDEE",
        "UNITE": "-",
        "INTERPRETATION": (
            "Le scénario amélioré est plus conforme, "
            "stable et capable dans le cadre pédagogique."
        ),
    },
    {
        "SECTION": "LIMITES",
        "INDICATEUR": "TYPE_DONNEES",
        "VALEUR": "SYNTHETIQUES",
        "UNITE": "-",
        "INTERPRETATION": (
            "Aucune validation industrielle ou aéronautique "
            "réelle n’est revendiquée."
        ),
    },
]


# ============================================================
# EXPORTS
# ============================================================

DOSSIER_RESULTATS.mkdir(
    parents=True,
    exist_ok=True,
)

exporter_csv(
    SORTIE_DASHBOARD,
    [
        "SCENARIO",
        "TAUX_CONFORMITE_PCT",
        "TAUX_NON_CONFORMITE_PCT",
        "NB_PIECES_NON_CONFORMES",
        "MOYENNE_PLANEITE_ENTREE_MM",
        "CPK_UNILATERAL",
        "PPK_UNILATERAL",
        "SEUIL_CAPABILITE",
        "NB_HORS_SPEC",
        "NB_ALERTES_SPC_TOTAL",
        "STABILITE_SPC",
        "DECISION_CAPABILITE",
        "TYPE_DONNEES",
    ],
    lignes_dashboard,
)

exporter_csv(
    SORTIE_SYNTHESE,
    [
        "SECTION",
        "INDICATEUR",
        "VALEUR",
        "UNITE",
        "INTERPRETATION",
    ],
    lignes_synthese,
)


# ============================================================
# AFFICHAGE TERMINAL
# ============================================================

print()
print("DASHBOARD JOUR 64 TERMINÉ")
print(
    f"Gain de conformité : "
    f"+{gain_conformite:.2f} points"
)
print(
    f"Réduction des pièces non conformes : "
    f"{reduction_nc_pct:.2f} %"
)
print(
    f"Réduction de la moyenne de planéité : "
    f"{reduction_planeite_pct:.2f} %"
)
print(
    f"MSA : "
    f"{msa_par_indicateur['DECISION_MSA']}"
)
print(
    f"SPC amélioré : "
    f"{spc_ameliore['DECISION_SPC']}"
)
print(
    f"Capabilité améliorée : "
    f"{cap_ameliore['DECISION_CAPABILITE']}"
)
print()
print(f"Fichier créé : {SORTIE_DASHBOARD}")
print(f"Fichier créé : {SORTIE_SYNTHESE}")