# /// script
# requires-python = ">=3.10"
# dependencies = ["marimo", "pandas>=2.0"]
# ///
"""J6 · Faire collaborer plusieurs agents (+ validation humaine) — notebook autoportant."""
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
        # J6 · Faire collaborer plusieurs agents — et garder l'humain dans la boucle

        ### Ce que vous saurez faire à la fin
        - Expliquer **pourquoi** un seul agent qui fait tout finit par bâcler.
        - Répartir le travail entre des **workers** spécialisés.
        - Écrire un **superviseur** : une petite *machine à états* qui distribue les tâches.
        - Placer une **validation humaine** (HITL) au bon endroit de la chaîne.

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
    return (df,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ---
        # 1. Pourquoi *plusieurs* agents ?

        Imaginez un auditeur seul chargé, en même temps, de : **chercher** la règle,
        **calculer** un écart, **contrôler** le résultat, puis **rédiger** le rapport.
        Chaque tâche tire son attention dans une direction différente — il finit par bâcler.

        Un agent unique a le même défaut : plus on lui empile de rôles dans un seul prompt,
        moins il est fiable. La parade : **spécialiser**. On confie chaque rôle à un
        *worker* étroit, et un *superviseur* orchestre le tout.

        ```
                         ┌─────────────┐
             demande ──► │ SUPERVISEUR │  (il répartit, il ne fait pas le travail)
                         └──────┬──────┘
               ┌────────────────┼─────────────────┐
               ▼                ▼                  ▼
         ┌──────────┐    ┌──────────┐      ┌──────────┐
         │ Détection│    │ Contrôle │      │ Synthèse │   (workers spécialisés)
         └──────────┘    └──────────┘      └──────────┘
        ```

        Notre scénario d'audit : **détecter** un établissement au salaire moyen anormal,
        **quantifier** l'écart, puis **rédiger** une alerte.
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ---
        # 2. Les workers : trois spécialistes

        Chaque worker reçoit un « état » (un dictionnaire partagé), fait **sa** part, et
        enrichit l'état. Aucun ne déborde sur le rôle d'un autre — c'est ce qui rend la
        chaîne lisible et traçable.

        Lisez et exécutez la cellule : elle définit les trois workers.
        """
    )
    return


@app.cell
def _(df):
    # Worker 1 — DÉTECTION : trouve l'établissement au brut moyen le plus atypique.
    def worker_detection(etat: dict) -> dict:
        moyennes = df.groupby("Etablissement")["Brut"].mean()
        mediane_secteur = moyennes.median()
        cible = (moyennes / mediane_secteur).idxmax()
        etat["alerte"] = {
            "etablissement": cible,
            "brut_moyen": round(float(moyennes[cible])),
            "mediane_secteur": round(float(mediane_secteur)),
            "ratio": round(float(moyennes[cible] / mediane_secteur), 2),
        }
        return etat

    # Worker 2 — CONTRÔLE : quantifie l'ampleur (nb de bulletins, part au-dessus d'un seuil).
    def worker_controle(etat: dict) -> dict:
        cible = etat["alerte"]["etablissement"]
        sous = df[df["Etablissement"] == cible]
        etat["controle"] = {
            "nb_bulletins": int(len(sous)),
            "brut_max": int(sous["Brut"].max()),
            "part_sup_3500": round(float((sous["Brut"] > 3500).mean()), 2),
        }
        return etat

    # Worker 3 — SYNTHÈSE : rédige l'alerte à partir de l'état.
    def worker_synthese(etat: dict) -> dict:
        a, c = etat["alerte"], etat["controle"]
        etat["rapport"] = (
            f"ALERTE — {a['etablissement']} : brut moyen {a['brut_moyen']} € "
            f"contre {a['mediane_secteur']} € pour le secteur (ratio {a['ratio']}×). "
            f"{c['nb_bulletins']} bulletins, max {c['brut_max']} €. À vérifier."
        )
        return etat

    WORKERS = {"DETECTION": worker_detection, "CONTROLE": worker_controle, "SYNTHESE": worker_synthese}
    return (WORKERS,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ---
        # 3. Le superviseur : une machine à états

        Le superviseur **ne fait pas** le travail. À chaque tour, il **regarde l'état** et
        décide **la prochaine étape** : `DETECTION`, `CONTROLE`, `SYNTHESE`, ou `FIN`. Une
        seule décision par tour. C'est une **machine à états**.

        ```
          état vide            ──► DETECTION
          alerte mais pas de contrôle ──► CONTROLE
          contrôle mais pas de rapport ──► SYNTHESE
          rapport présent      ──► FIN
        ```

        Son gros avantage : il est **déterministe**, donc **testable** (au contraire d'un
        superviseur piloté par un vrai modèle, plus souple mais imprévisible).
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.callout(
        mo.md(
            r"""
            ## 🎯 Exercice — le superviseur et la boucle

            **Ce qu'on cherche à faire :** écrire deux choses.

            1. `superviseur(etat)` → renvoie la prochaine étape (voir le schéma ci-dessus).
            2. `faire_tourner()` → la boucle qui, tant que ≠ `FIN`, appelle le bon worker
               **et journalise** chaque décision (« qui a fait quoi »).

            Complétez la cellule ci-dessous. Le **journal** produit est votre piste d'audit.
            """
        ),
        kind="info",
    )
    return


@app.cell
def _():
    # ✏️  À TOI DE JOUER — complète les deux fonctions, puis exécute la cellule.
    def superviseur(etat: dict) -> str:
        # TODO — la machine à états (voir le schéma plus haut) :
        #   "alerte" absente de etat    → return "DETECTION"
        #   "controle" absente          → return "CONTROLE"
        #   "rapport" absente           → return "SYNTHESE"
        #   sinon                       → return "FIN"
        return "FIN"

    def faire_tourner(max_tours: int = 5):
        etat, journal = {}, []
        # TODO — au plus max_tours fois :
        #   1. etape = superviseur(etat)
        #   2. ajouter {"superviseur_décide": etape} au journal
        #   3. si etape == "FIN" → sortir de la boucle
        #   4. sinon : etat = WORKERS[etape](etat)
        #      et ajouter {"worker_exécuté": etape} au journal
        return etat, journal

    faire_tourner()
    return faire_tourner, superviseur


@app.cell(hide_code=True)
def _(WORKERS, faire_tourner, mo, superviseur):
    # Vérification automatique : la suite du notebook utilise TES fonctions dès
    # qu'elles sont correctes — et une version de référence en attendant.
    def _sup_ref(etat):
        if "alerte" not in etat:
            return "DETECTION"
        if "controle" not in etat:
            return "CONTROLE"
        if "rapport" not in etat:
            return "SYNTHESE"
        return "FIN"

    def _tourner_ref(max_tours=5):
        _etat, _journal = {}, []
        for _ in range(max_tours):
            _etape = _sup_ref(_etat)
            _journal.append({"superviseur_décide": _etape})
            if _etape == "FIN":
                break
            _etat = WORKERS[_etape](_etat)
            _journal.append({"worker_exécuté": _etape})
        return _etat, _journal

    try:
        _routage_ok = all([
            superviseur({}) == "DETECTION",
            superviseur({"alerte": {}}) == "CONTROLE",
            superviseur({"alerte": {}, "controle": {}}) == "SYNTHESE",
            superviseur({"alerte": {}, "controle": {}, "rapport": "x"}) == "FIN",
        ])
        _etat_essai, _journal_essai = faire_tourner()
        _ok = _routage_ok and bool(_etat_essai.get("rapport")) and len(_journal_essai) >= 7
    except Exception:
        _ok = False
    etat_final, journal = (faire_tourner() if _ok else _tourner_ref())
    mo.callout(
        mo.md("✅ **Ton superviseur et ta boucle passent les tests** — ce sont eux qui "
              "produisent le journal ci-dessous."
              if _ok else
              "✏️ **Exercice à compléter** (cellule ci-dessus). En attendant, la suite du "
              "notebook tourne avec une version de référence — cherche, puis compare avec "
              "la 🔓 Solution ci-dessous."),
        kind="success" if _ok else "warn",
    )
    return etat_final, journal


@app.cell(hide_code=True)
def _(WORKERS, mo):
    # La solution est EXÉCUTÉE ici même : le code affiché est garanti fonctionnel.
    _code = '''
    def superviseur(etat):
        if "alerte"   not in etat: return "DETECTION"
        if "controle" not in etat: return "CONTROLE"
        if "rapport"  not in etat: return "SYNTHESE"
        return "FIN"

    def faire_tourner(max_tours=5):
        etat, journal = {}, []
        for _ in range(max_tours):
            etape = superviseur(etat)              # 1. il décide
            journal.append({"superviseur_décide": etape})
            if etape == "FIN":
                break
            etat = WORKERS[etape](etat)            # 2. le worker agit
            journal.append({"worker_exécuté": etape})
        return etat, journal
'''
    _code = __import__('textwrap').dedent(_code)
    _ns = {"WORKERS": WORKERS}
    exec(_code, _ns)
    _etat, _journal = _ns["faire_tourner"]()
    _decisions = " → ".join(next(iter(d.values())) for d in _journal if "superviseur_décide" in d)
    mo.accordion(
        {
            "🔓 Solution — superviseur + boucle": mo.md(
                "Le code complet — **exécuté en direct** dans cette cellule :\n\n"
                + "```python\n" + _code.strip() + "\n```\n\n"
                + "**Test, calculé à l'instant** — `faire_tourner()` déroule bien le "
                + "circuit complet : **" + _decisions + "**, et l'état final contient un "
                + "rapport :\n\n"
                + "> " + str(_etat.get("rapport")) + "\n\n"
                + "Remarquez que le superviseur **ne calcule rien** : il *lit* l'état et "
                + "*oriente*. Toute l'intelligence de coordination tient dans ces quatre "
                + "`if`."
            )
        }
    )
    return


@app.cell(hide_code=True)
def _(etat_final, journal, mo):
    mo.md(
        f"""
        ## Résultat sur nos données

        Le journal montre la circulation, étape par étape :

        ```json
        {journal}
        ```

        Et l'alerte rédigée par le worker Synthèse :

        > {etat_final.get("rapport")}

        Sur notre extrait, la détection pointe **Brasserie Dorée** (salaires nettement plus
        élevés). Le **journal** dit *quel agent a produit quoi* — c'est votre traçabilité.
        """
    )
    return


@app.cell
def _(mo, superviseur):
    # On peut TESTER le superviseur sans rien exécuter d'autre (déterminisme) :
    _tests = [
        superviseur({}) == "DETECTION",
        superviseur({"alerte": {}}) == "CONTROLE",
        superviseur({"alerte": {}, "controle": {}}) == "SYNTHESE",
        superviseur({"alerte": {}, "controle": {}, "rapport": "x"}) == "FIN",
    ]
    mo.callout(
        mo.md(f"**Tests de routing : {sum(_tests)}/4 réussis** "
              + ("✅ — un superviseur à règles se teste en 4 lignes." if all(_tests) else "❌")),
        kind="success" if all(_tests) else "danger",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ---
        # 4. L'humain dans la boucle (HITL)

        Une chaîne d'audit ne doit pas décider seule sur un cas à fort enjeu. On place une
        **validation humaine** — l'auditeur valide ou rejette — **en sortie de chaîne, avant
        toute décision**, et surtout **quand l'enjeu est fort** (un écart qui pourrait
        déclencher un redressement).

        Réglez le **seuil** et l'**interrupteur** ci-dessous : la décision se recalcule toute
        seule. C'est l'équivalent, en notebook, du *node Human Input* de Flowise.
        """
    )
    return


