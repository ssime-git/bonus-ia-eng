# /// script
# requires-python = ">=3.10"
# dependencies = ["marimo", "pandas>=2.0"]
# ///
"""J4 · Agents — la boucle agentique sous le capot (notebook-cours marimo)."""
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
        # J4 · Agents — la boucle agentique *sous le capot*

        > **Format** : ce notebook *fusionne la fiche et le code*. Chaque notion suit
        > 5 temps → **① présentation · ② syntaxe · ③ exercice · ④ solution (repliée) ·
        > ⑤ commentaire**. Vous pouvez tout exécuter et tout modifier.

        **Prolonge** les slides J4 : S05 (function calling), S06 (boucle modèle ≠ harnais),
        S08 (anatomie d'un tour), S09/S17 (prompt système).

        Les données de paie LIORA (16 établissements) sont déjà chargées dans `df`.
        """
    )
    return


@app.cell
def _(df, mo):
    mo.md(
        f"""
        ### Données disponibles

        `df` = **{len(df)} bulletins** · **{df['Etablissement'].nunique()} établissements**.
        Colonnes clés : `Etablissement`, `Matricule`, `Sexe`, `Brut`, `Net à payer`…
        """
    )
    return


@app.cell
def _(df):
    df.head(4)
    return


@app.cell
def _(mo):
    mo.md(r"""---""")
    return


# ═══════════════════════════════════════════════════════════════════════════
# NOTION 1 — Un « outil », c'est une fonction + un schéma
# ═══════════════════════════════════════════════════════════════════════════
@app.cell
def _(mo):
    mo.md(
        r"""
        ## ① Notion 1 — Un « outil » n'est pas magique : c'est une fonction

        En slide, on a dit *« le modèle **nomme** un outil, le harnais l'**exécute** »*.
        Côté code, un outil = **une fonction Python** + **un schéma JSON** qui la décrit
        au modèle. Le modèle ne fait que *choisir* de l'appeler ; le calcul, lui, est
        déterministe.

        ```
            ┌─────────────┐   "appelle masse_salariale(Le Chaudron)"   ┌──────────┐
            │   MODÈLE    │ ─────────────────────────────────────────► │ HARNAIS  │
            │ (décide)    │                                            │ (exécute)│
            └─────────────┘ ◄───────────  {"brut": 979450.95} ──────── └────┬─────┘
                                                                            │
                                                                   ┌────────▼────────┐
                                                                   │ fonction Python │
                                                                   │  (pandas)       │
                                                                   └─────────────────┘
        ```
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        r"""
        ## ② Syntaxe — déclarer un outil

        Deux morceaux : **(a)** la fonction, **(b)** son schéma au format OpenAI.

        ```python
        def masse_salariale(etablissement: str) -> str:
            sub = df[df["Etablissement"].str.lower() == etablissement.lower()]
            if sub.empty:
                return "ERREUR: établissement inconnu"
            return json.dumps({"brut": round(float(sub["Brut"].sum()), 2)})

        SCHEMA = {"type": "function", "function": {
            "name": "masse_salariale",
            "description": "Masse salariale brute d'un établissement.",
            "parameters": {"type": "object",
                "properties": {"etablissement": {"type": "string"}},
                "required": ["etablissement"]}}}
        ```
        """
    )
    return


@app.cell
def _(df):
    # Version de référence, exécutée (pour les démos plus bas)
    import json as _json

    def masse_salariale(etablissement: str) -> str:
        sub = df[df["Etablissement"].str.lower() == etablissement.strip().lower()]
        if sub.empty:
            dispo = ", ".join(sorted(df["Etablissement"].unique()))
            return f"ERREUR: établissement inconnu. Dispo: {dispo}"
        return _json.dumps({
            "etablissement": sub["Etablissement"].iloc[0],
            "nb_bulletins": int(len(sub)),
            "brut": round(float(sub["Brut"].sum()), 2),
        }, ensure_ascii=False)

    masse_salariale("Le Chaudron")
    return (masse_salariale,)


@app.cell
def _(mo):
    mo.callout(
        mo.md(
            r"""
            ## ③ Exercice — écrivez votre premier outil

            Écrivez `compte_effectif(etablissement)` qui renvoie (en JSON) le **nombre de
            bulletins** et la **répartition H/F** (colonne `Sexe`) d'un établissement.
            Gérez le cas d'un établissement inconnu.

            *Testez-le sur « Le Carré Gourmand ».*
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
                def compte_effectif(etablissement: str) -> str:
                    sub = df[df["Etablissement"].str.lower() == etablissement.strip().lower()]
                    if sub.empty:
                        return "ERREUR: établissement inconnu"
                    rep = sub["Sexe"].value_counts().to_dict()
                    return json.dumps({"nb_bulletins": int(len(sub)),
                                       "repartition": rep}, ensure_ascii=False)
                ```

                **Idée clé** : c'est *exactement* la même forme que `masse_salariale` —
                filtrer, agréger, renvoyer du JSON. Un outil = une requête gouvernée.
                """
            )
        }
    )
    return


@app.cell
def _(df):
    # Démonstration exécutée de la solution
    import json as _json2

    def compte_effectif(etablissement: str) -> str:
        sub = df[df["Etablissement"].str.lower() == etablissement.strip().lower()]
        if sub.empty:
            return "ERREUR: établissement inconnu"
        rep = sub["Sexe"].value_counts().to_dict()
        return _json2.dumps({"nb_bulletins": int(len(sub)), "repartition": rep},
                            ensure_ascii=False)

    compte_effectif("Le Carré Gourmand")
    return (compte_effectif,)


