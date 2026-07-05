# /// script
# requires-python = ">=3.10"
# dependencies = ["marimo", "pandas>=2.0"]
# ///
"""J6 · Multi-agents & HITL — notebook-cours marimo."""
import marimo

__generated_with = "0.9.27"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _(mo):
    import pandas as pd
    from pathlib import Path

    _CSV = "liora_paie.csv"

    def _load_liora():
        # 1) Local (uv run / marimo edit) : systeme de fichiers
        for c in (Path("public/data") / _CSV, Path("../public/data") / _CSV,
                  Path("data") / _CSV, Path("../data") / _CSV):
            if c.exists():
                return pd.read_csv(c)
        # 2) WASM (GitHub Pages) : via l'URL du notebook
        base = str(mo.notebook_location()).rstrip("/")
        for url in (f"{base}/public/data/{_CSV}", f"{base}/../public/data/{_CSV}"):
            try:
                return pd.read_csv(url)
            except Exception:
                pass
        raise FileNotFoundError("liora_paie.csv introuvable (local et WASM).")

    df = _load_liora()
    return (df,)


@app.cell
def _(mo):
    mo.md(
        r"""
        # J6 · Multi-agents — le superviseur comme *machine à états*

        > 5 temps par notion → **① présentation · ② syntaxe · ③ exercice ·
        > ④ solution (repliée) · ⑤ commentaire**.

        **Prolonge** J6 : S06/S10 (le superviseur répartit, il ne fait pas),
        S13 (« même boucle, l'outil = un agent »), S14-S16 (Human Input), S24 (traçabilité).
        """
    )
    return


@app.cell
def _(mo):
    mo.md(r"""---""")
    return


# ═══════════════════════════════════════════════════════════════════════════
# NOTION 1 — Superviseur + workers = une machine à états
# ═══════════════════════════════════════════════════════════════════════════
@app.cell
def _(mo):
    mo.md(
        r"""
        ## ① Notion 1 — Le superviseur *répartit*, il ne *fait* pas

        Un seul agent qui cherche **et** calcule **et** rédige finit par bâcler. On
        spécialise : un **superviseur** découpe et distribue à des **workers**. À chaque
        tour, il tranche pour *exactement un* état suivant : `DOC → CALC → REPORT → FIN`.
        C'est une **machine à états**.
        """
    )
    return