@app.cell
def _(mo):
    seuil = mo.ui.slider(1.0, 8.0, value=1.5, step=0.5,
                         label="Seuil de ratio qui exige une validation humaine")
    valider = mo.ui.switch(label="✅ Auditeur : je valide l'alerte")
    mo.vstack([seuil, valider])
    return seuil, valider


@app.cell
def _(etat_final, mo, seuil, valider):
    ratio = etat_final["alerte"]["ratio"]
    if ratio >= seuil.value:
        decision = "VALIDÉE ✅" if valider.value else "EN ATTENTE ⏸️ (l'auditeur n'a pas encore validé)"
        pourquoi = f"ratio {ratio}× ≥ seuil {seuil.value} → **enjeu fort, humain requis**"
    else:
        decision = "AUTO-VALIDÉE (faible enjeu)"
        pourquoi = f"ratio {ratio}× < seuil {seuil.value} → validation humaine non requise"
    mo.callout(mo.md(f"**Alerte : {decision}**  \n{pourquoi}"),
               kind="success" if "VALID" in decision else "warn")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        La décision humaine (et *pourquoi* elle a été demandée) devrait **entrer dans le
        journal** : en audit, une validation n'est pas un clic perdu, c'est une **trace
        signée**.

        ---
        ## ✅ À emporter
        - Un seul agent qui fait tout = qualité en baisse. **Spécialisez** en workers.
        - Le **superviseur** est une machine à états : il *répartit*, il ne *fait* pas.
        - Chaque worker a **un** rôle → un **journal** « qui a fait quoi » exploitable.
        - Le **HITL** se place sur les cas à fort enjeu, et se journalise.
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ---
        # 5. Essayez avec un vrai modèle — le superviseur devient un LLM

        Notre superviseur à `if` est déterministe et testable. L'alternative « à la mode » :
        confier le **routage** à un vrai modèle (Llama 3.3 70B via
        [Groq](https://console.groq.com), gratuit). À chaque tour, on lui décrit l'état et
        il choisit la prochaine étape. Les **workers ne changent pas** — seul le chef
        d'orchestre est remplacé.

        Comparez le journal obtenu avec celui de la machine à états : souvent identique…
        mais **rien ne le garantit**. C'est tout l'enjeu : un superviseur LLM est plus
        souple, et moins prévisible — il *s'évalue* (J7) là où l'autre se *teste*.

        > 🔒 La clé reste dans votre navigateur : elle n'est ni enregistrée ni publiée.
        > En local (`marimo edit`), vous pouvez laisser le champ vide et mettre
        > `GROQ_API_KEY` dans un fichier `.env` (voir `.env_template` du dépôt).
        """
    )
    return


@app.cell
def _(mo):
    cle_groq = mo.ui.text(kind="password", label="🔑 Clé Groq (gsk_…)", full_width=True)
    lancer = mo.ui.run_button(label="Lancer la chaîne avec un superviseur LLM")
    mo.vstack([cle_groq, lancer])
    return cle_groq, lancer


@app.cell
async def _(WORKERS, cle_groq, lancer, mo):
    import json as _json
    import sys as _sys

    async def _appel_groq(messages: list, cle: str) -> dict:
        """Un appel au modèle (API compatible OpenAI). Marche dans le navigateur ET en local."""
        _payload = {"model": "llama-3.3-70b-versatile", "messages": messages,
                    "temperature": 0}
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

    _CONSIGNE = (
        "Tu es le superviseur d'une chaîne d'audit de paie. Étapes possibles : "
        "DETECTION, CONTROLE, SYNTHESE, FIN. Règles : DETECTION produit la clé 'alerte' ; "
        "CONTROLE (uniquement après 'alerte') produit 'controle' ; SYNTHESE (uniquement "
        "après 'controle') produit 'rapport' ; quand 'rapport' est présent, réponds FIN. "
        "Réponds par UN SEUL mot, sans explication."
    )

    async def _superviseur_llm(etat: dict, cle: str) -> str:
        _cles = sorted(etat.keys()) or ["(état vide)"]
        _data = await _appel_groq([
            {"role": "system", "content": _CONSIGNE},
            {"role": "user", "content": f"Clés présentes dans l'état : {_cles}. "
                                        "Prochaine étape ?"},
        ], cle)
        if "error" in _data:
            raise RuntimeError(_data["error"].get("message", str(_data["error"])))
        _mot = _data["choices"][0]["message"]["content"].strip().upper()
        for _etape in ("DETECTION", "CONTROLE", "SYNTHESE", "FIN"):
            if _etape in _mot:
                return _etape
        return "FIN"  # réponse illisible → on s'arrête proprement

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
                         "**Lancer la chaîne avec un superviseur LLM**."),
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
        _etat, _journal_llm = {}, []
        for _ in range(6):  # garde-fou : un LLM peut boucler, pas notre programme
            _etape = await _superviseur_llm(_etat, _cle_active)
            _journal_llm.append({"superviseur_LLM_décide": _etape})
            if _etape == "FIN":
                break
            _etat = WORKERS[_etape](_etat)
            _journal_llm.append({"worker_exécuté": _etape})
        _erreur = ""
    except Exception as _e:
        _erreur = f"Échec de l'appel ({type(_e).__name__}) : {_e}"
    mo.stop(bool(_erreur), mo.callout(mo.md("⚠️ " + _erreur), kind="danger"))
    _circuit = " → ".join(next(iter(_d.values())) for _d in _journal_llm
                          if "superviseur_LLM_décide" in _d)
    mo.md(
        "**Circuit décidé par le modèle :** " + _circuit + "\n\n"
        + "**Journal complet :** `" + str(_journal_llm) + "`\n\n"
        + "**Rapport produit :**\n\n> " + str(_etat.get("rapport", "(aucun)")) + "\n\n"
        + "Mêmes workers, même journal — seul le **routage** vient du modèle. Relancez "
        + "plusieurs fois : la machine à états donne *toujours* le même circuit ; le LLM, "
        + "*presque* toujours. Cette nuance est exactement ce que le harnais du J7 mesure."
    )
    return


if __name__ == "__main__":
    app.run()
