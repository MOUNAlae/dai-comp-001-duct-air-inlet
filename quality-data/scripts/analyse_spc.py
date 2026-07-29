import csv
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

DOSSIER_DATASET = BASE_DIR / "dataset"
DOSSIER_RESULTATS = BASE_DIR / "results"

ENTREE = (
    DOSSIER_DATASET
    / "DAI_COMP_001_Dataset_Synthetique.csv"
)

SORTIE_INITIAL = (
    DOSSIER_RESULTATS
    / "DAI_COMP_001_SPC_INITIAL.csv"
)

SORTIE_AMELIORE = (
    DOSSIER_RESULTATS
    / "DAI_COMP_001_SPC_AMELIORE.csv"
)

SORTIE_SYNTHESE = (
    DOSSIER_RESULTATS
    / "DAI_COMP_001_SPC_Synthese.csv"
)

SCENARIOS = ["INITIAL", "AMELIORE"]

CARACTERISTIQUE = "PLANEITE_ENTREE_MM"

# Constantes des cartes I-MR pour une étendue mobile de 2 valeurs.
D2 = 1.128
D3 = 0.000
D4 = 3.267


# ============================================================
# FONCTIONS
# ============================================================

def nombre_fr(texte: str) -> float:
    """Convertit un nombre français en nombre Python."""

    return float(texte.replace(",", "."))


def decimal_fr(
    valeur: float,
    chiffres: int = 4,
) -> str:
    """Écrit un nombre avec une virgule décimale."""

    return f"{valeur:.{chiffres}f}".replace(".", ",")


def moyenne(valeurs: list[float]) -> float:
    """Calcule la moyenne d'une liste non vide."""

    if not valeurs:
        raise ValueError("Impossible de calculer une moyenne vide.")

    return sum(valeurs) / len(valeurs)


def exporter_csv(
    chemin: Path,
    colonnes: list[str],
    lignes: list[dict[str, object]],
) -> None:
    """Exporte les résultats au format CSV français."""

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


# ============================================================
# LECTURE ET CONTRÔLE DU DATASET
# ============================================================

if not ENTREE.exists():
    raise FileNotFoundError(
        f"Fichier introuvable : {ENTREE}"
    )

with ENTREE.open(
    mode="r",
    newline="",
    encoding="utf-8-sig",
) as fichier:

    lecteur = csv.DictReader(
        fichier,
        delimiter=";",
    )

    donnees = list(lecteur)
    colonnes_entree = lecteur.fieldnames or []


colonnes_obligatoires = {
    "ID_PIECE",
    "ORDRE_PRODUCTION",
    "SCENARIO",
    "DATE_FABRICATION",
    CARACTERISTIQUE,
}

colonnes_manquantes = (
    colonnes_obligatoires
    - set(colonnes_entree)
)

if colonnes_manquantes:
    raise ValueError(
        "Colonnes manquantes : "
        + ", ".join(sorted(colonnes_manquantes))
    )

if len(donnees) != 100:
    raise ValueError(
        f"100 pièces attendues, {len(donnees)} trouvées."
    )


# ============================================================
# ANALYSE SPC PAR SCÉNARIO
# ============================================================

resultats_scenarios: dict[
    str,
    list[dict[str, object]],
] = {}

lignes_synthese = []