@app.cell
def _(mo):
    mo.md(
        r"""
        ## ⑤ Commentaire

        Vous venez de créer deux **outils** sans écrire une seule ligne d'IA. C'est le
        point de la slide S06 : l'outil est du code *ordinaire*. Ce que l'agent ajoute,
        c'est la **décision** d'y recourir — la notion suivante.
        """
    )
    return


@app.cell
def _(mo):
    mo.md(r"""---""")
    return


# ═══════════════════════════════════════════════════════════════════════════
# NOTION 2 — La boucle agentique (function calling)
# ═══════════════════════════════════════════════════════════════════════════
@app.cell
def _(mo):
    mo.md(r"""## ① Notion 2 — La boucle agentique""")
    return


@app.cell
def _(mo):
    mo.mermaid(
        """
        graph TD
            U[Question de l'auditeur] --> M{Modèle décide}
            M -- répond seul --> R[Réponse finale]
            M -- appelle un outil --> H[Harnais exécute l'outil]
            H --> T[Résultat renvoyé au modèle]
            T --> M
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        r"""
        La *boucle* : tant que le modèle **nomme un outil**, le harnais l'exécute et
        renvoie le résultat ; dès qu'il **répond sans outil**, on sort. C'est tout ce
        que fait « un agent » dans Flowise (les *intermediate steps* = un tour de boucle).

        ## ② Syntaxe — le harnais en ~12 lignes

        ```python
        def run_agent(question, tools_spec, registre):
            messages = [{"role": "system", "content": SYSTEM},
                        {"role": "user", "content": question}]
            while True:
                msg = llm.chat(messages, tools=tools_spec)      # le modèle décide
                if not msg.tool_calls:                          # ── SORTIE ──
                    return msg.content
                messages.append(msg)
                for call in msg.tool_calls:                     # le harnais exécute
                    res = registre[call.function.name](**json.loads(call.function.arguments))
                    messages.append({"role": "tool",
                                     "tool_call_id": call.id, "content": res})
        ```

        > La ligne `if not msg.tool_calls: return` **est** toute la logique de décision
        > de la slide S11. Repérez-la.
        """
    )
    return


@app.cell
def _(mo):
    mo.callout(
        mo.md(
            r"""
            ## ③ Exercice — faire tourner la boucle SANS clé LLM

            On n'a pas toujours une clé API en formation. Remplacez le modèle par un
            **modèle simulé** : une fonction qui, au 1ᵉʳ tour, « décide » d'appeler
            `masse_salariale("Le Chaudron")`, puis au 2ᵉ tour renvoie une phrase finale.
            Câblez-la dans une mini-boucle et observez la **trace**.
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
                def modele_simule(messages, tour):
                    # tour 1 : demande l'outil ; tour 2 : conclut
                    if tour == 1:
                        return {"tool": "masse_salariale", "args": {"etablissement": "Le Chaudron"}}
                    return {"reponse": "La masse salariale brute du Chaudron est calculée par l'outil."}

                def run_agent_simule():
                    trace, tour = [], 1
                    while tour <= 3:
                        d = modele_simule(None, tour)
                        if "reponse" in d:
                            return d["reponse"], trace
                        res = masse_salariale(**d["args"])       # le harnais EXÉCUTE
                        trace.append({"tour": tour, "outil": d["tool"], "res": res})
                        tour += 1
                ```

                La boucle est **identique** à la vraie : seule la source de la décision
                change (ici scriptée, en vrai un LLM). C'est pourquoi on peut *tester* un
                agent sans dépendre du modèle.
                """
            )
        }
    )
    return


@app.cell
def _(masse_salariale):
    # Démonstration exécutée : la boucle agentique, modèle simulé, aucun LLM
    def _modele_simule(tour):
        if tour == 1:
            return {"tool": "masse_salariale", "args": {"etablissement": "Le Chaudron"}}
        return {"reponse": "→ La masse salariale brute du Chaudron a été obtenue via l'outil."}

    def run_agent_simule():
        trace, tour = [], 1
        while tour <= 3:
            d = _modele_simule(tour)
            if "reponse" in d:
                return d["reponse"], trace
            res = masse_salariale(**d["args"])
            trace.append({"tour": tour, "outil": d["tool"], "res": res})
            tour += 1
        return "stop", trace

    reponse_demo, trace_demo = run_agent_simule()
    {"reponse": reponse_demo, "trace": trace_demo}
    return reponse_demo, trace_demo


@app.cell
def _(mo, trace_demo):
    mo.md(
        f"""
        ## ⑤ Commentaire

        La **trace** ci-dessous, c'est l'équivalent exact des *intermediate steps* de
        Flowise : on voit *quel outil* a produit *quel chiffre*. En audit, c'est votre
        **piste d'audit**.

        ```json
        {trace_demo}
        ```

        **Pour aller plus loin (avec clé LLM)** : remplacez `modele_simule` par un vrai
        appel `llm.chat(...)` (voir `code/j4_agent.py`). Testez avec / sans prompt
        système et observez si le modèle recourt encore à l'outil (slide S09).
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        r"""
        ---
        ### ✅ Récap J4
        - Un **outil** = fonction + schéma. Le modèle *nomme*, le harnais *exécute*.
        - Un **agent** = une boucle `while` autour d'un appel modèle.
        - La **trace** rend l'agent auditable — gardez-la.
        """
    )
    return


if __name__ == "__main__":
    app.run()
