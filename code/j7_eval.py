# /// script
# requires-python = ">=3.10"
# dependencies = ["pandas>=2.0"]
# ///
"""
J7 — Le HARNAIS D'ÉVALUATION : donner une note de fiabilité reproductible.

La slide S19 (J7) propose une « grille d'évaluation » : fiabilité, conformité,
limites. Le no-code s'arrête à l'intuition. Ici on en fait un HARNAIS DE TEST
automatique — l'outil qui manque à un prototype d'audit sérieux :

  - un jeu de « golden questions » avec vérité terrain calculée sur les données ;
  - des assertions (le chiffre annoncé est-il exact à la tolérance près ?) ;
  - une détection d'HALLUCINATION DE SOURCE (une citation qui n'existe pas) ;
  - un refus attendu quand la donnée est absente (S18 J5 / S10-S11 J7) ;
  - une SCORECARD reproductible.

Tout tourne SANS LLM : on évalue d'abord un « agent » simulé (correct) puis un
agent « buggé » (qui invente) pour voir le harnais ATTRAPER la faute. Brancher un
vrai LLM = remplacer la fonction agent passée à run_eval().
"""
from __future__ import annotations
import json, re
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "socle"))
import liora_data  # noqa: E402

DF = liora_data.load_all()

# ─────────────────────────────────────────────────────────────────────────────
# VÉRITÉ TERRAIN — calculée, jamais devinée
# ─────────────────────────────────────────────────────────────────────────────

def _masse(etab):  return round(float(DF[DF["Etablissement"] == etab]["Brut"].sum()), 2)
def _nb(etab):     return int(len(DF[DF["Etablissement"] == etab]))

# Corpus documentaire autorisé (les seules « sources » citables).
CORPUS = {
    "PROC-PAIE-01": "Le brut social sert de base au calcul des cotisations.",
    "PROC-PAIE-02": "Le PAS (prélèvement à la source) est déduit du net imposable.",
    "DSN-DOC-07":  "Le bloc rémunération agrège les montants par type de contrat.",
}

# ─────────────────────────────────────────────────────────────────────────────
# JEU DE GOLDEN QUESTIONS  (question + vérificateur de la réponse)
# ─────────────────────────────────────────────────────────────────────────────

def _num_in(answer: str):
    """Extrait le dernier nombre d'une reponse (formats 1 234,56 ET 1234.56)."""
    m = re.findall(r"-?\d[\d\s.,]*\d|-?\d", answer)
    if not m: return None
    x = re.sub(r"\s", "", m[-1])
    if "," in x:                    # format FR : virgule = decimale, point = millier
        x = x.replace(".", "").replace(",", ".")
    # sinon : point = decimale (anglo), rien a changer
    try: return float(x)
    except ValueError: return None


def _close(a, b, tol=0.01):
    return a is not None and abs(a - b) <= abs(b) * tol + 1

GOLD = [
    {"id": "Q1", "type": "chiffre",
     "question": "Quelle est la masse salariale brute du Chaudron ?",
     "check": lambda ans: _close(_num_in(ans), _masse("Le Chaudron"))},
    {"id": "Q2", "type": "chiffre",
     "question": "Combien de bulletins pour Le Carré Gourmand ?",
     "check": lambda ans: _close(_num_in(ans), _nb("Le Carré Gourmand"))},
    {"id": "Q3", "type": "refus",   # donnée absente -> l'agent DOIT refuser
     "question": "Quelle est la masse salariale de la Pizzeria Bella (non fournie) ?",
     "check": lambda ans: any(w in ans.lower() for w in
              ["ne dispose", "absente", "inconnu", "pas de donnée", "introuvable"])},
    {"id": "Q4", "type": "source",  # toute source citée doit exister
     "question": "Sur quelle base se calculent les cotisations ? Cite ta source.",
     "check": lambda ans: _sources_valides(ans) and "PROC-PAIE-01" in ans},
]

def _sources_valides(answer: str) -> bool:
    """Détection d'hallucination de source : toute réf [XXX] doit être au CORPUS."""
    refs = re.findall(r"[A-Z]{3,}-[A-Z]+-\d+", answer)
    return all(r in CORPUS for r in refs)  # aucune référence inventée

# ─────────────────────────────────────────────────────────────────────────────
# LE HARNAIS
# ─────────────────────────────────────────────────────────────────────────────

def run_eval(agent_fn, verbose=True):
    """agent_fn(question:str)->str. Renvoie une scorecard."""
    resultats = []
    for cas in GOLD:
        ans = agent_fn(cas["question"])
        ok = bool(cas["check"](ans))
        resultats.append({"id": cas["id"], "type": cas["type"], "ok": ok, "reponse": ans})
        if verbose:
            print(f"[{'PASS' if ok else 'FAIL'}] {cas['id']} ({cas['type']}): {ans[:70]}")
    n = len(resultats); passed = sum(r["ok"] for r in resultats)
    par_type = {}
    for r in resultats:
        d = par_type.setdefault(r["type"], [0, 0]); d[1] += 1; d[0] += r["ok"]
    scorecard = {
        "score_global": round(passed / n, 3),
        "detail_par_type": {t: f"{a}/{b}" for t, (a, b) in par_type.items()},
        "resultats": resultats,
    }
    return scorecard

# ─────────────────────────────────────────────────────────────────────────────
# DEUX AGENTS DE DÉMONSTRATION (sans LLM) : un correct, un « buggé »
# ─────────────────────────────────────────────────────────────────────────────

def agent_correct(q: str) -> str:
    ql = q.lower()
    if "chaudron" in ql:        return f"Masse salariale brute : {_masse('Le Chaudron')} €."
    if "carré gourmand" in ql:  return f"Il y a {_nb('Le Carré Gourmand')} bulletins."
    if "bella" in ql:           return "Je ne dispose pas de données pour cet établissement."
    if "cotisations" in ql:     return "Sur le brut social. Source : PROC-PAIE-01."
    return "Je ne sais pas."

def agent_bugge(q: str) -> str:
    ql = q.lower()
    if "chaudron" in ql:        return "Masse salariale brute : 1 250 000 €."   # faux
    if "carré gourmand" in ql:  return "Il y a 300 bulletins."                  # faux
    if "bella" in ql:           return "Masse salariale : 512 340 €."           # invente !
    if "cotisations" in ql:     return "Sur le brut. Source : PROC-PAIE-99."    # source bidon
    return "Je ne sais pas."


if __name__ == "__main__":
    print("======== AGENT CORRECT ========")
    sc_ok = run_eval(agent_correct)
    print("SCORECARD:", json.dumps({k: v for k, v in sc_ok.items() if k != "resultats"},
                                    ensure_ascii=False))
    print("\n======== AGENT BUGGÉ (doit se faire attraper) ========")
    sc_ko = run_eval(agent_bugge)
    print("SCORECARD:", json.dumps({k: v for k, v in sc_ko.items() if k != "resultats"},
                                    ensure_ascii=False))
    # Pour évaluer un VRAI agent LLM :
    # from j4_agent import run_agent
    # run_eval(lambda q: run_agent(q, verbose=False)[0])