for scenario in SCENARIOS:

    sous_ensemble = sorted(
        [
            ligne
            for ligne in donnees
            if ligne["SCENARIO"] == scenario
        ],
        key=lambda ligne: int(
            ligne["ORDRE_PRODUCTION"]
        ),
    )

    if len(sous_ensemble) != 50:
        raise ValueError(
            f"50 pièces attendues pour {scenario}, "
            f"{len(sous_ensemble)} trouvées."
        )

    valeurs = [
        nombre_fr(
            ligne[CARACTERISTIQUE]
        )
        for ligne in sous_ensemble
    ]

    etendues_mobiles = [
        abs(
            valeurs[index]
            - valeurs[index - 1]
        )
        for index in range(1, len(valeurs))
    ]

    centre_i = moyenne(valeurs)
    moyenne_mr = moyenne(etendues_mobiles)

    sigma_estime = moyenne_mr / D2

    lcl_i = centre_i - 3 * sigma_estime
    ucl_i = centre_i + 3 * sigma_estime

    lcl_mr = D3 * moyenne_mr
    ucl_mr = D4 * moyenne_mr

    lignes_points = []

    alertes_i = 0
    alertes_mr = 0

    for index, ligne in enumerate(
        sous_ensemble,
        start=1,
    ):

        mesure = valeurs[index - 1]

        hors_controle_i = (
            mesure < lcl_i
            or mesure > ucl_i
        )

        if hors_controle_i:
            alertes_i += 1

        if index == 1:
            mr = None
            hors_controle_mr = False

        else:
            mr = etendues_mobiles[index - 2]

            hors_controle_mr = (
                mr < lcl_mr
                or mr > ucl_mr
            )

            if hors_controle_mr:
                alertes_mr += 1

        lignes_points.append(
            {
                "POINT": index,
                "ID_PIECE": ligne["ID_PIECE"],
                "ORDRE_PRODUCTION": (
                    ligne["ORDRE_PRODUCTION"]
                ),
                "DATE_FABRICATION": (
                    ligne["DATE_FABRICATION"]
                ),
                "SCENARIO": scenario,
                "PLANEITE_ENTREE_MM": decimal_fr(
                    mesure,
                    2,
                ),
                "CL_I_MM": decimal_fr(
                    centre_i,
                    4,
                ),
                "UCL_I_MM": decimal_fr(
                    ucl_i,
                    4,
                ),
                "LCL_I_MM": decimal_fr(
                    lcl_i,
                    4,
                ),
                "ALERTE_I": (
                    "HORS CONTROLE"
                    if hors_controle_i
                    else "OK"
                ),
                "MR_MM": (
                    ""
                    if mr is None
                    else decimal_fr(mr, 2)
                ),
                "CL_MR_MM": decimal_fr(
                    moyenne_mr,
                    4,
                ),
                "UCL_MR_MM": decimal_fr(
                    ucl_mr,
                    4,
                ),
                "LCL_MR_MM": decimal_fr(
                    lcl_mr,
                    4,
                ),
                "ALERTE_MR": (
                    ""
                    if mr is None
                    else (
                        "HORS CONTROLE"
                        if hors_controle_mr
                        else "OK"
                    )
                ),
            }
        )

    decision = (
        "PROCEDE STABLE"
        if alertes_i == 0 and alertes_mr == 0
        else "PROCEDE INSTABLE"
    )

    lignes_synthese.append(
        {
            "SCENARIO": scenario,
            "NOMBRE_PIECES": len(valeurs),
            "MOYENNE_I_MM": decimal_fr(
                centre_i,
                4,
            ),
            "MOYENNE_MR_MM": decimal_fr(
                moyenne_mr,
                4,
            ),
            "SIGMA_ESTIME_MM": decimal_fr(
                sigma_estime,
                4,
            ),
            "LCL_I_MM": decimal_fr(
                lcl_i,
                4,
            ),
            "UCL_I_MM": decimal_fr(
                ucl_i,
                4,
            ),
            "LCL_MR_MM": decimal_fr(
                lcl_mr,
                4,
            ),
            "UCL_MR_MM": decimal_fr(
                ucl_mr,
                4,
            ),
            "NB_ALERTES_I": alertes_i,
            "NB_ALERTES_MR": alertes_mr,
            "DECISION_SPC": decision,
            "TYPE_DONNEES": "SYNTHETIQUES",
        }
    )

    resultats_scenarios[scenario] = lignes_points


# ============================================================
# CONTRÔLES FINAUX
# ============================================================

if len(resultats_scenarios["INITIAL"]) != 50:
    raise ValueError(
        "La table INITIAL doit contenir 50 points."
    )

if len(resultats_scenarios["AMELIORE"]) != 50:
    raise ValueError(
        "La table AMELIORE doit contenir 50 points."
    )


# ============================================================
# EXPORTS
# ============================================================

DOSSIER_RESULTATS.mkdir(
    parents=True,
    exist_ok=True,
)

colonnes_points = [
    "POINT",
    "ID_PIECE",
    "ORDRE_PRODUCTION",
    "DATE_FABRICATION",
    "SCENARIO",
    "PLANEITE_ENTREE_MM",
    "CL_I_MM",
    "UCL_I_MM",
    "LCL_I_MM",
    "ALERTE_I",
    "MR_MM",
    "CL_MR_MM",
    "UCL_MR_MM",
    "LCL_MR_MM",
    "ALERTE_MR",
]

exporter_csv(
    SORTIE_INITIAL,
    colonnes_points,
    resultats_scenarios["INITIAL"],
)

exporter_csv(
    SORTIE_AMELIORE,
    colonnes_points,
    resultats_scenarios["AMELIORE"],
)

exporter_csv(
    SORTIE_SYNTHESE,
    [
        "SCENARIO",
        "NOMBRE_PIECES",
        "MOYENNE_I_MM",
        "MOYENNE_MR_MM",
        "SIGMA_ESTIME_MM",
        "LCL_I_MM",
        "UCL_I_MM",
        "LCL_MR_MM",
        "UCL_MR_MM",
        "NB_ALERTES_I",
        "NB_ALERTES_MR",
        "DECISION_SPC",
        "TYPE_DONNEES",
    ],
    lignes_synthese,
)


# ============================================================
# AFFICHAGE TERMINAL
# ============================================================

print()
print("ANALYSE SPC JOUR 62 TERMINÉE")

for ligne in lignes_synthese:

    print()
    print(f"SCÉNARIO : {ligne['SCENARIO']}")
    print(
        f"Moyenne I : "
        f"{ligne['MOYENNE_I_MM']} mm"
    )
    print(
        f"Moyenne MR : "
        f"{ligne['MOYENNE_MR_MM']} mm"
    )
    print(
        f"Limites I : "
        f"[{ligne['LCL_I_MM']} ; "
        f"{ligne['UCL_I_MM']}] mm"
    )
    print(
        f"UCL MR : "
        f"{ligne['UCL_MR_MM']} mm"
    )
    print(
        f"Alertes I : "
        f"{ligne['NB_ALERTES_I']}"
    )
    print(
        f"Alertes MR : "
        f"{ligne['NB_ALERTES_MR']}"
    )
    print(
        f"Décision : "
        f"{ligne['DECISION_SPC']}"
    )

print()
print(f"Fichier créé : {SORTIE_INITIAL}")
print(f"Fichier créé : {SORTIE_AMELIORE}")
print(f"Fichier créé : {SORTIE_SYNTHESE}")