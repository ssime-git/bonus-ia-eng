# /// script
# requires-python = ">=3.10"
# dependencies = ["marimo", "pandas>=2.0"]
# ///
"""J7 · Vérifier qu'un agent est fiable — notebook autoportant."""
import marimo

__generated_with = "0.9.27"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _(mo):
    mo.md(
        r"""
        # J7 · Vérifier qu'un agent est *fiable* (au lieu de l'espérer)

        ### Ce que vous saurez faire à la fin
        - Expliquer pourquoi « ça a l'air de marcher » n'est pas une preuve de fiabilité.
        - Écrire des **questions-tests** dont la **bonne réponse est calculée** sur les données.
        - Écrire des **vérificateurs** : exactitude d'un chiffre, **refus** d'inventer,
          **détection d'une source inventée** (hallucination).
        - Produire une **note de fiabilité** reproductible qui *attrape* un agent défaillant.

        ### Mode d'emploi
        Cours à lire de haut en bas. **🎯 Exercice** = à vous ; **🔓 Solution** = à déplier
        après. **Autoportant** : données incluses, aucune clé d'IA.
        """
    )
    return


@app.cell
def _():
    import pandas as pd
    import re
    from io import StringIO

    _CSV = """Etablissement,Matricule,Sexe,Brut
Le Chaudron,C001,M,2450
Le Chaudron,C002,F,2100
Le Chaudron,C003,M,3200
Le Chaudron,C004,F,1950
Le Chaudron,C005,M,2780
Le Chaudron,C006,F,2300
Brasserie Dorée,B001,M,4200
Brasserie Dorée,B002,F,3800
Brasserie Dorée,B003,M,5100
Brasserie Dorée,B004,F,2600
Brasserie Dorée,B005,M,3400
Maison Favreau,F001,F,2200
Maison Favreau,F002,M,2600
Maison Favreau,F003,F,1900
Maison Favreau,F004,M,3100
Au Fil des Saisons,S001,F,2050
Au Fil des Saisons,S002,M,2400
Au Fil des Saisons,S003,F,2750
Au Fil des Saisons,S004,M,2900
Au Fil des Saisons,S005,F,1850
Au Fil des Saisons,S006,M,3300
"""
    df = pd.read_csv(StringIO(_CSV))
    return df, pd, re


