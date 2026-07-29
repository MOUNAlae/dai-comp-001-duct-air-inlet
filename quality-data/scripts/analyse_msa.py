import csv
import math
import random
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

SEED_MESURES = 202661
SEED_ORDRES = 202662

BASE_DIR = Path(__file__).resolve().parents[1]

DOSSIER_RESULTATS = BASE_DIR / "results"

SORTIE_MESURES = (
    DOSSIER_RESULTATS
    / "DAI_COMP_001_MSA_Mesures.csv"
)

SORTIE_ANOVA = (
    DOSSIER_RESULTATS
    / "DAI_COMP_001_MSA_ANOVA.csv"
)

SORTIE_COMPOSANTES = (
    DOSSIER_RESULTATS
    / "DAI_COMP_001_MSA_Composantes.csv"
)

SORTIE_SYNTHESE = (
    DOSSIER_RESULTATS
    / "DAI_COMP_001_MSA_Synthese.csv"
)

SORTIE_MOYENNES = (
    DOSSIER_RESULTATS
    / "DAI_COMP_001_MSA_Moyennes.csv"
)

PIECES = [
    "P01", "P02", "P03", "P04", "P05",
    "P06", "P07", "P08", "P09", "P10",
]

VALEURS_REFERENCE_MM = {
    "P01": 0.16,
    "P02": 0.19,
    "P03": 0.23,
    "P04": 0.26,
    "P05": 0.29,
    "P06": 0.32,
    "P07": 0.35,
    "P08": 0.38,
    "P09": 0.41,
    "P10": 0.45,
}

OPERATEURS = ["A", "B", "C"]
REPETITIONS = [1, 2]

BIAIS_OPERATEUR_MM = {
    "A": -0.003,
    "B": 0.002,
    "C": 0.001,
}

LARGEUR_TOLERANCE_MM = 0.50


# ============================================================
# FONCTIONS
# ============================================================

def decimal_fr(
    valeur: float,
    chiffres: int = 4,
) -> str:
    return f"{valeur:.{chiffres}f}".replace(".", ",")


def moyenne(valeurs: list[float]) -> float:
    if not valeurs:
        raise ValueError("Liste vide.")
    return sum(valeurs) / len(valeurs)


def exporter_csv(
    chemin: Path,
    colonnes: list[str],
    lignes: list[dict[str, object]],
) -> None:
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
# GÉNÉRATION DES MESURES
# ============================================================

rng_mesures = random.Random(SEED_MESURES)
rng_ordres = random.Random(SEED_ORDRES)

effets_interaction = {}

for piece in PIECES:
    for operateur in OPERATEURS:
        effets_interaction[(piece, operateur)] = (
            rng_mesures.gauss(0.0, 0.003)
        )

mesures = {}

for piece in PIECES:
    reference = VALEURS_REFERENCE_MM[piece]

    for operateur in OPERATEURS:
        interaction = effets_interaction[(piece, operateur)]

        for repetition in REPETITIONS:
            bruit = rng_mesures.gauss(0.0, 0.006)

            valeur = (
                reference
                + BIAIS_OPERATEUR_MM[operateur]
                + interaction
                + bruit
            )

            # Résolution pédagogique : 0,01 mm.
            mesures[(piece, operateur, repetition)] = round(
                valeur,
                2,
            )


# ============================================================
# ORDRES ALÉATOIRES DES SIX SÉRIES
# ============================================================

ordres = {}
ordres_utilises = set()

for operateur in OPERATEURS:
    for repetition in REPETITIONS:
        ordre = PIECES.copy()
        rng_ordres.shuffle(ordre)

        while tuple(ordre) in ordres_utilises:
            rng_ordres.shuffle(ordre)

        ordres_utilises.add(tuple(ordre))
        ordres[(operateur, repetition)] = ordre

if len(ordres_utilises) != 6:
    raise ValueError(
        "Les six ordres de mesure doivent être différents."
    )


# ============================================================
# TABLE DES 60 MESURES
# ============================================================

lignes_mesures = []
numero_serie = 0

for operateur in OPERATEURS:
    for repetition in REPETITIONS:
        numero_serie += 1

        for position, piece in enumerate(
            ordres[(operateur, repetition)],
            start=1,
        ):
            lignes_mesures.append(
                {
                    "SERIE": f"S{numero_serie}",
                    "OPERATEUR": operateur,
                    "REPETITION": repetition,
                    "POSITION_ORDRE": position,
                    "PIECE": piece,
                    "VALEUR_REFERENCE_MM": decimal_fr(
                        VALEURS_REFERENCE_MM[piece],
                        2,
                    ),
                    "MESURE_PLANEITE_MM": decimal_fr(
                        mesures[
                            (piece, operateur, repetition)
                        ],
                        2,
                    ),
                    "TYPE_DONNEE": "SYNTHETIQUE",
                }
            )