@app.cell
def _(mo):
    mo.mermaid(
        """
        stateDiagram-v2
            [*] --> DOC
            DOC --> CALC : alerte détectée
            CALC --> REPORT : écart quantifié
            REPORT --> FIN : rapport rédigé
            FIN --> [*]
            note right of DOC : Agent Détection
            note right of CALC : Agent Contrôle
            note right of REPORT : Agent Synthèse
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        r"""
        ## ② Syntaxe — le superviseur est une fonction *pure*

        ```python
        def superviseur(etat: dict) -> str:
            if "alerte" not in etat:       return "DOC"     # rien détecté
            if etat.get("besoin_calcul"):  return "CALC"    # pas encore quantifié
            if "rapport" not in etat:      return "REPORT"  # pas encore rédigé
            return "FIN"
        ```

        Il ne *fait* rien : il **lit l'état** et renvoie le prochain nœud. Déterministe,
        donc **testable** (contrairement à un superviseur LLM).
        """
    )
    return


@app.cell
def _(df):
    # Les 3 workers (déterministes, sans LLM)
    def worker_detection(etat):
        g = df.groupby("Etablissement")["Brut"].mean()
        med = g.median()
        cible = (g / med).idxmax()
        etat["alerte"] = {"etablissement": cible, "brut_moyen": round(float(g[cible]), 2),
                          "median_secteur": round(float(med), 2), "ratio": round(float(g[cible] / med), 2)}
        etat["besoin_calcul"] = True
        return etat

    def worker_controle(etat):
        sub = df[df["Etablissement"] == etat["alerte"]["etablissement"]]
        etat["controle"] = {"nb_bulletins": int(len(sub)),
                            "part_gt_10k": round(float((sub["Brut"] > 10000).mean()), 3)}
        etat["besoin_calcul"] = False
        return etat

    def worker_synthese(etat):
        a, c = etat["alerte"], etat["controle"]
        etat["rapport"] = (f"ALERTE — {a['etablissement']} : brut moyen {a['brut_moyen']} € "
                           f"vs médiane {a['median_secteur']} € (ratio {a['ratio']}×) ; "
                           f"{c['nb_bulletins']} bulletins, {int(c['part_gt_10k']*100)}% > 10 000 €.")
        return etat

    WORKERS = {"DOC": worker_detection, "CALC": worker_controle, "REPORT": worker_synthese}
    return (WORKERS,)


@app.cell
def _(mo):
    mo.callout(
        mo.md(
            r"""
            ## ③ Exercice — écrivez le superviseur et la boucle

            1. Écrivez `superviseur(etat)` (voir syntaxe).
            2. Écrivez la boucle qui, tant que ≠ `FIN`, appelle `WORKERS[etat_suivant]`
               et **journalise** chaque décision (« qui a fait quoi »).
            """
        ),
        kind="info",
    )
    return


@app.cell
def _(mo):
    mo.accordion(
        {
            "🔓 ④ Afficher la solution": mo.md(
                r"""
                ```python
                def superviseur(etat):
                    if "alerte" not in etat:      return "DOC"
                    if etat.get("besoin_calcul"): return "CALC"
                    if "rapport" not in etat:     return "REPORT"
                    return "FIN"

                def run():
                    etat, journal = {}, []
                    while True:
                        nxt = superviseur(etat)
                        journal.append({"superviseur": nxt})
                        if nxt == "FIN":
                            break
                        etat = WORKERS[nxt](etat)
                        journal.append({"worker": nxt})
                    return etat, journal
                ```
                Le **journal** est votre piste d'audit : on sait quel agent a produit quoi.
                """
            )
        }
    )
    return


@app.cell
def _(WORKERS):
    def superviseur(etat):
        if "alerte" not in etat:
            return "DOC"
        if etat.get("besoin_calcul"):
            return "CALC"
        if "rapport" not in etat:
            return "REPORT"
        return "FIN"

    def run_chaine():
        etat, journal = {}, []
        while True:
            nxt = superviseur(etat)
            journal.append({"superviseur_choisit": nxt})
            if nxt == "FIN":
                break
            etat = WORKERS[nxt](etat)
            journal.append({"worker": nxt, "fait": True})
        return etat, journal

    etat_final, journal = run_chaine()
    {"journal": journal, "rapport": etat_final["rapport"]}
    return etat_final, journal, superviseur


@app.cell
def _(mo, superviseur):
    # Tests de routing (rigueur d'ingénieur) — s'exécutent à l'affichage
    _t = [
        superviseur({}) == "DOC",
        superviseur({"alerte": {}, "besoin_calcul": True}) == "CALC",
        superviseur({"alerte": {}, "besoin_calcul": False}) == "REPORT",
        superviseur({"alerte": {}, "besoin_calcul": False, "rapport": "x"}) == "FIN",
    ]
    mo.callout(
        mo.md(f"**Tests de routing** : {sum(_t)}/4 passent "
              + ("✅" if all(_t) else "❌")),
        kind="success" if all(_t) else "danger",
    )
    return


@app.cell
def _(mo):
    mo.md(
        r"""
        ## ⑤ Commentaire

        Un superviseur **à règles** se teste en 4 assertions (ci-dessus). Un superviseur
        **LLM** apporte de la flexibilité mais coûte en contrôle — c'est l'arbitrage
        « contrôle vs flexibilité » (S09). Plus la décision de routing est explicite,
        plus le système est auditable.
        """
    )
    return


@app.cell
def _(mo):
    mo.md(r"""---""")
    return


# ═══════════════════════════════════════════════════════════════════════════
# NOTION 2 — Human-in-the-loop
# ═══════════════════════════════════════════════════════════════════════════
@app.cell
def _(mo):
    mo.md(
        r"""
        ## ① Notion 2 — Où placer l'humain ?

        La validation humaine se place **en sortie de chaîne, avant toute décision**, et
        surtout **sur les anomalies à fort enjeu** (S14/S16). Ici, l'auditeur valide ou
        rejette l'alerte avant restitution.

        ## ② Syntaxe — un point de validation réactif

        En notebook, on remplace le `input()` bloquant par un **interrupteur marimo**
        dont la valeur circule, réactive, dans la suite du flow.
        """
    )
    return


@app.cell
def _(mo):
    seuil_hitl = mo.ui.slider(1.0, 10.0, value=3.0, step=0.5,
                              label="Seuil de ratio déclenchant la validation humaine")
    valider = mo.ui.switch(label="✅ Auditeur : je valide l'alerte")
    mo.vstack([seuil_hitl, valider])
    return seuil_hitl, valider


@app.cell
def _(mo):
    mo.callout(
        mo.md(
            r"""
            ## ③ Exercice — conditionner le HITL au risque

            La validation ne doit être **demandée** que si le `ratio` de l'alerte dépasse
            le seuil. Écrivez la logique qui : si `ratio > seuil` → statut dépend de
            l'interrupteur `valider` ; sinon → « auto-validé (faible enjeu) ».
            """
        ),
        kind="info",
    )
    return


@app.cell
def _(mo):
    mo.accordion(
        {
            "🔓 ④ Afficher la solution": mo.md(
                r"""
                ```python
                ratio = etat_final["alerte"]["ratio"]
                if ratio > seuil_hitl.value:
                    statut = "VALIDÉ" if valider.value else "EN ATTENTE / REJETÉ"
                else:
                    statut = "AUTO-VALIDÉ (faible enjeu)"
                ```
                La décision (et *pourquoi* elle a été requise) entre dans le journal :
                en audit, une validation est une **trace signée**, pas un clic perdu.
                """
            )
        }
    )
    return


@app.cell
def _(etat_final, mo, seuil_hitl, valider):
    ratio = etat_final["alerte"]["ratio"]
    if ratio > seuil_hitl.value:
        statut = "VALIDÉ" if valider.value else "EN ATTENTE / REJETÉ"
        raison = f"ratio {ratio}× > seuil {seuil_hitl.value} → humain requis"
    else:
        statut = "AUTO-VALIDÉ (faible enjeu)"
        raison = f"ratio {ratio}× ≤ seuil {seuil_hitl.value}"
    mo.callout(mo.md(f"**Statut de l'alerte : {statut}**  \n*{raison}*"),
               kind="success" if statut.startswith("VALIDÉ") or statut.startswith("AUTO") else "warn")
    return


@app.cell
def _(mo):
    mo.md(
        r"""
        ## ⑤ Commentaire

        Bougez le curseur et l'interrupteur ci-dessus : le statut se recalcule tout seul.
        C'est l'équivalent réactif du **node Human Input**. Le HITL n'a de valeur que si
        l'humain a le contexte pour trancher — d'où l'importance d'un rapport **lisible
        et sourcé**.

        ---
        ### ✅ Récap J6
        - Le superviseur = **machine à états** (un état/tour), testable sans LLM.
        - Chaque worker a **un** rôle → traçabilité « qui a fait quoi ».
        - Le HITL se place sur les **anomalies à fort enjeu**, et se journalise.
        """
    )
    return


if __name__ == "__main__":
    app.run()
