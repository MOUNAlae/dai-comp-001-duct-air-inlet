import csv
import math
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

DOSSIER_DATASET = BASE_DIR / "dataset"
DOSSIER_RESULTATS = BASE_DIR / "results"

ENTREE_DATASET = (
    DOSSIER_DATASET
    / "DAI_COMP_001_Dataset_Synthetique.csv"
)

ENTREE_SPC = (
    DOSSIER_RESULTATS
    / "DAI_COMP_001_SPC_Synthese.csv"
)

SORTIE = (
    DOSSIER_RESULTATS
    / "DAI_COMP_001_Capabilite_Synthese.csv"
)

CARACTERISTIQUE = "PLANEITE_ENTREE_MM"

SCENARIOS = ["INITIAL", "AMELIORE"]

USL_MM = 0.50
SEUIL_CAPABILITE = 1.33

# Constante d2 pour une étendue mobile de deux observations.
D2 = 1.128


# ============================================================
# FONCTIONS
# ============================================================

def nombre_fr(texte: str) -> float:
    """Convertit un nombre avec virgule en float."""

    return float(texte.replace(",", "."))


def decimal_fr(
    valeur: float,
    chiffres: int = 4,
) -> str:
    """Formate un nombre avec une virgule décimale."""

    return f"{valeur:.{chiffres}f}".replace(".", ",")


def moyenne(valeurs: list[float]) -> float:
    """Calcule la moyenne d'une liste non vide."""

    if not valeurs:
        raise ValueError("Liste vide.")

    return sum(valeurs) / len(valeurs)


def ecart_type_echantillon(
    valeurs: list[float],
) -> float:
    """Calcule l'écart-type global avec n - 1."""

    if len(valeurs) < 2:
        raise ValueError(
            "Au moins deux valeurs sont nécessaires."
        )

    centre = moyenne(valeurs)

    variance = sum(
        (valeur - centre) ** 2
        for valeur in valeurs
    ) / (len(valeurs) - 1)

    return math.sqrt(variance)


def exporter_csv(
    chemin: Path,
    colonnes: list[str],
    lignes: list[dict[str, object]],
) -> None:
    """Exporte un fichier CSV français."""

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
# LECTURE DU DATASET
# ============================================================

if not ENTREE_DATASET.exists():
    raise FileNotFoundError(
        f"Dataset introuvable : {ENTREE_DATASET}"
    )

with ENTREE_DATASET.open(
    mode="r",
    newline="",
    encoding="utf-8-sig",
) as fichier:

    lecteur = csv.DictReader(
        fichier,
        delimiter=";",
    )

    donnees = list(lecteur)
    colonnes_dataset = lecteur.fieldnames or []


colonnes_obligatoires = {
    "ID_PIECE",
    "ORDRE_PRODUCTION",
    "SCENARIO",
    CARACTERISTIQUE,
}

colonnes_manquantes = (
    colonnes_obligatoires
    - set(colonnes_dataset)
)

if colonnes_manquantes:
    raise ValueError(
        "Colonnes dataset manquantes : "
        + ", ".join(sorted(colonnes_manquantes))
    )

if len(donnees) != 100:
    raise ValueError(
        f"100 pièces attendues, {len(donnees)} trouvées."
    )


# ============================================================
# LECTURE DE LA DÉCISION SPC
# ============================================================

if not ENTREE_SPC.exists():
    raise FileNotFoundError(
        f"Synthèse SPC introuvable : {ENTREE_SPC}"
    )

with ENTREE_SPC.open(
    mode="r",
    newline="",
    encoding="utf-8-sig",
) as fichier:

    lecteur_spc = csv.DictReader(
        fichier,
        delimiter=";",
    )

    lignes_spc = list(lecteur_spc)


stabilite_spc = {
    ligne["SCENARIO"]: ligne["DECISION_SPC"]
    for ligne in lignes_spc
}

for scenario in SCENARIOS:

    if scenario not in stabilite_spc:
        raise ValueError(
            f"Décision SPC absente pour {scenario}."
        )


# ============================================================
# CAPABILITÉ UNILATÉRALE
# ============================================================

