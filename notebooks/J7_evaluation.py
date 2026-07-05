# /// script
# requires-python = ">=3.10"
# dependencies = ["marimo", "pandas>=2.0"]
# ///
"""J7 · Évaluation & fiabilité — notebook-cours marimo."""
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
    return df, pd


@app.cell
def _(mo):
    mo.md(
        r"""
        # J7 · Évaluation — transformer la *grille* en *harnais de test*

        > 5 temps par notion → **① présentation · ② syntaxe · ③ exercice ·
        > ④ solution (repliée) · ⑤ commentaire**.

        **Prolonge** J7 : S10-S11 (robustesse, refus, hallucination), S19-S20 (grille
        d'évaluation, « limites = critère noté »), S21 (RGPD). C'est la couche
        d'ingénieur qui manque au prototype no-code — et la réponse à *« l'IA se trompe
        si on ne dit pas vérifie »* : on **industrialise** le « vérifie ».
        """
    )
    return


@app.cell
def _(mo):
    mo.md(r"""---""")
    return


# ═══════════════════════════════════════════════════════════════════════════
# NOTION 1 — Golden questions & vérité terrain
# ═══════════════════════════════════════════════════════════════════════════
@app.cell
def _(mo):
    mo.md(
        r"""
        ## ① Notion 1 — On ne *dit* pas « fiable », on le *mesure*

        Un harnais d'évaluation = un jeu de **golden questions** dont la **vérité terrain
        est calculée** (jamais recopiée à la main), plus un **vérificateur** par question.

        ```
          Question ──► [ AGENT ] ──► réponse ──► [ CHECK(réponse, vérité) ] ──► PASS / FAIL
                                                        ▲
                                             vérité calculée sur df
        ```

        Quatre types de contrôle : **chiffre** (exactitude), **refus** (dire « je ne sais
        pas » quand la donnée manque), **source** (la citation existe-t-elle ?),
        **minimisation** (refuser d'exposer du nominatif — RGPD).
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        r"""
        ## ② Syntaxe — une golden question

        ```python
        def masse(etab):                    # vérité terrain, CALCULÉE
            return round(float(df[df["Etablissement"] == etab]["Brut"].sum()), 2)

        GOLD = [
            {"id": "Q1", "type": "chiffre",
             "question": "Masse salariale brute du Chaudron ?",
             "check": lambda ans: close(num_in(ans), masse("Le Chaudron"))},
        ]
        ```

        `num_in` extrait le nombre de la réponse ; `close` tolère ±1 % (arrondis).
        """
    )
    return


@app.cell
def _(df):
    import re as _re

    def masse(etab):
        return round(float(df[df["Etablissement"] == etab]["Brut"].sum()), 2)

    def num_in(answer):
        m = _re.findall(r"-?\d[\d\s.,]*\d|-?\d", answer)
        if not m:
            return None
        x = _re.sub(r"\s", "", m[-1])
        if "," in x:
            x = x.replace(".", "").replace(",", ".")
        try:
            return float(x)
        except ValueError:
            return None

    def close(a, b, tol=0.01):
        return a is not None and abs(a - b) <= abs(b) * tol + 1

    CORPUS = {"PROC-PAIE-01", "PROC-PAIE-02", "DSN-DOC-07"}   # sources autorisées
    return CORPUS, close, masse, num_in


@app.cell
def _(mo):
    mo.callout(
        mo.md(
            r"""
            ## ③ Exercice — écrivez deux vérificateurs

            1. Un `check` de type **refus** : réussit si la réponse contient « ne dispose »,
               « inconnu », « pas de donnée »… (agent confronté à un établissement absent).
            2. Un `check` de type **source** : réussit si **toute** référence de la forme
               `XXX-XXX-00` présente dans la réponse appartient à `CORPUS` (sinon =
               hallucination de source).
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
                def check_refus(ans):
                    return any(w in ans.lower() for w in
                               ["ne dispose", "inconnu", "pas de donnée", "absente"])

                def check_source(ans):
                    refs = re.findall(r"[A-Z]{3,}-[A-Z]+-\\d+", ans)
                    return all(r in CORPUS for r in refs)   # aucune réf inventée
                ```

                `check_source` est le filet anti-hallucination : une source citée qui
                n'existe pas fait **échouer** le test, même si le reste est plausible.
                """
            )
        }
    )
    return


@app.cell
def _(CORPUS, close, masse, num_in):
    import re as _re2

    def check_refus(ans):
        return any(w in ans.lower() for w in
                   ["ne dispose", "inconnu", "pas de donnée", "absente", "introuvable"])

    def check_source(ans):
        refs = _re2.findall(r"[A-Z]{3,}-[A-Z]+-\d+", ans)
        return all(r in CORPUS for r in refs)

    GOLD = [
        {"id": "Q1", "type": "chiffre",
         "question": "Masse salariale brute du Chaudron ?",
         "check": lambda a: close(num_in(a), masse("Le Chaudron"))},
        {"id": "Q2", "type": "refus",
         "question": "Masse salariale de la Pizzeria Bella (non fournie) ?",
         "check": check_refus},
        {"id": "Q3", "type": "source",
         "question": "Base de calcul des cotisations ? Cite ta source.",
         "check": lambda a: check_source(a) and "PROC-PAIE-01" in a},
    ]
    return (GOLD,)


@app.cell
def _(mo):
    mo.md(
        r"""
        ## ⑤ Commentaire

        Chaque `check` est une **assertion automatique**. Rejouable à chaque modif du
        prompt/flow : c'est de la **non-régression**. Les cas `FAIL` *sont* votre section
        « limites identifiées » (critère noté, S20) — plus besoin de la rédiger à la main.

        ---
        """
    )
    return


# ═══════════════════════════════════════════════════════════════════════════
# NOTION 2 — Le harnais attrape l'agent qui invente
# ═══════════════════════════════════════════════════════════════════════════
@app.cell
def _(masse):
    # Deux agents de démonstration : un correct, un « buggé »
    def agent_correct(q):
        ql = q.lower()
        if "chaudron" in ql:
            return f"Masse salariale brute : {masse('Le Chaudron')} €."
        if "bella" in ql:
            return "Je ne dispose pas de données pour cet établissement."
        if "cotisations" in ql:
            return "Sur le brut social. Source : PROC-PAIE-01."
        return "Je ne sais pas."

    def agent_bugge(q):
        ql = q.lower()
        if "chaudron" in ql:
            return "Masse salariale brute : 1 250 000 €."          # faux
        if "bella" in ql:
            return "Masse salariale : 512 340 €."                  # invente
        if "cotisations" in ql:
            return "Sur le brut. Source : PROC-PAIE-99."           # source bidon
        return "Je ne sais pas."

    AGENTS = {"agent_correct": agent_correct, "agent_bugge": agent_bugge}
    return (AGENTS,)


@app.cell
def _(GOLD, pd):
    def run_eval(agent_fn):
        rows = []
        for cas in GOLD:
            ans = agent_fn(cas["question"])
            rows.append({"id": cas["id"], "type": cas["type"],
                         "PASS": bool(cas["check"](ans)), "réponse": ans})
        return pd.DataFrame(rows)
    return (run_eval,)


@app.cell
def _(mo):
    mo.md(
        r"""
        ## ① Notion 2 — Faire *échouer* un agent qui invente

        Deux agents simulés (aucun LLM) : un **correct**, un **buggé** (chiffre faux,
        invention sur donnée absente, source inexistante). Choisissez-en un :
        """
    )
    return


@app.cell
def _(mo):
    choix_agent = mo.ui.dropdown(
        options=["agent_correct", "agent_bugge"], value="agent_bugge",
        label="Agent à évaluer")
    choix_agent
    return (choix_agent,)


@app.cell
def _(AGENTS, choix_agent, run_eval):
    resultats = run_eval(AGENTS[choix_agent.value])
    resultats
    return (resultats,)


@app.cell
def _(choix_agent, mo, resultats):
    _score = resultats["PASS"].mean()
    mo.callout(
        mo.md(f"**Scorecard — {choix_agent.value} : "
              f"{int(resultats['PASS'].sum())}/{len(resultats)} "
              f"({_score:.0%})**"),
        kind="success" if _score == 1 else "danger",
    )
    return


@app.cell
def _(mo):
    mo.md(
        r"""
        ## ⑤ Commentaire

        Basculez sur `agent_bugge` : le harnais l'attrape sur les **trois** axes — le
        chiffre faux, l'invention sur donnée absente, **et** la source `PROC-PAIE-99` qui
        n'existe pas. C'est *ça*, la rigueur d'ingénieur : les limites ne sont pas
        « identifiées à la main », elles **tombent d'un test**.

        **Pour aller plus loin** : branchez un vrai agent LLM
        (`run_eval(lambda q: run_agent(q)[0])`), lancez-le à `temperature` 0 puis 0.7, et
        comparez la **stabilité** des scores — une propriété que le no-code ne montre jamais.

        ---
        ### ✅ Récap J7
        - Vérité terrain **calculée**, jamais recopiée.
        - Quatre axes : chiffre · refus · source · minimisation (RGPD).
        - La scorecard **rejouable** remplace l'opinion « ça a l'air fiable ».
        """
    )
    return


if __name__ == "__main__":
    app.run()