if len(lignes_mesures) != 60:
    raise ValueError(
        f"60 mesures attendues, "
        f"{len(lignes_mesures)} générées."
    )


# ============================================================
# ANOVA CROISÉE
# ============================================================

p = len(PIECES)
o = len(OPERATEURS)
r = len(REPETITIONS)
n = p * o * r

toutes_mesures = [
    mesures[(piece, operateur, repetition)]
    for piece in PIECES
    for operateur in OPERATEURS
    for repetition in REPETITIONS
]

moyenne_generale = moyenne(toutes_mesures)

moyennes_piece = {
    piece: moyenne(
        [
            mesures[(piece, operateur, repetition)]
            for operateur in OPERATEURS
            for repetition in REPETITIONS
        ]
    )
    for piece in PIECES
}

moyennes_operateur = {
    operateur: moyenne(
        [
            mesures[(piece, operateur, repetition)]
            for piece in PIECES
            for repetition in REPETITIONS
        ]
    )
    for operateur in OPERATEURS
}

moyennes_cellule = {
    (piece, operateur): moyenne(
        [
            mesures[(piece, operateur, repetition)]
            for repetition in REPETITIONS
        ]
    )
    for piece in PIECES
    for operateur in OPERATEURS
}

ss_piece = (
    o
    * r
    * sum(
        (
            moyennes_piece[piece]
            - moyenne_generale
        ) ** 2
        for piece in PIECES
    )
)

ss_operateur = (
    p
    * r
    * sum(
        (
            moyennes_operateur[operateur]
            - moyenne_generale
        ) ** 2
        for operateur in OPERATEURS
    )
)

ss_interaction = (
    r
    * sum(
        (
            moyennes_cellule[(piece, operateur)]
            - moyennes_piece[piece]
            - moyennes_operateur[operateur]
            + moyenne_generale
        ) ** 2
        for piece in PIECES
        for operateur in OPERATEURS
    )
)

ss_repetabilite = sum(
    (
        mesures[(piece, operateur, repetition)]
        - moyennes_cellule[(piece, operateur)]
    ) ** 2
    for piece in PIECES
    for operateur in OPERATEURS
    for repetition in REPETITIONS
)

ss_total = sum(
    (valeur - moyenne_generale) ** 2
    for valeur in toutes_mesures
)

df_piece = p - 1
df_operateur = o - 1
df_interaction = (p - 1) * (o - 1)
df_repetabilite = p * o * (r - 1)
df_total = n - 1

ms_piece = ss_piece / df_piece
ms_operateur = ss_operateur / df_operateur
ms_interaction = ss_interaction / df_interaction
ms_repetabilite = ss_repetabilite / df_repetabilite

f_piece = ms_piece / ms_interaction
f_operateur = ms_operateur / ms_interaction
f_interaction = ms_interaction / ms_repetabilite

somme_decomposee = (
    ss_piece
    + ss_operateur
    + ss_interaction
    + ss_repetabilite
)

if not math.isclose(
    somme_decomposee,
    ss_total,
    rel_tol=1e-9,
    abs_tol=1e-9,
):
    raise ValueError(
        "Erreur dans la décomposition ANOVA."
    )

lignes_anova = [
    {
        "SOURCE": "PIECE",
        "SOMME_CARRES_SS": decimal_fr(ss_piece, 8),
        "DEGRES_LIBERTE_DF": df_piece,
        "CARRE_MOYEN_MS": decimal_fr(ms_piece, 8),
        "F": decimal_fr(f_piece, 4),
    },
    {
        "SOURCE": "OPERATEUR",
        "SOMME_CARRES_SS": decimal_fr(ss_operateur, 8),
        "DEGRES_LIBERTE_DF": df_operateur,
        "CARRE_MOYEN_MS": decimal_fr(ms_operateur, 8),
        "F": decimal_fr(f_operateur, 4),
    },
    {
        "SOURCE": "PIECE_X_OPERATEUR",
        "SOMME_CARRES_SS": decimal_fr(ss_interaction, 8),
        "DEGRES_LIBERTE_DF": df_interaction,
        "CARRE_MOYEN_MS": decimal_fr(
            ms_interaction,
            8,
        ),
        "F": decimal_fr(f_interaction, 4),
    },
    {
        "SOURCE": "REPETABILITE",
        "SOMME_CARRES_SS": decimal_fr(
            ss_repetabilite,
            8,
        ),
        "DEGRES_LIBERTE_DF": df_repetabilite,
        "CARRE_MOYEN_MS": decimal_fr(
            ms_repetabilite,
            8,
        ),
        "F": "",
    },
    {
        "SOURCE": "TOTAL",
        "SOMME_CARRES_SS": decimal_fr(ss_total, 8),
        "DEGRES_LIBERTE_DF": df_total,
        "CARRE_MOYEN_MS": "",
        "F": "",
    },
]


