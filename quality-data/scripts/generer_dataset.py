import csv
import random
from datetime import date, timedelta
from pathlib import Path


# ============================================================
# CONFIGURATION GÉNÉRALE
# ============================================================

SEED = 202659
NB_PIECES = 100
NB_INITIAL = 50
DATE_DEBUT = date(2026, 1, 5)

BASE_DIR = Path(__file__).resolve().parents[1]

DOSSIER_DATASET = BASE_DIR / "dataset"

SORTIE = (
    DOSSIER_DATASET
    / "DAI_COMP_001_Dataset_Synthetique.csv"
)


# ============================================================
# STRUCTURE OFFICIELLE DU DATASET — 33 COLONNES
# ============================================================

COLONNES = [
    "ID_PIECE",
    "ORDRE_PRODUCTION",
    "SCENARIO",
    "DATE_FABRICATION",
    "ID_UPPER",
    "ID_LOWER",
    "LOT_PREIMPREGNE",
    "LOT_ADHESIF",
    "MOULE_UPPER",
    "MOULE_LOWER",
    "OPERATEUR_DRAPAGE",
    "OPERATEUR_ASSEMBLAGE",
    "CYCLE_CUISSON",
    "PRESSION_VIDE_ABS_MBAR",
    "TEMP_MAX_C",
    "TEMPS_MAINTIEN_MIN",
    "TEMP_DEMOULAGE_C",
    "RATIO_ADHESIF",
    "TEMPS_OUVERT_MIN",
    "EPAISSEUR_MOY_MM",
    "PLANEITE_ENTREE_MM",
    "PLANEITE_SORTIE_MM",
    "DIAMETRE_TROU_MOY_MM",
    "ECART_PROFIL_MAX_MM",
    "ECART_POSITION_TROUS_MAX_MM",
    "PRESSION_TEST_KPA",
    "DUREE_TEST_S",
    "TAUX_FUITE",
    "JOINT_CONTINU_CONFORME",
    "DEFAUT_PRINCIPAL",
    "NB_DEFAUTS",
    "STATUT_FINAL",
    "COMMENTAIRE",
]


# ============================================================
# FONCTIONS UTILITAIRES
# ============================================================

def borner(
    valeur: float,
    minimum: float,
    maximum: float,
) -> float:
    """Maintient une valeur entre une limite basse et haute."""
    return min(max(valeur, minimum), maximum)


def decimale_fr(
    valeur: float,
    chiffres: int = 2,
) -> str:
    """Transforme un nombre en texte avec une virgule décimale."""
    return f"{valeur:.{chiffres}f}".replace(".", ",")


def choisir_defaut_principal(
    defauts: list[str],
    pression_vide: float,
) -> str:
    """Détermine le défaut principal selon une règle de priorité."""

    if not defauts:
        return "AUCUN"

    # Une pression absolue élevée correspond à un vide moins efficace.
    if pression_vide > 110 and any(
        defaut in defauts
        for defaut in (
            "EPAISSEUR",
            "PLANEITE",
            "PROFIL",
        )
    ):
        return "VIDE_POROSITE"

    priorite = [
        "COLLAGE",
        "ETANCHEITE",
        "PLANEITE",
        "EPAISSEUR",
        "PERCAGE",
        "PROFIL",
    ]

    for defaut in priorite:
        if defaut in defauts:
            return defaut

    raise ValueError(
        f"Aucun défaut principal trouvé pour : {defauts}"
    )


# ============================================================
# GÉNÉRATION DES DONNÉES
# ============================================================

rng = random.Random(SEED)
lignes: list[dict[str, object]] = []

