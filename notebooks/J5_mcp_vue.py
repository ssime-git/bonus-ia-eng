# /// script
# requires-python = ">=3.10"
# dependencies = ["marimo", "pandas>=2.0"]
# ///
"""J5 · MCP & vue contrôlée — notebook-cours marimo."""
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
        # J5 · MCP — la *vue contrôlée* sous le capot

        > 5 temps par notion → **① présentation · ② syntaxe · ③ exercice ·
        > ④ solution (repliée) · ⑤ commentaire**.

        **Prolonge** J5 : S04 (document/outil/vue), S15-S18 (50 000 lignes ?),
        S24-S26 (node Custom MCP), S28 (stratégies d'échelle).
        """
    )
    return


@app.cell
def _(mo):
    mo.md(r"""---""")
    return


# ═══════════════════════════════════════════════════════════════════════════
# NOTION 1 — Exposer une VUE, pas le fichier brut
# ═══════════════════════════════════════════════════════════════════════════
@app.cell
def _(mo):
    mo.md(
        r"""
        ## ① Notion 1 — On expose une *vue*, jamais le brut

        Un serveur MCP publie des **outils** qui renvoient des vues *gouvernées*
        (agrégées, filtrées, pseudonymisées) — jamais le fichier de paie entier.

        ```
           FICHIER BRUT (7 200 lignes nominatives)         ✗ ne sort jamais
                 │
                 ▼
           ┌───────────────── Serveur MCP ─────────────────┐
           │  get_audit_scope()   → périmètre (compteurs)  │  ✓ ce qui sort
           │  aggregate_...()     → totaux par établ.      │
           │  dossiers_exception()→ sous-ensemble ciblé    │
           └───────────────────────────────────────────────┘
                 │
                 ▼   AGENT (ne voit que la vue)
        ```
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        r"""
        ## ② Syntaxe — un outil de vue = une agrégation pandas

        ```python
        def aggregate_masse_salariale():
            g = (df.groupby("Etablissement")
                   .agg(nb=("Brut", "size"), masse=("Brut", "sum"))
                   .round(2).reset_index())
            return g.to_json(orient="records", force_ascii=False)
        ```

        Le principe **minimisation** : on renvoie des agrégats, ou au pire un
        **matricule** (pseudonyme), jamais le **nom** (slide S29 / RGPD).
        """
    )
    return


@app.cell
def _(df):
    import json as _json

    def get_audit_scope() -> str:
        return _json.dumps({
            "nb_etablissements": int(df["Etablissement"].nunique()),
            "nb_bulletins": int(len(df)),
            "masse_totale": round(float(df["Brut"].sum()), 2),
        }, ensure_ascii=False)

    get_audit_scope()
    return (get_audit_scope,)


@app.cell
def _(mo):
    mo.callout(
        mo.md(
            r"""
            ## ③ Exercice — un outil de vue avec refus propre

            Écrivez `masse_par_sexe(etablissement)` : la masse brute ventilée H/F pour
            **un** établissement. Contrainte d'audit : si l'établissement n'existe pas,
            l'outil doit **refuser proprement** (message d'erreur), pas planter.
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
                def masse_par_sexe(etablissement: str) -> str:
                    sub = df[df["Etablissement"].str.lower() == etablissement.strip().lower()]
                    if sub.empty:
                        return "ERREUR: établissement inconnu (refus propre)"
                    v = sub.groupby("Sexe")["Brut"].sum().round(2).to_dict()
                    return json.dumps({"etablissement": etablissement,
                                       "masse_par_sexe": v}, ensure_ascii=False)
                ```

                Le **refus** n'est pas un détail : un outil MCP qui plante casse tout le
                flow. « Accepter les demandes gouvernées, refuser le reste » (S29).
                """
            )
        }
    )
    return


@app.cell
def _(df):
    import json as _json2

    def masse_par_sexe(etablissement: str) -> str:
        sub = df[df["Etablissement"].str.lower() == etablissement.strip().lower()]
        if sub.empty:
            return "ERREUR: établissement inconnu (refus propre)"
        v = sub.groupby("Sexe")["Brut"].sum().round(2).to_dict()
        return _json2.dumps({"etablissement": etablissement, "masse_par_sexe": v},
                            ensure_ascii=False)

    {"ok": masse_par_sexe("Le Chaudron"), "refus": masse_par_sexe("Chez Bernard")}
    return (masse_par_sexe,)