@app.cell
def _(mo):
    mo.md(
        r"""
        ---
        # 1. Le problème : une démo qui marche ne prouve rien

        Un agent qui répond juste **une fois** peut se tromper la fois suivante. En audit,
        on ne se contente pas de « ça a l'air bon » : on **mesure** la fiabilité, et on peut
        la **rejouer** à volonté. C'est la différence entre une intuition et une preuve.

        L'outil pour ça s'appelle un **harnais d'évaluation** :

        ```
          question ──► [ AGENT ] ──► réponse ──► [ VÉRIFICATEUR ] ──► ✅ / ❌
                                                       ▲
                                          bonne réponse CALCULÉE sur les données
        ```

        Le secret : la bonne réponse (la « vérité terrain ») est **calculée** sur `df`,
        jamais recopiée à la main — sinon on ne teste que sa propre erreur.
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        r"""
        ---
        # 2. Vérité terrain + questions-tests

        On calcule la vérité directement depuis les données :

        ```python
        def masse(etab):
            return int(df[df["Etablissement"] == etab]["Brut"].sum())
        ```

        Puis on définit des **questions-tests** (« golden questions »), chacune avec un
        **vérificateur** qui dit si une réponse est acceptable. Trois familles nous
        intéressent particulièrement en audit :

        - **chiffre** — la réponse contient-elle le bon montant ?
        - **refus** — face à une donnée absente, l'agent dit-il « je ne sais pas » ?
        - **source** — toute source *citée* existe-t-elle vraiment ? (sinon = hallucination)
        """
    )
    return


@app.cell
def _(df, re):
    # Vérité terrain — calculée, jamais devinée
    def masse(etab):
        return int(df[df["Etablissement"] == etab]["Brut"].sum())

    def nombre_dans(texte):
        """Extrait le dernier nombre d'une phrase (ex. 'total : 14 780 €' -> 14780)."""
        trouve = re.findall(r"\d[\d\s]*", texte)
        return int(re.sub(r"\s", "", trouve[-1])) if trouve else None

    SOURCES_VALIDES = {"PROC-PAIE-01", "PROC-PAIE-02"}  # les seules sources citables
    return SOURCES_VALIDES, masse, nombre_dans


@app.cell
def _(mo):
    mo.callout(
        mo.md(
            r"""
            ## 🎯 Exercice — écrivez deux vérificateurs

            **Ce qu'on cherche à faire :** deux fonctions qui prennent une réponse (texte) et
            renvoient `True`/`False`.

            1. `verif_refus(reponse)` → `True` si la réponse **refuse** (contient « ne sais
               pas », « inconnu », « pas de donnée »…). Sert quand la donnée n'existe pas.
            2. `verif_source(reponse)` → `True` si **toutes** les références du type
               `PROC-XXX-00` citées appartiennent à `SOURCES_VALIDES` (sinon = source inventée).

            ```
            "…Source : PROC-PAIE-01"  ─► source connue     ─► ✅
            "…Source : PROC-PAIE-99"  ─► source inventée   ─► ❌ (hallucination attrapée)
            ```

            Complétez la cellule ci-dessous.
            """
        ),
        kind="info",
    )
    return


@app.cell
def _(SOURCES_VALIDES, re):
    # ✏️  À TOI DE JOUER — versions fonctionnelles fournies ; réécris-les pour t'entraîner.
    def verif_refus(reponse: str) -> bool:
        mots = ["ne sais pas", "ne dispose", "inconnu", "pas de donnée", "absente"]
        return any(m in reponse.lower() for m in mots)

    def verif_source(reponse: str) -> bool:
        citees = re.findall(r"PROC-[A-Z]+-\d+", reponse)
        return all(src in SOURCES_VALIDES for src in citees)  # aucune source inventée

    {"refus détecté ?": verif_refus("Je ne dispose pas de cette donnée."),
     "source PROC-PAIE-99 acceptée ?": verif_source("Voir PROC-PAIE-99")}
    return verif_refus, verif_source


@app.cell
def _(mo):
    mo.accordion(
        {
            "🔓 Solution — les deux vérificateurs": mo.md(
                r"""
                ```python
                def verif_refus(reponse):
                    mots = ["ne sais pas", "ne dispose", "inconnu", "pas de donnée", "absente"]
                    return any(m in reponse.lower() for m in mots)

                def verif_source(reponse):
                    citees = re.findall(r"PROC-[A-Z]+-\\d+", reponse)
                    return all(src in SOURCES_VALIDES for src in citees)
                ```

                `verif_source` est le **filet anti-hallucination** : une source citée qui
                n'est pas dans la liste blanche fait **échouer** le test — même si le reste de
                la réponse paraît crédible. C'est souvent là que se cachent les erreurs les
                plus dangereuses en audit.
                """
            )
        }
    )
    return


@app.cell
def _(masse, nombre_dans, verif_refus, verif_source):
    # Le jeu de questions-tests (vérité calculée via masse / vérificateurs)
    QUESTIONS = [
        {"id": "Q1 · chiffre", "question": "Masse salariale du Chaudron ?",
         "verifie": lambda r: nombre_dans(r) == masse("Le Chaudron")},
        {"id": "Q2 · refus", "question": "Masse salariale de la Pizzeria Bella (absente) ?",
         "verifie": verif_refus},
        {"id": "Q3 · source", "question": "Base des cotisations ? Cite ta source.",
         "verifie": lambda r: verif_source(r) and "PROC-PAIE-01" in r},
    ]
    return (QUESTIONS,)


@app.cell
def _(mo):
    mo.md(
        r"""
        ---
        # 3. Le harnais attrape l'agent qui invente

        On évalue deux agents (simulés, sans IA) : un **sérieux** et un **défaillant** (qui
        donne un chiffre faux, invente sur une donnée absente, et cite une source
        inexistante). Le harnais lance chaque question et compte les réussites.

        **Choisissez l'agent à évaluer** et regardez la note bouger :
        """
    )
    return


@app.cell
def _(masse):
    def agent_serieux(q: str) -> str:
        ql = q.lower()
        if "chaudron" in ql:      return f"Masse salariale : {masse('Le Chaudron')} €."
        if "bella" in ql:         return "Je ne dispose pas de données pour cet établissement."
        if "cotisation" in ql:    return "Le brut social. Source : PROC-PAIE-01."
        return "Je ne sais pas."

    def agent_defaillant(q: str) -> str:
        ql = q.lower()
        if "chaudron" in ql:      return "Masse salariale : 9 999 €."        # faux
        if "bella" in ql:         return "Masse salariale : 12 500 €."       # inventé
        if "cotisation" in ql:    return "Le brut. Source : PROC-PAIE-99."   # source bidon
        return "Je ne sais pas."

    AGENTS = {"agent_serieux": agent_serieux, "agent_defaillant": agent_defaillant}
    return (AGENTS,)


@app.cell
def _(QUESTIONS, pd):
    def evaluer(agent) -> pd.DataFrame:
        lignes = []
        for cas in QUESTIONS:
            reponse = agent(cas["question"])
            lignes.append({"test": cas["id"], "réussi": bool(cas["verifie"](reponse)),
                           "réponse de l'agent": reponse})
        return pd.DataFrame(lignes)
    return (evaluer,)


@app.cell
def _(mo):
    choix = mo.ui.dropdown(options=["agent_serieux", "agent_defaillant"],
                           value="agent_defaillant", label="Agent à évaluer")
    choix
    return (choix,)


@app.cell
def _(AGENTS, choix, evaluer):
    resultats = evaluer(AGENTS[choix.value])
    resultats
    return (resultats,)


@app.cell
def _(choix, mo, resultats):
    note = resultats["réussi"].mean()
    mo.callout(
        mo.md(f"**Note de fiabilité — {choix.value} : "
              f"{int(resultats['réussi'].sum())}/{len(resultats)} ({note:.0%})**"),
        kind="success" if note == 1 else "danger",
    )
    return


@app.cell
def _(mo):
    mo.md(
        r"""
        Basculez sur `agent_defaillant` : il tombe à **0/3**. Le harnais l'attrape sur les
        **trois** plans — chiffre faux, invention sur donnée absente, **et** source
        `PROC-PAIE-99` qui n'existe pas. Voilà la rigueur d'ingénieur : les défauts ne sont
        pas « repérés à l'œil », ils **tombent d'un test** qu'on peut relancer après chaque
        modification (non-régression).
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        r"""
        ---
        # 4. Et avec un vrai agent ?

        Le harnais est **agnostique** : il prend n'importe quelle fonction
        `question -> réponse`. Pour noter le vrai agent LLM du J4 :

        ```python
        from j4_agent import run_agent
        resultats = evaluer(lambda q: run_agent(q)[0])
        ```

        Lancez-le deux fois (température 0 puis 0.7) et comparez les notes : vous mesurez la
        **stabilité** — une propriété que le no-code ne montre jamais.

        ---
        ## ✅ À emporter
        - La **vérité terrain** se **calcule**, elle ne se recopie pas.
        - On teste au moins : **exactitude**, **refus** d'inventer, **sources** réelles.
        - Une **note reproductible** remplace « ça a l'air fiable ».
        - Les cas ❌ *sont* votre section « limites identifiées » — écrite automatiquement.
        """
    )
    return


if __name__ == "__main__":
    app.run()
