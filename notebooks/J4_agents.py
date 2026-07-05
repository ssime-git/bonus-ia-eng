# /// script
# requires-python = ">=3.10"
# dependencies = ["marimo", "pandas>=2.0"]
# ///
"""J4 · Concevoir un agent en Python, simplement — notebook-cours autoportant."""
import marimo

__generated_with = "0.9.27"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        # J4 · Concevoir un agent IA en Python — *simplement*

        ### Ce que vous saurez faire à la fin de ce notebook
        - Expliquer, avec vos mots, **ce qu'est un agent** (et ce qu'il n'est pas).
        - Écrire un **outil** que l'agent peut utiliser (c'est juste une fonction Python).
        - Comprendre le **function calling** : comment un modèle *décide* d'appeler un outil.
        - Assembler la **boucle d'un agent** — une vingtaine de lignes — et lire sa trace.

        ### Comment utiliser ce notebook
        Il se lit **de haut en bas**, comme un cours. Vous rencontrerez :

        - des **explications** (comme ce texte) — lisez-les tranquillement ;
        - des **cellules de code** que vous pouvez exécuter **et modifier** librement ;
        - des blocs **🎯 Exercice** : essayez d'abord par vous-même ;
        - des blocs **🔓 Solution** repliés : dépliez-les *après* avoir cherché.

        > Tout est **autoportant** : les données d'exemple sont incluses dans le notebook,
        > rien à installer ni à télécharger. Aucune clé d'IA n'est nécessaire pour le cœur
        > du cours — nous *simulerons* le modèle pour bien voir la mécanique. En fin de
        > notebook, vous pourrez brancher un **vrai modèle** (gratuit, via Groq) en collant
        > simplement une clé.
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ---
        ## Le décor : un mini-audit de paie

        Nous travaillons sur un **petit extrait anonymisé** de bulletins de paie de
        quelques restaurants (données d'exemple, montants mensuels bruts). Notre agent
        jouera le rôle d'un **assistant d'audit** : répondre à des questions sur ces
        données *sans jamais inventer un chiffre*.

        La cellule ci-dessous crée le jeu de données `df`. Exécutez-la et regardez.
        """
    )
    return


@app.cell
def _():
    import pandas as pd
    from io import StringIO

    # ── Données d'exemple embarquées (autoportant : aucune source externe) ──
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
    return df, pd


@app.cell
def _(df):
    df
    return


@app.cell(hide_code=True)
def _(df, mo):
    mo.md(
        f"""
        Notre jeu d'exemple contient **{len(df)} bulletins** répartis sur
        **{df['Etablissement'].nunique()} établissements** :
        {", ".join(df['Etablissement'].unique())}.
        Colonnes : `Etablissement`, `Matricule` (pseudonyme), `Sexe`, `Brut` (mensuel, €).
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ---
        # 1. C'est quoi un « agent », au juste ?

        On confond souvent trois choses. Prenons-les dans l'ordre.

        - **Un chat** répond avec ce qu'il *sait déjà* (son entraînement). Si vous lui
          demandez la masse salariale d'un restaurant, il **devine** — et se trompe.
        - **Une chaîne** suit un chemin **fixe**, imposé par vous : toujours les mêmes
          étapes, dans le même ordre.
        - **Un agent** peut **décider lui-même** d'aller chercher une information ou de
          faire un calcul, en utilisant des **outils** que vous lui donnez, *avant* de
          répondre.

        La différence n'est donc **pas** la puissance du modèle. C'est **qui décide quoi
        faire**. Un agent, c'est un modèle à qui on a donné des outils **et** le droit de
        choisir de s'en servir.
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""Voici le modèle mental que nous allons construire, brique par brique :""")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.mermaid(
        """
        graph LR
            U[Question de l'auditeur] --> M{{Le modèle décide}}
            M -- « je sais répondre » --> R[Réponse]
            M -- « j'ai besoin d'un outil » --> T[Appel d'un outil]
            T --> E[Le programme exécute l'outil]
            E -- résultat --> M
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        Trois briques, donc, que nous allons coder une par une :

        1. **les outils** — de simples fonctions Python (section 2) ;
        2. **la décision** — comment le modèle choisit un outil (section 3) ;
        3. **la boucle** — le programme qui fait tourner le tout (section 4).
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ---
        # 2. Première brique : un outil, c'est une fonction

        Un « outil », dans le monde des agents, ça a l'air sophistiqué. En réalité c'est
        **une fonction Python ordinaire**. Rien de plus. Ce qui la rend spéciale, c'est
        qu'on va la *décrire* au modèle pour qu'il sache qu'elle existe et à quoi elle sert.

        Notre premier outil va calculer la **masse salariale** d'un établissement : la
        somme des bruts. Un calcul **exact**, que le modèle ne doit surtout pas faire de
        tête.

        ## La syntaxe, expliquée

        ```python
        def masse_salariale(etablissement: str) -> str:
            # 1. filtrer les lignes de cet établissement
            sous_ensemble = df[df["Etablissement"] == etablissement]
            # 2. faire le calcul exact
            total = sous_ensemble["Brut"].sum()
            # 3. renvoyer un texte clair (l'agent lira ce texte)
            return f"Masse salariale de {etablissement} : {total} €"
        ```

        Deux points importants :

        - un outil **renvoie du texte** (ou du JSON) : c'est ce que l'agent va *lire* ;
        - un bon outil **gère les cas d'erreur** — ici, un établissement qui n'existe pas.
          C'est ce qui empêche l'agent d'inventer.
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.callout(
        mo.md(
            r"""
            ## 🎯 Exercice 1 — votre premier outil

            **Ce qu'on cherche à faire :** écrire la fonction `masse_salariale` pour qu'elle
            calcule le total des bruts d'un établissement, **et** qu'elle réponde proprement
            si l'établissement est inconnu.

            ```
            entrée : "Le Chaudron"
                       │
                       ▼
              [ filtrer df sur Etablissement ]
                       │
                 établissement connu ?
                   ├─ oui ─► somme des Brut ─► "Masse salariale : 14780 €"
                   └─ non ─► "établissement inconnu : ..."
            ```

            **À vous :** essayez de l'écrire dans la cellule juste en dessous (elle contient
            un squelette à compléter). Testez avec `"Le Chaudron"`, puis avec `"Chez Paul"`
            (qui n'existe pas). Cherchez un peu **avant** de dérouler la solution.
            """
        ),
        kind="info",
    )
    return


@app.cell
def _(df):
    # ✏️  À TOI DE JOUER — complète cette fonction, puis exécute la cellule.
    #     (tu peux la réécrire entièrement : c'est ton bac à sable)

    def masse_salariale(etablissement: str) -> str:
        sous_ensemble = df[df["Etablissement"] == etablissement]
        if len(sous_ensemble) == 0:
            dispo = ", ".join(sorted(df["Etablissement"].unique()))
            return f"Établissement inconnu. Disponibles : {dispo}"
        total = int(sous_ensemble["Brut"].sum())
        return f"Masse salariale de {etablissement} : {total} €"

    # petit test rapide :
    masse_salariale("Le Chaudron")
    return (masse_salariale,)


@app.cell(hide_code=True)
def _(df, mo):
    # La solution est EXÉCUTÉE ici même : le code affiché est garanti fonctionnel.
    _code = '''
    def masse_salariale(etablissement: str) -> str:
        sous_ensemble = df[df["Etablissement"] == etablissement]
        if len(sous_ensemble) == 0:               # cas d'erreur d'abord
            dispo = ", ".join(sorted(df["Etablissement"].unique()))
            return f"Établissement inconnu. Disponibles : {dispo}"
        total = int(sous_ensemble["Brut"].sum())  # calcul exact
        return f"Masse salariale de {etablissement} : {total} €"
'''
    _code = __import__('textwrap').dedent(_code)
    _ns = {"df": df}
    exec(_code, _ns)
    _sol = _ns["masse_salariale"]
    mo.accordion(
        {
            "🔓 Solution — Exercice 1 (déplier après avoir cherché)": mo.md(
                "Le code complet — **exécuté en direct** dans cette cellule :\n\n"
                + "```python\n" + _code.strip() + "\n```\n\n"
                + "**Tests, calculés à l'instant :**\n\n"
                + '- `masse_salariale("Le Chaudron")` → *' + _sol("Le Chaudron") + "*\n"
                + '- `masse_salariale("Chez Paul")` → *' + _sol("Chez Paul") + "*\n\n"
                + "**Pourquoi gérer l'erreur en premier ?** Parce que c'est ce garde-fou "
                + "qui, plus tard, empêchera l'agent d'inventer un chiffre pour un "
                + "restaurant qu'il ne connaît pas. Un outil qui « échoue proprement » "
                + "vaut mieux qu'un outil qui renvoie n'importe quoi."
            )
        }
    )
    return


@app.cell(hide_code=True)
def _(masse_salariale, mo):
    mo.md(
        f"""
        **Vérifions les deux cas :**

        - `masse_salariale("Le Chaudron")` → *{masse_salariale("Le Chaudron")}*
        - `masse_salariale("Chez Paul")` → *{masse_salariale("Chez Paul")}*

        Remarquez : **aucun modèle d'IA n'est intervenu**. Un outil, c'est du Python normal
        et déterministe. Le modèle, lui, ne fera que *choisir* de l'appeler. C'est l'objet
        de la section suivante.
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ---
        # 3. Deuxième brique : comment le modèle « décide »

        Un vrai modèle de langage (GPT, Claude…) sait faire une chose très utile appelée
        **function calling** : on lui présente la *liste des outils disponibles* (leur nom,
        ce qu'ils font, leurs paramètres), et il répond **soit** par du texte, **soit** par
        « appelle l'outil `X` avec ces arguments ».

        Il ne *lance* pas l'outil lui-même — il ne fait que le **nommer**. C'est votre
        programme qui l'exécute. Retenez cette phrase :

        > **Le modèle nomme l'outil ; le programme l'exécute.**

        Comme nous n'utilisons pas de clé d'IA ici, nous allons **simuler** ce modèle par
        une petite fonction. Elle regarde la question et « décide » — exactement comme le
        ferait un vrai modèle, en plus prévisible. Cela nous permet de comprendre la
        mécanique sans dépendre d'un service externe.
        """
    )
    return


@app.cell
def _():
    # Le "modèle" simulé : il reçoit la question et renvoie SA DÉCISION.
    # Deux formes de décision possibles, comme un vrai function calling :
    #   {"outil": "...", "arguments": {...}}   → il veut utiliser un outil
    #   {"reponse": "..."}                      → il répond directement
    def modele_simule(question: str) -> dict:
        q = question.lower()
        for etab in ["le chaudron", "brasserie dorée", "maison favreau", "au fil des saisons"]:
            if etab in q and ("masse" in q or "salaria" in q or "brut" in q):
                # il reconnaît un besoin de donnée chiffrée → il demande l'outil
                nom_propre = {"le chaudron": "Le Chaudron", "brasserie dorée": "Brasserie Dorée",
                              "maison favreau": "Maison Favreau", "au fil des saisons": "Au Fil des Saisons"}[etab]
                return {"outil": "masse_salariale", "arguments": {"etablissement": nom_propre}}
        # sinon, il répond de lui-même
        return {"reponse": "Je n'ai pas d'outil pour cette question — je préfère m'abstenir."}

    return (modele_simule,)


@app.cell(hide_code=True)
def _(mo, modele_simule):
    mo.md(
        f"""
        Regardons ce que « décide » notre modèle simulé sur deux questions :

        - « Quelle est la **masse salariale du Chaudron** ? »
          → `{modele_simule("Quelle est la masse salariale du Chaudron ?")}`
        - « Quel temps fait-il ? »
          → `{modele_simule("Quel temps fait-il ?")}`

        Dans le premier cas, il **demande l'outil** `masse_salariale` avec le bon argument.
        Dans le second, il **répond directement**. C'est *exactement* le comportement d'un
        vrai modèle en function calling — nous avons juste rendu la décision lisible.
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ---
        # 4. Troisième brique : la boucle de l'agent

        Nous avons un **outil** (section 2) et un **modèle qui décide** (section 3). Il ne
        manque que le chef d'orchestre : une **boucle** qui répète le cycle jusqu'à obtenir
        une réponse. On l'appelle parfois le *harnais*.

        Le cycle, étape par étape :

        ```
          ┌───────────────────────────────────────────────────────────┐
          │  1. on demande sa décision au modèle                       │
          │  2. décision = "réponse" ?  ──► on renvoie la réponse. FIN │
          │  3. décision = "outil" ?    ──► on exécute l'outil,        │
          │                                 on note le résultat,       │
          │                                 et on RECOMMENCE (retour 1)│
          └───────────────────────────────────────────────────────────┘
        ```

        Chaque passage dans la boucle est un « tour ». À chaque tour, soit l'agent conclut,
        soit il utilise un outil et continue. On garde une **trace** de tout ce qu'il fait :
        c'est la piste d'audit.
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.callout(
        mo.md(
            r"""
            ## 🎯 Exercice 2 — assemblez la boucle

            **Ce qu'on cherche à faire :** écrire `executer_agent(question)` qui applique le
            cycle ci-dessus. On vous fournit :

            - `modele_simule(question)` → la décision du modèle (`{"outil":...}` ou `{"reponse":...}`) ;
            - `OUTILS` → un dictionnaire `{"masse_salariale": la_fonction}` pour retrouver
              un outil par son nom.

            **Le squelette à compléter est dans la cellule ci-dessous.** Objectif : renvoyer
            la réponse finale **et** la trace des outils utilisés. Cherchez avant de dérouler
            la solution.
            """
        ),
        kind="info",
    )
    return


@app.cell
def _(masse_salariale, modele_simule):
    # Le registre d'outils : le programme s'en sert pour retrouver une fonction par son nom.
    OUTILS = {"masse_salariale": masse_salariale}

    # ✏️  À TOI DE JOUER — complète la boucle (une version qui marche est fournie ;
    #     essaie de la réécrire de mémoire, ou modifie-la pour expérimenter).
    def executer_agent(question: str, max_tours: int = 4):
        trace = []
        for tour in range(1, max_tours + 1):
            decision = modele_simule(question)            # 1. demander au modèle
            if "reponse" in decision:                     # 2. réponse directe ? → fin
                return decision["reponse"], trace
            nom = decision["outil"]                        # 3. sinon, exécuter l'outil
            args = decision["arguments"]
            resultat = OUTILS[nom](**args)                #    (le programme exécute)
            trace.append({"tour": tour, "outil": nom, "arguments": args, "resultat": resultat})
            # Ici, notre modèle simulé conclut après un outil : on renvoie le résultat.
            return resultat, trace
        return "Trop de tours — on s'arrête.", trace

    reponse, trace = executer_agent("Quelle est la masse salariale du Chaudron ?")
    {"réponse": reponse, "trace": trace}
    return OUTILS, executer_agent, reponse, trace


@app.cell(hide_code=True)
def _(masse_salariale, mo, modele_simule):
    # La solution est EXÉCUTÉE ici même : le code affiché est garanti fonctionnel.
    _code = '''
    OUTILS = {"masse_salariale": masse_salariale}

    def executer_agent(question, max_tours=4):
        trace = []
        for tour in range(1, max_tours + 1):
            decision = modele_simule(question)     # 1. décision du modèle
            if "reponse" in decision:              # 2. il répond → FIN
                return decision["reponse"], trace
            nom  = decision["outil"]               # 3. il demande un outil
            args = decision["arguments"]
            resultat = OUTILS[nom](**args)         #    le programme l'exécute
            trace.append({"tour": tour, "outil": nom,
                          "arguments": args, "resultat": resultat})
            return resultat, trace                 # (notre modèle conclut ici)
        return "Trop de tours.", trace
'''
    _code = __import__('textwrap').dedent(_code)
    _ns = {"masse_salariale": masse_salariale, "modele_simule": modele_simule}
    exec(_code, _ns)
    _reponse, _trace = _ns["executer_agent"]("Quelle est la masse salariale du Chaudron ?")
    mo.accordion(
        {
            "🔓 Solution — Exercice 2 (déplier après avoir cherché)": mo.md(
                "Le code complet — **exécuté en direct** dans cette cellule :\n\n"
                + "```python\n" + _code.strip() + "\n```\n\n"
                + "**Test, calculé à l'instant** — `executer_agent(\"Quelle est la masse "
                + "salariale du Chaudron ?\")` renvoie :\n\n"
                + "- réponse : *" + str(_reponse) + "*\n"
                + "- trace : `" + str(_trace) + "`\n\n"
                + "**Les deux lignes qui font tout le travail :**\n\n"
                + '- `if "reponse" in decision:` → c\'est la **condition de sortie**. '
                + "C'est *toute* la logique « l'agent a-t-il fini ? ».\n"
                + "- `OUTILS[nom](**args)` → c'est **le programme qui exécute** ce que le "
                + "modèle a seulement nommé. La séparation *décider / exécuter* est le cœur "
                + "d'un agent.\n\n"
                + "> Dans un vrai agent, on ne fait pas `return` juste après l'outil : on "
                + "renvoie le résultat **au modèle** et on reboucle, pour qu'il puisse "
                + "enchaîner plusieurs outils (ex. chercher *puis* calculer). Notre modèle "
                + "simulé conclut en un tour pour rester lisible."
            )
        }
    )
    return


@app.cell(hide_code=True)
def _(mo, trace):
    mo.md(
        f"""
        ## La trace : votre piste d'audit

        Voici ce que l'agent a fait, tour par tour :

        ```json
        {trace}
        ```

        On voit **quel outil** a produit **quel chiffre**, à partir de **quels arguments**.
        C'est précisément ce qu'affiche Flowise sous le nom d'*intermediate steps*. En audit,
        cette trace n'est pas un détail technique : c'est la **preuve** de comment le résultat
        a été obtenu.
        """
    )
    return


@app.cell(hide_code=True)
def _(executer_agent, mo):
    mo.md(
        f"""
        ### Essayez vous-même

        Modifiez la question passée à `executer_agent(...)` dans la cellule d'exercice, ou
        testez ici mentalement le comportement :

        - question sur un établissement connu → l'agent appelle l'outil :
          *{executer_agent("masse salariale de la Brasserie Dorée")[0]}*
        - question hors sujet → l'agent s'abstient :
          *{executer_agent("Quel est le sens de la vie ?")[0]}*

        L'agent **ne devine jamais** : soit il a un outil et l'utilise, soit il le dit.
        C'est ça, un agent d'audit digne de confiance.
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ---
        # 5. Et avec un vrai modèle d'IA ?

        Tout ce que nous avons construit reste identique. La **seule** chose qui change,
        c'est la brique « décision » : on remplace `modele_simule(question)` par un appel
        à un vrai modèle. Le schéma d'un vrai appel (format OpenAI) ressemble à ceci :

        ```python
        from openai import OpenAI
        client = OpenAI(api_key="...")

        reponse = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Tu es un assistant d'audit paie. "
                                               "N'invente jamais un chiffre : utilise les outils."},
                {"role": "user", "content": question},
            ],
            tools=[{                                   # on DÉCRIT l'outil au modèle
                "type": "function",
                "function": {
                    "name": "masse_salariale",
                    "description": "Masse salariale brute d'un établissement.",
                    "parameters": {"type": "object",
                        "properties": {"etablissement": {"type": "string"}},
                        "required": ["etablissement"]},
                }
            }],
        )
        # reponse.choices[0].message.tool_calls  ← le modèle NOMME l'outil, comme notre simulé
        ```

        Le **prompt système** (`"role": "system"`) est ce qui transforme un modèle
        généraliste en assistant d'audit prudent : c'est là qu'on écrit *« n'invente jamais
        un chiffre »*. La boucle, les outils, la trace : **tout le reste ne bouge pas**.

        Une version complète, prête à exécuter avec une clé, est fournie dans
        `code/j4_agent.py` du dépôt.

        ## Essayez avec un vrai modèle — maintenant

        Ci-dessous, le **même agent**, mais dont la décision est prise par un vrai modèle
        (Llama 3.3 70B servi par [Groq](https://console.groq.com), gratuit). Collez une clé
        d'API — celle distribuée par votre formateur, ou la vôtre créée en 2 minutes sur
        console.groq.com — posez une question, et comparez la trace avec celle du modèle
        simulé.

        > 🔒 La clé reste dans votre navigateur : elle n'est ni enregistrée ni publiée.
        > En local (`marimo edit`), vous pouvez aussi laisser le champ vide et mettre
        > `GROQ_API_KEY` dans un fichier `.env` (voir `.env_template` du dépôt).
        """
    )
    return


@app.cell
def _(mo):
    cle_groq = mo.ui.text(kind="password", label="🔑 Clé Groq (gsk_…)", full_width=True)
    question_reelle = mo.ui.text(
        value="Quelle est la masse salariale du Chaudron ?",
        label="❓ Votre question", full_width=True,
    )
    lancer = mo.ui.run_button(label="Interroger le vrai modèle")
    mo.vstack([cle_groq, question_reelle, lancer])
    return cle_groq, lancer, question_reelle


@app.cell
async def _(OUTILS, cle_groq, lancer, mo, question_reelle):
    import json as _json
    import sys as _sys

    _DESCRIPTION_OUTILS = [{
        "type": "function",
        "function": {
            "name": "masse_salariale",
            "description": "Masse salariale brute mensuelle d'un établissement (restaurant).",
            "parameters": {"type": "object",
                           "properties": {"etablissement": {"type": "string"}},
                           "required": ["etablissement"]},
        },
    }]

    async def _appel_groq(messages: list, cle: str) -> dict:
        """Un appel au modèle (API compatible OpenAI). Marche dans le navigateur ET en local."""
        _payload = {"model": "llama-3.3-70b-versatile", "messages": messages,
                    "tools": _DESCRIPTION_OUTILS}
        _url = "https://api.groq.com/openai/v1/chat/completions"
        _entetes = {"Authorization": f"Bearer {cle}", "Content-Type": "application/json"}
        if _sys.platform == "emscripten":  # navigateur (WASM)
            from pyodide.http import pyfetch
            _rep = await pyfetch(_url, method="POST", headers=_entetes,
                                 body=_json.dumps(_payload))
            return await _rep.json()
        import urllib.request  # exécution locale (marimo edit)
        _entetes["User-Agent"] = "marimo-notebook/1.0"  # l'UA python-urllib est bloqué
        _req = urllib.request.Request(_url, data=_json.dumps(_payload).encode(),
                                      headers=_entetes)
        try:
            with urllib.request.urlopen(_req) as _f:
                return _json.loads(_f.read())
        except urllib.error.HTTPError as _e:  # renvoyer l'erreur API, lisible
            _corps = _e.read().decode("utf-8", "replace")
            try:
                return _json.loads(_corps)
            except Exception:
                return {"error": {"message": f"HTTP {_e.code} : {_corps[:200]}"}}

    async def _agent_reel(question: str, cle: str, max_tours: int = 4):
        """LA MÊME boucle qu'avec le modèle simulé — seule la « décision » change."""
        _messages = [
            {"role": "system", "content": "Tu es un assistant d'audit paie. Réponds en "
             "français. N'invente JAMAIS un chiffre : utilise les outils. Si tu n'as pas "
             "d'outil pour répondre, dis-le."},
            {"role": "user", "content": question},
        ]
        _trace = []
        for _tour in range(1, max_tours + 1):
            _data = await _appel_groq(_messages, cle)          # 1. décision du modèle
            if "error" in _data:
                return f"Erreur API : {_data['error'].get('message', _data['error'])}", _trace
            _msg = _data["choices"][0]["message"]
            if not _msg.get("tool_calls"):                     # 2. réponse directe ? → FIN
                return _msg["content"], _trace
            # On ré-envoie une version ASSAINIE du message (l'API refuse parfois
            # ses propres champs additionnels renvoyés tels quels).
            _messages.append({"role": "assistant", "content": _msg.get("content"),
                              "tool_calls": _msg["tool_calls"]})
            for _tc in _msg["tool_calls"]:                     # 3. sinon, exécuter l'outil
                _nom = _tc["function"]["name"]
                _args = _json.loads(_tc["function"]["arguments"])
                _resultat = OUTILS[_nom](**_args)              #    (le programme exécute)
                _trace.append({"tour": _tour, "outil": _nom,
                               "arguments": _args, "resultat": _resultat})
                _messages.append({"role": "tool", "tool_call_id": _tc["id"],
                                  "content": _resultat})       # 4. résultat → modèle, on reboucle
        return "Trop de tours — on s'arrête.", _trace

    def _cle_locale() -> str:
        """En local seulement : lit GROQ_API_KEY / LLM_API_KEY (environnement ou .env)."""
        if _sys.platform == "emscripten":  # navigateur : uniquement le champ ci-dessus
            return ""
        import os as _os
        import pathlib as _pathlib
        _cle = _os.environ.get("GROQ_API_KEY") or _os.environ.get("LLM_API_KEY")
        if _cle:
            return _cle
        for _dossier in (_pathlib.Path.cwd(), *_pathlib.Path.cwd().parents):
            _fichier = _dossier / ".env"
            if _fichier.exists():
                for _ligne in _fichier.read_text(encoding="utf-8").splitlines():
                    _nom, _, _val = _ligne.partition("=")
                    if _nom.strip() in ("GROQ_API_KEY", "LLM_API_KEY") and _val.strip():
                        return _val.strip().strip('"').strip("'")
        return ""

    _cle_active = cle_groq.value.strip() or _cle_locale()
    mo.stop(
        not lancer.value,
        mo.callout(mo.md("Collez une clé (ou, en local, renseignez `GROQ_API_KEY` dans "
                         "un `.env` — voir `.env_template`), puis cliquez "
                         "**Interroger le vrai modèle**."),
                   kind="neutral"),
    )
    mo.stop(
        not _cle_active,
        mo.callout(mo.md("⚠️ Il manque la clé Groq : collez-la dans le champ `gsk_…` "
                         "ci-dessus (ou, en local, dans un `.env` — voir "
                         "`.env_template`)."),
                   kind="warn"),
    )
    try:
        _reponse_ia, _trace_ia = await _agent_reel(question_reelle.value, _cle_active)
    except Exception as _e:
        _reponse_ia, _trace_ia = f"Échec de l'appel ({type(_e).__name__}) : {_e}", []
    _citation = "> " + str(_reponse_ia).replace("\n", "\n> ")
    mo.md(
        "**Réponse du vrai modèle :**\n\n"
        + _citation + "\n\n"
        + "**Trace (piste d'audit) :** `" + str(_trace_ia) + "`\n\n"
        + "Comparez avec le modèle simulé : même boucle, même trace — seule la "
        + "« décision » est devenue intelligente (et capable d'enchaîner plusieurs "
        + "outils !). Essayez : *« Compare la masse salariale du Chaudron et de la "
        + "Maison Favreau »*."
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ---
        ## ✅ Ce que vous venez de construire

        Un **agent**, entièrement en Python, en trois briques :

        1. **un outil** = une fonction qui filtre, calcule, et renvoie du texte (+ un garde-fou) ;
        2. **une décision** = le modèle qui *nomme* un outil ou répond (le *function calling*) ;
        3. **une boucle** = le programme qui exécute et garde la **trace**.

        La grande idée à emporter : **un agent n'est pas magique**. C'est une boucle autour
        d'un modèle à qui on a donné des outils et le droit de choisir. Vous savez maintenant
        ce qu'il y a *sous le capot* de Flowise.

        ### Pour aller plus loin (si vous êtes à l'aise)
        - Ajoutez un **deuxième outil** `compte_effectif(etablissement)` (nombre de bulletins
          + répartition H/F) et enseignez-le au modèle simulé.
        - Renforcez le garde-fou : que doit répondre l'agent si on lui demande la masse
          salariale d'un établissement absent ? Vérifiez qu'il **refuse** au lieu d'inventer.
        """
    )
    return


if __name__ == "__main__":
    app.run()