@app.cell
def _(mo):
    mo.md(
        r"""
        ## ⑤ Commentaire

        Vos trois fonctions sont déjà « MCP-ready » : un serveur MCP n'est qu'un
        décorateur autour d'elles (`FastMCP(...).tool()(...)`). Le node « Custom MCP »
        de Flowise parle le même protocole. Vous n'avez pas quitté la formation — vous
        en avez ouvert le capot.
        """
    )
    return


@app.cell
def _(mo):
    mo.md(r"""---""")
    return


# ═══════════════════════════════════════════════════════════════════════════
# NOTION 2 — Pourquoi 50 000 lignes échouent (tokens & coût)
# ═══════════════════════════════════════════════════════════════════════════
@app.cell
def _(mo):
    mo.md(
        r"""
        ## ① Notion 2 — « Et si je collais tout le fichier dans le prompt ? »

        Trois échecs *simultanés* (slide S15) : la **fenêtre sature**, chaque **token se
        paie**, et la **qualité chute** (dilution). La bonne réponse n'est pas « un plus
        gros modèle » mais « une **vue** ». On va le *mesurer*.

        ## ② Syntaxe — compter les tokens

        ```python
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        n = len(enc.encode(texte))     # nb de tokens réels
        ```
        """
    )
    return


@app.cell
def _(mo):
    mo.callout(
        mo.md(
            r"""
            ## ③ Exercice — brut vs vue, en tokens

            Comparez le nombre de **tokens** de : (a) tout `df` en CSV, (b) la même chose
            répétée ×7 (≈ un « gros lot » DSN de la slide), (c) la sortie de
            `aggregate_masse_salariale()`. Concluez sur le coût.
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
                def n_tokens(t):
                    try:
                        import tiktoken
                        return len(tiktoken.get_encoding("cl100k_base").encode(t))
                    except Exception:
                        return len(t) // 4          # approximation

                brut = df.to_csv(sep="|", index=False)
                gros = "\\n".join([brut] * 7)
                vue  = aggregate_masse_salariale()
                for nom, c in [("brut", brut), ("gros ×7", gros), ("vue", vue)]:
                    print(nom, n_tokens(c))
                ```
                """
            )
        }
    )
    return


@app.cell
def _(df, get_audit_scope, pd):
    # Démonstration exécutée
    def _n_tokens(t):
        try:
            import tiktoken
            return len(tiktoken.get_encoding("cl100k_base").encode(t))
        except Exception:
            return len(t) // 4

    def _agg():
        g = (df.groupby("Etablissement")
               .agg(nb=("Brut", "size"), masse=("Brut", "sum")).round(2).reset_index())
        return g.to_json(orient="records", force_ascii=False)

    brut = df.to_csv(sep="|", index=False)
    gros = "\n".join([brut] * 7)
    vue = _agg()
    tableau_tokens = pd.DataFrame([
        {"contenu": "brut (~7 200 lignes)", "tokens": _n_tokens(brut)},
        {"contenu": "gros lot ×7 (~50 000)", "tokens": _n_tokens(gros)},
        {"contenu": "vue agrégée (16 lignes)", "tokens": _n_tokens(vue)},
    ])
    tableau_tokens
    return (tableau_tokens,)


@app.cell
def _(mo, tableau_tokens):
    _t = tableau_tokens.set_index("contenu")["tokens"].to_dict()
    mo.md(
        f"""
        ## ⑤ Commentaire

        Le « gros lot » pèse **{_t['gros lot ×7 (~50 000)']:,} tokens** — au-delà de la
        fenêtre de la plupart des modèles : **ça ne rentre même pas**. La vue agrégée
        (**{_t['vue agrégée (16 lignes)']} tokens**) répond à la même question d'audit
        pour une fraction du coût, **sans exposer une seule ligne nominative**.

        C'est la démonstration chiffrée de la slide S28 : *pré-agréger, filtrer côté
        outil*. Le filtre va dans la **requête**, jamais dans le prompt.

        ---
        ### ✅ Récap J5
        - Un outil MCP renvoie une **vue** (agrégée / pseudonymisée), pas le brut.
        - Un outil **refuse proprement** un périmètre invalide.
        - Le volume a un **coût mesurable** : agrégez en amont.
        """
    )
    return


if __name__ == "__main__":
    app.run()