for i in range(1, NB_PIECES + 1):

    ameliore = i > NB_INITIAL

    scenario = (
        "AMELIORE"
        if ameliore
        else "INITIAL"
    )

    # --------------------------------------------------------
    # PARAMÈTRES DU PROCÉDÉ
    # --------------------------------------------------------

    if not ameliore:

        pression_vide = borner(
            rng.gauss(100, 13),
            70,
            130,
        )

        temp_max = borner(
            rng.gauss(121, 1.4),
            118,
            124,
        )

        maintien = borner(
            rng.gauss(92.5, 3.7),
            85,
            100,
        )

        temp_demoulage = borner(
            rng.gauss(60, 4.5),
            50,
            70,
        )

        ratio = borner(
            rng.gauss(1.00, 0.024),
            0.95,
            1.05,
        )

        temps_ouvert = borner(
            rng.gauss(32, 6),
            20,
            45,
        )

    else:

        pression_vide = borner(
            rng.gauss(75, 6),
            60,
            90,
        )

        temp_max = borner(
            rng.gauss(121, 0.45),
            120,
            122,
        )

        maintien = borner(
            rng.gauss(90, 1.0),
            88,
            92,
        )

        temp_demoulage = borner(
            rng.gauss(55, 2.0),
            50,
            60,
        )

        ratio = borner(
            rng.gauss(1.00, 0.009),
            0.98,
            1.02,
        )

        temps_ouvert = borner(
            rng.gauss(25, 2.2),
            20,
            30,
        )

    # --------------------------------------------------------
    # PÉNALITÉS LIÉES AUX PARAMÈTRES DU PROCÉDÉ
    # --------------------------------------------------------

    penalite_vide = max(
        0,
        (pression_vide - 85) / 45,
    )

    penalite_temp = (
        abs(temp_max - 121) / 3
    )

    penalite_demoulage = max(
        0,
        (temp_demoulage - 55) / 15,
    )

    penalite_ratio = (
        abs(ratio - 1.00) / 0.05
    )

    penalite_temps_ouvert = max(
        0,
        (temps_ouvert - 28) / 17,
    )

    # --------------------------------------------------------
    # CARACTÉRISTIQUES PRODUIT — SCÉNARIO INITIAL
    # --------------------------------------------------------

    if not ameliore:

        epaisseur = (
            2
            + rng.gauss(0, 0.085)
            + 0.05
            * penalite_vide
            * rng.choice([-1, 1])
        )

        planeite_entree = (
            0.30
            + 0.13 * penalite_vide
            + 0.10 * penalite_demoulage
            + rng.gauss(0, 0.075)
        )

        planeite_sortie = (
            0.23
            + 0.10 * penalite_vide
            + 0.08 * penalite_demoulage
            + rng.gauss(0, 0.065)
        )

        diametre = (
            6.5
            + rng.gauss(0, 0.055)
        )

        profil = (
            0.55
            + 0.25 * penalite_vide
            + 0.12 * penalite_temp
            + rng.gauss(0, 0.14)
        )

        position = (
            0.28
            + rng.gauss(0, 0.11)
        )

        probabilite_joint_non = (
            0.06
            + 0.12 * penalite_temps_ouvert
            + 0.08 * penalite_ratio
        )

        joint = (
            "NON"
            if rng.random() < probabilite_joint_non
            else "OUI"
        )

        fuite = (
            0.22
            + 0.22 * penalite_temps_ouvert
            + 0.18 * penalite_ratio
            + (
                0.25
                if joint == "NON"
                else 0
            )
            + rng.gauss(0, 0.08)
        )

    # --------------------------------------------------------
    # CARACTÉRISTIQUES PRODUIT — SCÉNARIO AMÉLIORÉ
    # --------------------------------------------------------

    else:

        epaisseur = (
            2
            + rng.gauss(0, 0.04)
            + 0.02
            * penalite_vide
            * rng.choice([-1, 1])
        )

        planeite_entree = (
            0.24
            + 0.05 * penalite_vide
            + 0.04 * penalite_demoulage
            + rng.gauss(0, 0.045)
        )

        planeite_sortie = (
            0.18
            + 0.04 * penalite_vide
            + 0.03 * penalite_demoulage
            + rng.gauss(0, 0.035)
        )

        diametre = (
            6.5
            + rng.gauss(0, 0.025)
        )

        profil = (
            0.40
            + 0.10 * penalite_vide
            + 0.05 * penalite_temp
            + rng.gauss(0, 0.08)
        )

        position = (
            0.22
            + rng.gauss(0, 0.06)
        )

        probabilite_joint_non = (
            0.015
            + 0.03 * penalite_temps_ouvert
            + 0.02 * penalite_ratio
        )

        joint = (
            "NON"
            if rng.random() < probabilite_joint_non
            else "OUI"
        )

        fuite = (
            0.14
            + 0.07 * penalite_temps_ouvert
            + 0.06 * penalite_ratio
            + (
                0.18
                if joint == "NON"
                else 0
            )
            + rng.gauss(0, 0.045)
        )

    # --------------------------------------------------------
    # BORNAGE DES VALEURS
    # --------------------------------------------------------

    epaisseur = borner(
        epaisseur,
        1.60,
        2.40,
    )

    planeite_entree = borner(
        planeite_entree,
        0.05,
        0.90,
    )

    planeite_sortie = borner(
        planeite_sortie,
        0.05,
        0.70,
    )

    diametre = borner(
        diametre,
        6.25,
        6.75,
    )

    profil = borner(
        profil,
        0.10,
        1.50,
    )

    position = borner(
        position,
        0.05,
        0.90,
    )

    fuite = borner(
        fuite,
        0.02,
        1.20,
    )

    # --------------------------------------------------------
    # ARRONDI AVANT LE CALCUL DE CONFORMITÉ
    # --------------------------------------------------------
    # La conformité doit être calculée avec exactement les valeurs
    # qui seront visibles dans le fichier CSV.

    epaisseur = round(epaisseur, 2)
    planeite_entree = round(planeite_entree, 2)
    planeite_sortie = round(planeite_sortie, 2)
    diametre = round(diametre, 2)
    profil = round(profil, 2)
    position = round(position, 2)
    fuite = round(fuite, 2)

    # --------------------------------------------------------
    # CONTRÔLE DE CONFORMITÉ
    # --------------------------------------------------------

    defauts: list[str] = []

    if not 1.80 <= epaisseur <= 2.20:
        defauts.append("EPAISSEUR")

    if (
        planeite_entree > 0.50
        or planeite_sortie > 0.40
    ):
        defauts.append("PLANEITE")

    if profil > 1.00:
        defauts.append("PROFIL")

    if position > 0.50:
        defauts.append("PERCAGE")

    if fuite > 0.50:
        defauts.append("ETANCHEITE")

    if joint != "OUI":
        defauts.append("COLLAGE")

    statut = (
        "CONFORME"
        if not defauts
        else "NON CONFORME"
    )

    defaut_principal = choisir_defaut_principal(
        defauts,
        pression_vide,
    )

    commentaire = (
        ""
        if not defauts
        else (
            "Critères hors limite : "
            + ", ".join(defauts)
        )
    )

    # --------------------------------------------------------
    # CONSTRUCTION DE LA LIGNE
    # --------------------------------------------------------

    ligne = {
        "ID_PIECE": f"DAI-{i:04d}",
        "ORDRE_PRODUCTION": i,
        "SCENARIO": scenario,
        "DATE_FABRICATION": (
            DATE_DEBUT
            + timedelta(days=i - 1)
        ).strftime("%d/%m/%Y"),
        "ID_UPPER": f"UP-{i:04d}",
        "ID_LOWER": f"LO-{i:04d}",
        "LOT_PREIMPREGNE": (
            f"PRE-{((i - 1) // 20) + 1:02d}"
        ),
        "LOT_ADHESIF": (
            f"ADH-{((i - 1) // 25) + 1:02d}"
        ),
        "MOULE_UPPER": (
            f"MU-{1 + ((i - 1) % 2):02d}"
        ),
        "MOULE_LOWER": (
            f"ML-{1 + ((i - 1) % 2):02d}"
        ),
        "OPERATEUR_DRAPAGE": (
            f"OP-D{1 + ((i - 1) % 3):02d}"
        ),
        "OPERATEUR_ASSEMBLAGE": (
            f"OP-A{1 + ((i - 1) % 2):02d}"
        ),
        "CYCLE_CUISSON": (
            f"CYC-{((i - 1) // 5) + 1:03d}"
        ),
        "PRESSION_VIDE_ABS_MBAR": decimale_fr(
            pression_vide,
            1,
        ),
        "TEMP_MAX_C": decimale_fr(
            temp_max,
            1,
        ),
        "TEMPS_MAINTIEN_MIN": decimale_fr(
            maintien,
            1,
        ),
        "TEMP_DEMOULAGE_C": decimale_fr(
            temp_demoulage,
            1,
        ),
        "RATIO_ADHESIF": decimale_fr(
            ratio,
            3,
        ),
        "TEMPS_OUVERT_MIN": decimale_fr(
            temps_ouvert,
            1,
        ),
        "EPAISSEUR_MOY_MM": decimale_fr(
            epaisseur,
            2,
        ),
        "PLANEITE_ENTREE_MM": decimale_fr(
            planeite_entree,
            2,
        ),
        "PLANEITE_SORTIE_MM": decimale_fr(
            planeite_sortie,
            2,
        ),
        "DIAMETRE_TROU_MOY_MM": decimale_fr(
            diametre,
            2,
        ),
        "ECART_PROFIL_MAX_MM": decimale_fr(
            profil,
            2,
        ),
        "ECART_POSITION_TROUS_MAX_MM": (
            decimale_fr(
                position,
                2,
            )
        ),
        "PRESSION_TEST_KPA": "20,0",
        "DUREE_TEST_S": "60",
        "TAUX_FUITE": decimale_fr(
            fuite,
            2,
        ),
        "JOINT_CONTINU_CONFORME": joint,
        "DEFAUT_PRINCIPAL": defaut_principal,
        "NB_DEFAUTS": len(defauts),
        "STATUT_FINAL": statut,
        "COMMENTAIRE": commentaire,
    }

    # Vérification stricte : exactement les 33 colonnes prévues.
    if list(ligne.keys()) != COLONNES:
        raise ValueError(
            f"Structure incorrecte pour {ligne['ID_PIECE']}"
        )

    lignes.append(ligne)


