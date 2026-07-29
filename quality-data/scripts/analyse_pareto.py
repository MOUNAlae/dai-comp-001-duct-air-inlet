import csv
from collections import Counter
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

SORTIE_SYNTHESE = (
    DOSSIER_RESULTATS
    / "DAI_COMP_001_Synthese_Conformite.csv"
)

SORTIE_PARETO = (
    DOSSIER_RESULTATS
    / "DAI_COMP_001_Pareto_Defauts.csv"
)

SCENARIOS = ["INITIAL", "AMELIORE"]


# ============================================================
# FONCTIONS
# ============================================================

def pourcentage(
    valeur: int,
    total: int,
) -> float:
    """Calcule un pourcentage en évitant la division par zéro."""

    if total == 0:
        return 0.0

    return round(100 * valeur / total, 2)


def decimal_fr(
    valeur: float,
    chiffres: int = 2,
) -> str:
    """Formate un nombre avec une virgule décimale."""

    return f"{valeur:.{chiffres}f}".replace(".", ",")


def exporter_csv(
    chemin: Path,
    colonnes: list[str],
    lignes: list[dict[str, object]],
) -> None:
    """Exporte une liste de dictionnaires au format CSV français."""

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
    colonnes_entree = lecteur.fieldnames


colonnes_obligatoires = {
    "ID_PIECE",
    "SCENARIO",
    "DEFAUT_PRINCIPAL",
    "NB_DEFAUTS",
    "STATUT_FINAL",
}

