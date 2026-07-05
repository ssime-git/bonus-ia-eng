# /// script
# requires-python = ">=3.10"
# dependencies = ["pandas>=2.0"]
# ///
"""
J6 — Le SUPERVISEUR sous le capot : une machine à états + human-in-the-loop.

En J6 (S06, S10, S13) le superviseur « répartit, il ne fait pas » : à chaque tour
il tranche pour EXACTEMENT un état suivant — DOC, CALC, REPORT ou FIN — et
l'« outil » du superviseur, c'est un agent worker. La slide S13 le dit :
« la même boucle, l'outil = un agent ».

Ici on code cette boucle comme une machine à états, avec :
  - 3 workers spécialisés (recherche / contrôle / synthèse),
  - un JOURNAL de traçabilité « qui a fait quoi » (S24 : traçabilité notée),
  - un point Human-in-the-loop avant la restitution (S14-S16, node Human Input).

Tout tourne SANS LLM : le superviseur est ici à base de règles (déterministe,
donc testable). Un encart montre comment brancher un vrai LLM à la place.
"""
from __future__ import annotations
import json
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "socle"))
import liora_data  # noqa: E402

DF = liora_data.load_all()

# ─────────────────────────────────────────────────────────────────────────────
# LES WORKERS  (chacun une mission étroite — S12 « aucun worker ne déborde »)
# ─────────────────────────────────────────────────────────────────────────────

def worker_detection(etat: dict) -> dict:
    """Agent 1 · Détection : repère l'établissement au brut moyen le plus atypique."""
    g = DF.groupby("Etablissement")["Brut"].mean()
    mediane = g.median()
    cible = (g / mediane).idxmax()          # le plus éloigné de la médiane
    ecart = float(g[cible] / mediane)
    etat["alerte"] = {"etablissement": cible,
                      "brut_moyen": round(float(g[cible]), 2),
                      "brut_moyen_median_secteur": round(float(mediane), 2),
                      "ratio": round(ecart, 2)}
    etat["besoin_calcul"] = True
    return etat


def worker_controle(etat: dict) -> dict:
    """Agent 2 · Contrôle : quantifie l'écart et le nb de bulletins concernés."""
    cible = etat["alerte"]["etablissement"]
    sub = DF[DF["Etablissement"] == cible]
    etat["controle"] = {
        "nb_bulletins": int(len(sub)),
        "part_brut_gt_10k": round(float((sub["Brut"] > 10000).mean()), 3),
        "brut_max": round(float(sub["Brut"].max()), 2),
    }
    etat["besoin_calcul"] = False
    return etat


def worker_synthese(etat: dict) -> dict:
    """Agent 3 · Synthèse : rédige l'alerte d'audit (version sans LLM)."""
    a, c = etat["alerte"], etat["controle"]
    etat["rapport"] = (
        f"ALERTE AUDIT — {a['etablissement']}\n"
        f"Brut moyen {a['brut_moyen']} € vs médiane secteur "
        f"{a['brut_moyen_median_secteur']} € (ratio {a['ratio']}×).\n"
        f"{c['nb_bulletins']} bulletins ; "
        f"{int(c['part_brut_gt_10k']*100)}% au-dessus de 10 000 € ; "
        f"brut max {c['brut_max']} €.\n"
        f"À vérifier : primes exceptionnelles, régularisations, ou anomalie de saisie."
    )
    return etat


WORKERS = {"DOC": worker_detection, "CALC": worker_controle, "REPORT": worker_synthese}

# ─────────────────────────────────────────────────────────────────────────────
# LE SUPERVISEUR  (à base de règles : déterministe, testable sans LLM)
# ─────────────────────────────────────────────────────────────────────────────

def superviseur(etat: dict) -> str:
    """Renvoie l'état suivant : DOC, CALC, REPORT ou FIN. UN seul, à chaque tour."""
    if "alerte" not in etat:
        return "DOC"                 # rien détecté encore -> détection
    if etat.get("besoin_calcul"):
        return "CALC"                # alerte posée mais pas quantifiée
    if "rapport" not in etat:
        return "REPORT"              # quantifié mais pas rédigé
    return "FIN"


def demande_validation_humaine(rapport: str) -> bool:
    """Node Human Input (S15) : l'auditeur valide ou rejette avant restitution."""
    print("\n──── VALIDATION HUMAINE REQUISE (HITL) ────")
    print(rapport)
    rep = input("\nValidez-vous cette alerte d'audit ? [o/N] ").strip().lower()
    return rep in ("o", "oui", "y", "yes")


def run(hitl: bool = True, max_tours: int = 8):
    etat: dict = {}
    journal = []                     # traçabilité : qui a fait quoi (S24)
    for tour in range(1, max_tours + 1):
        prochain = superviseur(etat)
        journal.append({"tour": tour, "superviseur_choisit": prochain})
        if prochain == "FIN":
            break
        etat = WORKERS[prochain](etat)
        journal.append({"tour": tour, "worker": prochain,
                        "produit": _resume(etat, prochain)})
    # Human-in-the-loop avant toute décision (S14 : « en sortie de chaîne »)
    valide = True
    if hitl and "rapport" in etat:
        valide = demande_validation_humaine(etat["rapport"])
    etat["validation_humaine"] = valide
    journal.append({"decision_humaine": "VALIDÉ" if valide else "REJETÉ"})
    return etat, journal


def _resume(etat, etape):
    return {"DOC": etat.get("alerte"), "CALC": etat.get("controle"),
            "REPORT": "rapport rédigé"}.get(etape)


if __name__ == "__main__":
    # Sans HITL (non-interactif) pour la démo automatique :
    etat, journal = run(hitl=False)
    print("== JOURNAL DE TRAÇABILITÉ (qui a fait quoi) ==")
    print(json.dumps(journal, ensure_ascii=False, indent=2))
    print("\n== RAPPORT ==")
    print(etat["rapport"])
