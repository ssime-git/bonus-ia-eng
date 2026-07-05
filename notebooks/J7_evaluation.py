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


@app.cell(hide_code=True)
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
        après. **Autoportant** : données incluses ; clé d'IA **optionnelle** (uniquement
        pour la section finale « vrai modèle »).
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


@app.cell(hide_code=True)
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


@app.cell(hide_code=True)
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


@app.cell(hide_code=True)
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
def _():
    # ✏️  À TOI DE JOUER — complète les deux vérificateurs, puis exécute la cellule.
    def verif_refus(reponse: str) -> bool:
        # TODO : renvoyer True si la réponse contient un marqueur de refus, parmi :
        # "ne sais pas", "ne dispose", "inconnu", "pas de donnée", "absente"
        # (pense à reponse.lower() ; any(...) rend ça élégant)
        return False

    def verif_source(reponse: str) -> bool:
        # TODO : extraire les références avec re.findall(r"PROC-[A-Z]+-\d+", reponse)
        # et renvoyer True seulement si TOUTES sont dans SOURCES_VALIDES (all(...))
        return False

    {"refus détecté ?": verif_refus("Je ne dispose pas de cette donnée."),
     "source PROC-PAIE-99 acceptée ?": verif_source("Voir PROC-PAIE-99")}
    return verif_refus, verif_source


@app.cell(hide_code=True)
def _(SOURCES_VALIDES, mo, re, verif_refus, verif_source):
    # Vérification automatique : le harnais utilise TES vérificateurs dès
    # qu'ils sont corrects — et une version de référence en attendant.
    def _refus_ref(reponse):
        _mots = ["ne sais pas", "ne dispose", "inconnu", "pas de donnée", "absente"]
        return any(m in reponse.lower() for m in _mots)

    def _source_ref(reponse):
        _citees = re.findall(r"PROC-[A-Z]+-\d+", reponse)
        return all(_src in SOURCES_VALIDES for _src in _citees)

    try:
        _ok = (verif_refus("Je ne dispose pas de cette donnée.") is True
               and verif_refus("La masse salariale est de 14780 €.") is False
               and verif_source("Voir PROC-PAIE-01") is True
               and verif_source("Voir PROC-PAIE-99") is False)
    except Exception:
        _ok = False
    verif_refus_active = verif_refus if _ok else _refus_ref
    verif_source_active = verif_source if _ok else _source_ref
    mo.callout(
        mo.md("✅ **Tes deux vérificateurs passent les tests** — ce sont eux qui notent "
              "les agents ci-dessous."
              if _ok else
              "✏️ **Exercice à compléter** (cellule ci-dessus). En attendant, le harnais "
              "tourne avec des vérificateurs de référence — cherche, puis compare avec "
              "la 🔓 Solution ci-dessous."),
        kind="success" if _ok else "warn",
    )
    return verif_refus_active, verif_source_active


@app.cell(hide_code=True)
def _(SOURCES_VALIDES, mo, re):
    # La solution est EXÉCUTÉE ici même : le code affiché est garanti fonctionnel.
    _code = '''
    def verif_refus(reponse):
        mots = ["ne sais pas", "ne dispose", "inconnu", "pas de donnée", "absente"]
        return any(m in reponse.lower() for m in mots)

    def verif_source(reponse):
        citees = re.findall(r"PROC-[A-Z]+-\\d+", reponse)
        return all(src in SOURCES_VALIDES for src in citees)
'''
    _code = __import__('textwrap').dedent(_code)
    _ns = {"re": re, "SOURCES_VALIDES": SOURCES_VALIDES}
    exec(_code, _ns)
    _refus, _source = _ns["verif_refus"], _ns["verif_source"]
    mo.accordion(
        {
            "🔓 Solution — les deux vérificateurs": mo.md(
                "Le code complet — **exécuté en direct** dans cette cellule :\n\n"
                + "```python\n" + _code.strip() + "\n```\n\n"
                + "**Tests, calculés à l'instant :**\n\n"
                + '- `verif_refus("Je ne dispose pas de cette donnée.")` → `'
                + str(_refus("Je ne dispose pas de cette donnée.")) + "`\n"
                + '- `verif_source("Voir PROC-PAIE-01")` → `'
                + str(_source("Voir PROC-PAIE-01")) + "` (source connue)\n"
                + '- `verif_source("Voir PROC-PAIE-99")` → `'
                + str(_source("Voir PROC-PAIE-99")) + "` (source inventée, attrapée)\n\n"
                + "`verif_source` est le **filet anti-hallucination** : une source citée "
                + "qui n'est pas dans la liste blanche fait **échouer** le test — même si "
                + "le reste de la réponse paraît crédible. C'est souvent là que se cachent "
                + "les erreurs les plus dangereuses en audit."
            )
        }
    )
    return


@app.cell
def _(masse, nombre_dans, verif_refus_active, verif_source_active):
    # Le jeu de questions-tests (vérité calculée via masse / vérificateurs)
    QUESTIONS = [
        {"id": "Q1 · chiffre", "question": "Masse salariale du Chaudron ?",
         "verifie": lambda r: nombre_dans(r) == masse("Le Chaudron")},
        {"id": "Q2 · refus", "question": "Masse salariale de la Pizzeria Bella (absente) ?",
         "verifie": verif_refus_active},
        {"id": "Q3 · source", "question": "Base des cotisations ? Cite ta source.",
         "verifie": lambda r: verif_source_active(r) and "PROC-PAIE-01" in r},
    ]
    return (QUESTIONS,)


@app.cell(hide_code=True)
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