colonnes_manquantes = (
    colonnes_obligatoires
    - set(colonnes_entree or [])
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
# CONTRÔLES DE COHÉRENCE
# ============================================================

for ligne in donnees:

    statut = ligne["STATUT_FINAL"]
    defaut = ligne["DEFAUT_PRINCIPAL"]
    nb_defauts = int(ligne["NB_DEFAUTS"])

    if statut == "CONFORME":

        if defaut != "AUCUN" or nb_defauts != 0:
            raise ValueError(
                "Incohérence sur "
                f"{ligne['ID_PIECE']} : pièce conforme "
                "avec défaut déclaré."
            )

    elif statut == "NON CONFORME":

        if defaut == "AUCUN" or nb_defauts < 1:
            raise ValueError(
                "Incohérence sur "
                f"{ligne['ID_PIECE']} : pièce non conforme "
                "sans défaut déclaré."
            )

    else:
        raise ValueError(
            f"Statut inconnu pour {ligne['ID_PIECE']} : "
            f"{statut}"
        )


# ============================================================
# SYNTHÈSE DE CONFORMITÉ
# ============================================================

synthese = []

for scenario in SCENARIOS:

    sous_ensemble = [
        ligne
        for ligne in donnees
        if ligne["SCENARIO"] == scenario
    ]

    total = len(sous_ensemble)

    conformes = sum(
        1
        for ligne in sous_ensemble
        if ligne["STATUT_FINAL"] == "CONFORME"
    )

    non_conformes = total - conformes

    synthese.append(
        {
            "SCENARIO": scenario,
            "TOTAL_PIECES": total,
            "PIECES_CONFORMES": conformes,
            "PIECES_NON_CONFORMES": non_conformes,
            "TAUX_CONFORMITE_PCT": decimal_fr(
                pourcentage(conformes, total),
                2,
            ),
            "TAUX_NON_CONFORMITE_PCT": decimal_fr(
                pourcentage(non_conformes, total),
                2,
            ),
        }
    )


total_global = len(donnees)

conformes_global = sum(
    1
    for ligne in donnees
    if ligne["STATUT_FINAL"] == "CONFORME"
)

non_conformes_global = (
    total_global - conformes_global
)

synthese.append(
    {
        "SCENARIO": "GLOBAL",
        "TOTAL_PIECES": total_global,
        "PIECES_CONFORMES": conformes_global,
        "PIECES_NON_CONFORMES": non_conformes_global,
        "TAUX_CONFORMITE_PCT": decimal_fr(
            pourcentage(
                conformes_global,
                total_global,
            ),
            2,
        ),
        "TAUX_NON_CONFORMITE_PCT": decimal_fr(
            pourcentage(
                non_conformes_global,
                total_global,
            ),
            2,
        ),
    }
)


# ============================================================
# PARETO DES DÉFAUTS PRINCIPAUX
# ============================================================

pieces_non_conformes = [
    ligne
    for ligne in donnees
    if ligne["STATUT_FINAL"] == "NON CONFORME"
]

nombre_nc = len(pieces_non_conformes)

compteur_global = Counter(
    ligne["DEFAUT_PRINCIPAL"]
    for ligne in pieces_non_conformes
)

compteurs_scenario = {
    scenario: Counter(
        ligne["DEFAUT_PRINCIPAL"]
        for ligne in pieces_non_conformes
        if ligne["SCENARIO"] == scenario
    )
    for scenario in SCENARIOS
}

defauts_tries = sorted(
    compteur_global.items(),
    key=lambda element: (
        -element[1],
        element[0],
    ),
)

pareto = []
cumul = 0

for rang, (defaut, nombre) in enumerate(
    defauts_tries,
    start=1,
):

    cumul += nombre

    pareto.append(
        {
            "DEFAUT_PRINCIPAL": defaut,
            "NOMBRE_PIECES": nombre,
            "CUMUL_PCT": decimal_fr(
                pourcentage(cumul, nombre_nc),
                2,
            ),
            "POURCENTAGE_PCT": decimal_fr(
                pourcentage(nombre, nombre_nc),
                2,
            ),
            "INITIAL": compteurs_scenario[
                "INITIAL"
            ].get(defaut, 0),
            "AMELIORE": compteurs_scenario[
                "AMELIORE"
            ].get(defaut, 0),
            "RANG": rang,
        }
    )


if sum(compteur_global.values()) != nombre_nc:
    raise ValueError(
        "Le Pareto ne couvre pas toutes les pièces "
        "non conformes."
    )


# ============================================================
# EXPORTS
# ============================================================

DOSSIER_RESULTATS.mkdir(
    parents=True,
    exist_ok=True,
)

exporter_csv(
    SORTIE_SYNTHESE,
    [
        "SCENARIO",
        "TOTAL_PIECES",
        "PIECES_CONFORMES",
        "PIECES_NON_CONFORMES",
        "TAUX_CONFORMITE_PCT",
        "TAUX_NON_CONFORMITE_PCT",
    ],
    synthese,
)

exporter_csv(
    SORTIE_PARETO,
    [
        "DEFAUT_PRINCIPAL",
        "NOMBRE_PIECES",
        "CUMUL_PCT",
        "POURCENTAGE_PCT",
        "INITIAL",
        "AMELIORE",
        "RANG",
    ],
    pareto,
)


# ============================================================
# AFFICHAGE TERMINAL
# ============================================================

print()
print("ANALYSE JOUR 60 TERMINÉE")
print(f"Pièces analysées : {total_global}")
print(
    f"Conformes : {conformes_global}/{total_global} "
    f"({pourcentage(conformes_global, total_global):.2f} %)"
)
print(
    f"Non conformes : {non_conformes_global}/{total_global} "
    f"({pourcentage(non_conformes_global, total_global):.2f} %)"
)

for ligne in synthese[:2]:
    print(
        f"{ligne['SCENARIO']} : "
        f"{ligne['PIECES_CONFORMES']}/"
        f"{ligne['TOTAL_PIECES']} conformes"
    )

print()
print("PARETO DES DÉFAUTS PRINCIPAUX")

for ligne in pareto:
    print(
        f"{ligne['RANG']}. "
        f"{ligne['DEFAUT_PRINCIPAL']} : "
        f"{ligne['NOMBRE_PIECES']} pièces — "
        f"cumul {ligne['CUMUL_PCT']} %"
    )

print()
print(f"Fichier créé : {SORTIE_SYNTHESE}")
print(f"Fichier créé : {SORTIE_PARETO}")