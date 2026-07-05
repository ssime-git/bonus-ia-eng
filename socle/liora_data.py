# /// script
# requires-python = ">=3.10"
# dependencies = ["pandas>=2.0"]
# ///
"""
Socle données LIORA — chargement des journaux de paie (type DSN).

16 établissements (restaurants), ~450 bulletins au total.
Format source : CSV séparé par « | », décimales à la virgule, en-tête avec BOM.
Colonnes utiles : Matricule, Salarie, Sexe, Date début contrat, Date Sortie,
Total heures, Heures suppl., Heures compl., Brut, Net imposable, Net à payer,
Montant PAS, etc.

Aucune dépendance à un LLM : ce module tourne partout, tout de suite.
Utilisé par les fiches J4 → J7 pour exposer des « vues » de la donnée.
"""
from __future__ import annotations
import glob
import os
import re
import pandas as pd

# Dossier des CSV. Par défaut : ../data à côté de ce fichier.
DATA_DIR = os.environ.get(
    "LIORA_DATA_DIR",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"),
)

# Colonnes numériques (décimale virgule -> float)
_NUM_COLS = [
    "Total heures", "Heures suppl.", "Heures compl.", "Brut", "Base CSG",
    "Base cotisations", "Net imposable", "Retenues S. déductibles",
    "Retenues S. non déductibles", "Retenues P.", "Avantages en nature",
    "Divers +", "Divers -", "Net Bulletin", "Net Avant PAS",
    "Montant PAS", "Net à payer",
]


def _etab_from_path(path: str) -> str:
    """Nom d'établissement déduit du nom de fichier."""
    base = os.path.basename(path)
    base = re.sub(r"\.csv$", "", base)
    # « Journal de paie - Le Chaudron » -> « Le Chaudron »
    base = re.sub(r"^Journal d ?e ?paie\s*-\s*", "", base)
    return base.strip()


def _to_float(series: pd.Series) -> pd.Series:
    return (
        series.astype(str)
        .str.replace(" ", "", regex=False)  # espace fine
        .str.replace(" ", "", regex=False)
        .str.replace(",", ".", regex=False)
        .replace({"": None, "nan": None})
        .astype(float)
    )


def load_etablissement(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, sep="|", dtype=str, encoding="utf-8-sig").fillna("")
    df.columns = [c.strip().lstrip("﻿") for c in df.columns]
    df["Etablissement"] = _etab_from_path(path)
    for col in _NUM_COLS:
        if col in df.columns:
            df[col] = _to_float(df[col])
    return df


# CSV minimisé (sans colonne nominative) versionné dans le repo — utilisé si les
# journaux pipe bruts ne sont pas présents (ex. après un clone du dépôt public).
_HERE = os.path.dirname(os.path.abspath(__file__))
_COMBINED = [
    os.path.join(_HERE, "..", "public", "data", "liora_paie.csv"),
    "public/data/liora_paie.csv",
    "../public/data/liora_paie.csv",
]


def load_all(data_dir: str | None = None) -> pd.DataFrame:
    """Concatène les journaux LIORA dans un seul DataFrame.

    Priorité aux journaux pipe bruts de `data/` (dev local, données nominatives
    complètes). À défaut, on lit le CSV combiné minimisé `public/data/liora_paie.csv`
    (versionné, sans noms) — pour qu'un simple clone fonctionne.
    """
    data_dir = data_dir or DATA_DIR
    paths = sorted(glob.glob(os.path.join(data_dir, "*.csv")))
    if paths:
        return pd.concat([load_etablissement(p) for p in paths], ignore_index=True)
    for c in _COMBINED:
        if os.path.exists(c):
            return pd.read_csv(c)
    raise FileNotFoundError(
        "Aucune donnée trouvée (ni journaux pipe dans data/, ni "
        "public/data/liora_paie.csv). Fixez LIORA_DATA_DIR au besoin."
    )


def list_etablissements(data_dir: str | None = None) -> list[str]:
    df = load_all(data_dir)
    return sorted(df["Etablissement"].unique().tolist())


if __name__ == "__main__":
    df = load_all()
    print(f"{len(df)} bulletins · {df['Etablissement'].nunique()} établissements")
    print("Colonnes :", list(df.columns))
    print(df.groupby("Etablissement")["Brut"].agg(["count", "sum"]).round(0))