# ============================================================
# COMPOSANTES DE VARIATION
# ============================================================

variance_repetabilite = ms_repetabilite

variance_interaction = max(
    (ms_interaction - ms_repetabilite) / r,
    0.0,
)

variance_operateur = max(
    (ms_operateur - ms_interaction) / (p * r),
    0.0,
)

variance_piece = max(
    (ms_piece - ms_interaction) / (o * r),
    0.0,
)

variance_reproductibilite = (
    variance_operateur
    + variance_interaction
)

variance_grr = (
    variance_repetabilite
    + variance_reproductibilite
)

variance_totale = (
    variance_grr
    + variance_piece
)

sigma_total = math.sqrt(variance_totale)

composantes = [
    ("REPETABILITE_EV", variance_repetabilite),
    ("OPERATEUR", variance_operateur),
    (
        "INTERACTION_PIECE_OPERATEUR",
        variance_interaction,
    ),
    (
        "REPRODUCTIBILITE_AV",
        variance_reproductibilite,
    ),
    ("GAGE_RR_TOTAL", variance_grr),
    ("PIECE_A_PIECE_PV", variance_piece),
    ("VARIATION_TOTALE_TV", variance_totale),
]

lignes_composantes = []

for source, variance in composantes:
    sigma = math.sqrt(max(variance, 0.0))

    contribution = (
        100 * variance / variance_totale
        if variance_totale > 0
        else 0
    )

    study_variation = (
        100 * sigma / sigma_total
        if sigma_total > 0
        else 0
    )

    lignes_composantes.append(
        {
            "SOURCE": source,
            "VARIANCE": decimal_fr(variance, 8),
            "ECART_TYPE_SIGMA": decimal_fr(
                sigma,
                6,
            ),
            "VARIATION_ETUDE_6_SIGMA_MM": decimal_fr(
                6 * sigma,
                6,
            ),
            "CONTRIBUTION_PCT": decimal_fr(
                contribution,
                2,
            ),
            "STUDY_VARIATION_PCT": decimal_fr(
                study_variation,
                2,
            ),
        }
    )


# ============================================================
# SYNTHÈSE ET DÉCISION
# ============================================================

sigma_grr = math.sqrt(variance_grr)
sigma_piece = math.sqrt(variance_piece)

pourcentage_grr_etude = (
    100 * sigma_grr / sigma_total
)

pourcentage_grr_tolerance = (
    100
    * (6 * sigma_grr)
    / LARGEUR_TOLERANCE_MM
)

ndc = math.floor(
    1.41 * sigma_piece / sigma_grr
)

if pourcentage_grr_etude < 10 and ndc >= 5:
    decision = "SYSTEME ACCEPTABLE"
    autorisation = "OUI"

elif pourcentage_grr_etude <= 30 and ndc >= 5:
    decision = "ACCEPTABLE SOUS CONDITIONS"
    autorisation = "SOUS CONDITIONS"

else:
    decision = "SYSTEME NON ACCEPTABLE"
    autorisation = "NON"