# ============================================================
# VÉRIFICATIONS AVANT EXPORT
# ============================================================

if len(COLONNES) != 33:
    raise ValueError(
        f"Le dataset doit contenir 33 colonnes, "
        f"mais {len(COLONNES)} ont été trouvées."
    )

if len(lignes) != NB_PIECES:
    raise ValueError(
        f"{NB_PIECES} lignes attendues, "
        f"mais {len(lignes)} ont été générées."
    )

if lignes[0]["ID_PIECE"] != "DAI-0001":
    raise ValueError(
        "Le premier identifiant est incorrect."
    )

if lignes[-1]["ID_PIECE"] != "DAI-0100":
    raise ValueError(
        "Le dernier identifiant est incorrect."
    )

if lignes[49]["SCENARIO"] != "INITIAL":
    raise ValueError(
        "DAI-0050 doit appartenir au scénario INITIAL."
    )

if lignes[50]["SCENARIO"] != "AMELIORE":
    raise ValueError(
        "DAI-0051 doit appartenir au scénario AMELIORE."
    )


# ============================================================
# EXPORT CSV
# ============================================================

DOSSIER_DATASET.mkdir(
    parents=True,
    exist_ok=True,
)

with SORTIE.open(
    mode="w",
    newline="",
    encoding="utf-8-sig",
) as fichier:

    writer = csv.DictWriter(
        fichier,
        fieldnames=COLONNES,
        delimiter=";",
        extrasaction="raise",
        lineterminator="\n",
    )

    writer.writeheader()
    writer.writerows(lignes)


# ============================================================
# SYNTHÈSE DES RÉSULTATS
# ============================================================

initial_conformes = sum(
    1
    for ligne in lignes[:NB_INITIAL]
    if ligne["STATUT_FINAL"] == "CONFORME"
)

ameliore_conformes = sum(
    1
    for ligne in lignes[NB_INITIAL:]
    if ligne["STATUT_FINAL"] == "CONFORME"
)

initial_non_conformes = (
    NB_INITIAL - initial_conformes
)

ameliore_non_conformes = (
    (NB_PIECES - NB_INITIAL)
    - ameliore_conformes
)

print()
print("GÉNÉRATION TERMINÉE")
print(f"Fichier créé : {SORTIE}")
print(f"Colonnes générées : {len(COLONNES)}")
print(f"Lignes générées : {len(lignes)}")
print(
    f"INITIAL : {initial_conformes}/50 conformes "
    f"et {initial_non_conformes}/50 non conformes"
)
print(
    f"AMELIORE : {ameliore_conformes}/50 conformes "
    f"et {ameliore_non_conformes}/50 non conformes"
)