lignes_sortie = []

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

    centre = moyenne(valeurs)

    etendues_mobiles = [
        abs(
            valeurs[index]
            - valeurs[index - 1]
        )
        for index in range(1, len(valeurs))
    ]

    moyenne_mr = moyenne(etendues_mobiles)

    # Dispersion court terme issue de la carte I-MR.
    sigma_within = moyenne_mr / D2

    # Dispersion globale des 50 pièces.
    sigma_overall = ecart_type_echantillon(
        valeurs
    )

    if sigma_within <= 0 or sigma_overall <= 0:
        raise ValueError(
            f"Dispersion incorrecte pour {scenario}."
        )

    # Avec une seule limite supérieure :
    # Cpk unilatéral = Cpu.
    cpk_unilateral = (
        (USL_MM - centre)
        / (3 * sigma_within)
    )

    # Ppk unilatéral = Ppu.
    ppk_unilateral = (
        (USL_MM - centre)
        / (3 * sigma_overall)
    )

    nb_hors_spec = sum(
        1
        for valeur in valeurs
        if valeur > USL_MM
    )

    taux_hors_spec = (
        100 * nb_hors_spec / len(valeurs)
    )

    decision_spc = stabilite_spc[scenario]

    if decision_spc != "PROCEDE STABLE":

        decision_capabilite = (
            "NON INTERPRETABLE - PROCEDE INSTABLE"
        )

        interpretation = (
            "Indices indicatifs uniquement. "
            "La stabilité est obligatoire avant conclusion."
        )

    elif (
        cpk_unilateral >= SEUIL_CAPABILITE
        and ppk_unilateral >= SEUIL_CAPABILITE
    ):

        decision_capabilite = "PROCEDE CAPABLE"

        interpretation = (
            "Procédé stable et indices unilatéraux "
            "supérieurs ou égaux à 1,33."
        )

    else:

        decision_capabilite = "PROCEDE NON CAPABLE"

        interpretation = (
            "Procédé stable mais indice inférieur à 1,33."
        )

    lignes_sortie.append(
        {
            "SCENARIO": scenario,
            "CPK_UNILATERAL": decimal_fr(
                cpk_unilateral,
                2,
            ),
            "PPK_UNILATERAL": decimal_fr(
                ppk_unilateral,
                2,
            ),
            "SEUIL_CIBLE": decimal_fr(
                SEUIL_CAPABILITE,
                2,
            ),
            "STABILITE_SPC": decision_spc,
            "NOMBRE_PIECES": len(valeurs),
            "MOYENNE_MM": decimal_fr(
                centre,
                4,
            ),
            "SIGMA_WITHIN_MM": decimal_fr(
                sigma_within,
                4,
            ),
            "SIGMA_OVERALL_MM": decimal_fr(
                sigma_overall,
                4,
            ),
            "USL_MM": decimal_fr(
                USL_MM,
                2,
            ),
            "NB_HORS_SPEC": nb_hors_spec,
            "TAUX_HORS_SPEC_PCT": decimal_fr(
                taux_hors_spec,
                2,
            ),
            "DECISION_CAPABILITE": (
                decision_capabilite
            ),
            "CP_PP_BILATERAUX": "NON APPLICABLE",
            "INTERPRETATION": interpretation,
            "TYPE_DONNEES": "SYNTHETIQUES",
        }
    )


# ============================================================
# CONTRÔLES
# ============================================================

resultat_initial = lignes_sortie[0]
resultat_ameliore = lignes_sortie[1]

if resultat_initial["STABILITE_SPC"] != "PROCEDE INSTABLE":
    raise ValueError(
        "Le scénario INITIAL doit être instable."
    )

if resultat_ameliore["STABILITE_SPC"] != "PROCEDE STABLE":
    raise ValueError(
        "Le scénario AMELIORE doit être stable."
    )

if (
    resultat_ameliore["DECISION_CAPABILITE"]
    != "PROCEDE CAPABLE"
):
    raise ValueError(
        "Le scénario AMELIORE devrait être capable."
    )


# ============================================================
# EXPORT
# ============================================================

DOSSIER_RESULTATS.mkdir(
    parents=True,
    exist_ok=True,
)

exporter_csv(
    SORTIE,
    [
        "SCENARIO",
        "CPK_UNILATERAL",
        "PPK_UNILATERAL",
        "SEUIL_CIBLE",
        "STABILITE_SPC",
        "NOMBRE_PIECES",
        "MOYENNE_MM",
        "SIGMA_WITHIN_MM",
        "SIGMA_OVERALL_MM",
        "USL_MM",
        "NB_HORS_SPEC",
        "TAUX_HORS_SPEC_PCT",
        "DECISION_CAPABILITE",
        "CP_PP_BILATERAUX",
        "INTERPRETATION",
        "TYPE_DONNEES",
    ],
    lignes_sortie,
)


# ============================================================
# AFFICHAGE TERMINAL
# ============================================================

print()
print("ANALYSE DE CAPABILITÉ JOUR 63 TERMINÉE")
print(
    "Spécification : planéité entrée <= "
    f"{USL_MM:.2f} mm"
)
print(
    "Méthode : Cpk/Cpu et Ppk/Ppu unilatéraux"
)

for ligne in lignes_sortie:

    print()
    print(f"SCÉNARIO : {ligne['SCENARIO']}")
    print(
        f"Stabilité SPC : "
        f"{ligne['STABILITE_SPC']}"
    )
    print(
        f"Moyenne : "
        f"{ligne['MOYENNE_MM']} mm"
    )
    print(
        f"Cpk unilatéral : "
        f"{ligne['CPK_UNILATERAL']}"
    )
    print(
        f"Ppk unilatéral : "
        f"{ligne['PPK_UNILATERAL']}"
    )
    print(
        f"Hors spécification : "
        f"{ligne['NB_HORS_SPEC']}/"
        f"{ligne['NOMBRE_PIECES']}"
    )
    print(
        f"Décision : "
        f"{ligne['DECISION_CAPABILITE']}"
    )

print()
print(f"Fichier créé : {SORTIE}")