lignes_synthese = [
    {
        "INDICATEUR": "CARACTERISTIQUE",
        "VALEUR": "PLANEITE_BRIDE_ENTREE",
        "UNITE": "mm",
        "INTERPRETATION": "CTQ-01",
    },
    {
        "INDICATEUR": "TYPE_ETUDE",
        "VALEUR": "GAGE_RR_CROISE_ANOVA",
        "UNITE": "-",
        "INTERPRETATION": (
            "10 pièces x 3 opérateurs x 2 répétitions"
        ),
    },
    {
        "INDICATEUR": "NOMBRE_MESURES",
        "VALEUR": 60,
        "UNITE": "mesures",
        "INTERPRETATION": "Plan équilibré",
    },
    {
        "INDICATEUR": "POURCENTAGE_GRR_STUDY",
        "VALEUR": decimal_fr(
            pourcentage_grr_etude,
            2,
        ),
        "UNITE": "%",
        "INTERPRETATION": "< 10 % : acceptable",
    },
    {
        "INDICATEUR": "POURCENTAGE_GRR_TOLERANCE",
        "VALEUR": decimal_fr(
            pourcentage_grr_tolerance,
            2,
        ),
        "UNITE": "%",
        "INTERPRETATION": (
            "Indicateur complémentaire, "
            "spécification unilatérale"
        ),
    },
    {
        "INDICATEUR": "NDC",
        "VALEUR": ndc,
        "UNITE": "catégories",
        "INTERPRETATION": "Minimum attendu : 5",
    },
    {
        "INDICATEUR": "DECISION_MSA",
        "VALEUR": decision,
        "UNITE": "-",
        "INTERPRETATION": "Décision pédagogique",
    },
    {
        "INDICATEUR": "AUTORISATION_SPC_CAPABILITE",
        "VALEUR": autorisation,
        "UNITE": "-",
        "INTERPRETATION": (
            "Utilisation autorisée pour la suite pédagogique"
        ),
    },
    {
        "INDICATEUR": "TYPE_DONNEES",
        "VALEUR": "SYNTHETIQUES",
        "UNITE": "-",
        "INTERPRETATION": (
            "Aucune validation industrielle revendiquée"
        ),
    },
]


# ============================================================
# MOYENNES PAR PIÈCE ET OPÉRATEUR
# ============================================================

lignes_moyennes = []

for piece in PIECES:
    moyenne_a = moyenne(
        [
            mesures[(piece, "A", repetition)]
            for repetition in REPETITIONS
        ]
    )

    moyenne_b = moyenne(
        [
            mesures[(piece, "B", repetition)]
            for repetition in REPETITIONS
        ]
    )

    moyenne_c = moyenne(
        [
            mesures[(piece, "C", repetition)]
            for repetition in REPETITIONS
        ]
    )

    lignes_moyennes.append(
        {
            "PIECE": piece,
            "REFERENCE_MM": decimal_fr(
                VALEURS_REFERENCE_MM[piece],
                2,
            ),
            "MOYENNE_A_MM": decimal_fr(moyenne_a, 3),
            "MOYENNE_B_MM": decimal_fr(moyenne_b, 3),
            "MOYENNE_C_MM": decimal_fr(moyenne_c, 3),
            "MOYENNE_PIECE_MM": decimal_fr(
                moyennes_piece[piece],
                3,
            ),
        }
    )


# ============================================================
# EXPORTS
# ============================================================

DOSSIER_RESULTATS.mkdir(
    parents=True,
    exist_ok=True,
)

exporter_csv(
    SORTIE_MESURES,
    [
        "SERIE",
        "OPERATEUR",
        "REPETITION",
        "POSITION_ORDRE",
        "PIECE",
        "VALEUR_REFERENCE_MM",
        "MESURE_PLANEITE_MM",
        "TYPE_DONNEE",
    ],
    lignes_mesures,
)

exporter_csv(
    SORTIE_ANOVA,
    [
        "SOURCE",
        "SOMME_CARRES_SS",
        "DEGRES_LIBERTE_DF",
        "CARRE_MOYEN_MS",
        "F",
    ],
    lignes_anova,
)

exporter_csv(
    SORTIE_COMPOSANTES,
    [
        "SOURCE",
        "VARIANCE",
        "ECART_TYPE_SIGMA",
        "VARIATION_ETUDE_6_SIGMA_MM",
        "CONTRIBUTION_PCT",
        "STUDY_VARIATION_PCT",
    ],
    lignes_composantes,
)

exporter_csv(
    SORTIE_SYNTHESE,
    [
        "INDICATEUR",
        "VALEUR",
        "UNITE",
        "INTERPRETATION",
    ],
    lignes_synthese,
)

exporter_csv(
    SORTIE_MOYENNES,
    [
        "PIECE",
        "REFERENCE_MM",
        "MOYENNE_A_MM",
        "MOYENNE_B_MM",
        "MOYENNE_C_MM",
        "MOYENNE_PIECE_MM",
    ],
    lignes_moyennes,
)


# ============================================================
# AFFICHAGE
# ============================================================

print()
print("ANALYSE MSA JOUR 61 TERMINÉE")
print(f"Mesures générées : {len(lignes_mesures)}")
print(
    "% Gage R&R Study Variation : "
    f"{pourcentage_grr_etude:.2f} %"
)
print(
    "% Gage R&R Tolérance : "
    f"{pourcentage_grr_tolerance:.2f} %"
)
print(f"ndc : {ndc}")
print(f"Décision : {decision}")
print(
    "Autorisation SPC / capabilité : "
    f"{autorisation}"
)