@app.cell(hide_code=True)
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


@app.cell(hide_code=True)
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


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ---
        # 5. Faisons-le vraiment : le harnais note un vrai modèle

        Assez de simulation : notons un **vrai agent LLM** (Llama 3.3 70B via
        [Groq](https://console.groq.com), gratuit) avec **exactement le même harnais** —
        les 3 questions-tests et leurs vérificateurs n'ont pas bougé d'une ligne.

        L'agent reçoit un outil `masse_salariale` (calculé sur `df`) et une consigne
        stricte (« n'invente jamais, cite uniquement PROC-PAIE-01/02 »). Le harnais
        vérifie s'il **respecte** cette consigne. Relancez plusieurs fois : la note
        peut bouger — c'est la **stabilité** que vous mesurez.

        > 🔒 La clé reste dans votre navigateur : elle n'est ni enregistrée ni publiée.
        > En local (`marimo edit`), vous pouvez laisser le champ vide et mettre
        > `GROQ_API_KEY` dans un fichier `.env` (voir `.env_template` du dépôt).
        """
    )
    return


@app.cell
def _(mo):
    cle_groq = mo.ui.text(kind="password", label="🔑 Clé Groq (gsk_…)", full_width=True)
    lancer = mo.ui.run_button(label="Évaluer le vrai modèle (3 questions)")
    mo.vstack([cle_groq, lancer])
    return cle_groq, lancer


@app.cell
async def _(QUESTIONS, cle_groq, df, lancer, mo):
    import json as _json
    import sys as _sys

    def _outil_masse(etablissement: str) -> str:
        _sous = df[df["Etablissement"] == etablissement]
        if len(_sous) == 0:  # échec PROPRE : on liste ce qui existe (le modèle peut se corriger)
            _dispo = ", ".join(sorted(df["Etablissement"].unique()))
            return f"Aucune donnée pour « {etablissement} ». Établissements connus : {_dispo}"
        return f"Masse salariale de {etablissement} : {int(_sous['Brut'].sum())} €"

    _OUTILS = {"masse_salariale": _outil_masse}
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

    async def _agent_reel(question: str, cle: str, max_tours: int = 4) -> str:
        _messages = [
            {"role": "system", "content": "Tu es un assistant d'audit paie. Réponds en "
             "français, brièvement. N'invente JAMAIS un chiffre : utilise l'outil. Si les "
             "données n'existent pas, réponds « Je ne dispose pas de cette donnée. ». "
             "Règle métier : la base de calcul des cotisations est le brut social — "
             "Source : PROC-PAIE-01. Tu ne peux citer que PROC-PAIE-01 ou PROC-PAIE-02."},
            {"role": "user", "content": question},
        ]
        for _tour in range(1, max_tours + 1):
            _data = await _appel_groq(_messages, cle)
            if "error" in _data:
                return f"Erreur API : {_data['error'].get('message', _data['error'])}"
            _msg = _data["choices"][0]["message"]
            if not _msg.get("tool_calls"):
                return _msg["content"]
            # On ré-envoie une version ASSAINIE du message (l'API refuse parfois
            # ses propres champs additionnels renvoyés tels quels).
            _messages.append({"role": "assistant", "content": _msg.get("content"),
                              "tool_calls": _msg["tool_calls"]})
            for _tc in _msg["tool_calls"]:
                _resultat = _OUTILS[_tc["function"]["name"]](
                    **_json.loads(_tc["function"]["arguments"]))
                _messages.append({"role": "tool", "tool_call_id": _tc["id"],
                                  "content": _resultat})
        return "Trop de tours — on s'arrête."

    def _cle_locale() -> str:
        """En local seulement : lit GROQ_API_KEY / LLM_API_KEY (environnement ou .env)."""
        if _sys.platform == "emscripten":
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
                         "**Évaluer le vrai modèle**."),
                   kind="neutral"),
    )
    mo.stop(
        not _cle_active,
        mo.callout(mo.md("⚠️ Il manque la clé Groq : collez-la dans le champ `gsk_…` "
                         "ci-dessus (ou, en local, dans un `.env` — voir "
                         "`.env_template`)."),
                   kind="warn"),
    )
    _lignes = []
    _reussites = 0
    for _q in QUESTIONS:  # LE MÊME harnais que pour les agents simulés
        try:
            _rep = await _agent_reel(_q["question"], _cle_active)
        except Exception as _e:
            _rep = f"Échec de l'appel ({type(_e).__name__}) : {_e}"
        _ok = bool(_q["verifie"](_rep))
        _reussites += _ok
        _rep_courte = str(_rep).replace("\n", " ").replace("|", "/")
        if len(_rep_courte) > 110:
            _rep_courte = _rep_courte[:110] + "…"
        _lignes.append("| " + _q["id"] + " | " + _rep_courte + " | "
                       + ("✅" if _ok else "❌") + " |")
    _note = f"{_reussites}/{len(QUESTIONS)}"
    mo.md(
        "**Note de fiabilité du vrai modèle : " + _note + "**\n\n"
        + "| Question | Réponse du modèle | Verdict |\n|---|---|---|\n"
        + "\n".join(_lignes) + "\n\n"
        + "Le harnais n'a **pas changé** : mêmes questions, mêmes vérificateurs — seul "
        + "l'agent est devenu réel. Relancez pour mesurer la **stabilité**, ou durcissez "
        + "la consigne système et observez la note. Un ❌ ici n'est pas un échec du "
        + "notebook : c'est le harnais qui fait son travail."
    )
    return


if __name__ == "__main__":
    app.run()
