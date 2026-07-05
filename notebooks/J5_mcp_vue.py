# /// script
# requires-python = ">=3.10"
# dependencies = ["marimo", "pandas>=2.0"]
# ///
"""J5 · Donner des données à un agent, sans tout lui donner — notebook autoportant."""
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
        # J5 · Donner des données à un agent — sans tout lui donner

        ### Ce que vous saurez faire à la fin
        - Expliquer **pourquoi** on ne colle pas un gros fichier dans un prompt.
        - Écrire des **vues** : des fonctions qui renvoient des données *agrégées*,
          jamais le fichier brut ni un nom de salarié.
        - **Mesurer** le coût (en « tokens ») du brut face à une vue — et voir l'écart.
        - Faire le lien avec le **MCP** : un standard pour brancher un agent à ces vues.

        ### Mode d'emploi
        Cours à lire de haut en bas. **🎯 Exercice** = à vous de jouer ; **🔓 Solution** =
        à déplier après avoir cherché. **Autoportant** : données incluses, aucune clé d'IA.
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
    return df, pd


@app.cell
def _(mo):
    mo.md(
        r"""
        ---
        # 1. Le problème : le prompt n'est pas une base de données

        Un réflexe naturel : « pour que l'IA réponde sur mes données de paie, je vais lui
        **coller tout le fichier** dans la question ». Sur un vrai fichier (dizaines de
        milliers de lignes), cette idée échoue de **trois façons à la fois** :

        1. **La fenêtre sature.** Un modèle a une taille maximale d'entrée. Un gros fichier
           n'y tient tout simplement pas.
        2. **Chaque mot se paie.** On facture au *token* (≈ un morceau de mot). Envoyer tout
           le fichier à *chaque* question coûte cher, très vite.
        3. **La qualité chute.** Noyé sous les lignes, le modèle confond, « moyenne », et se
           met à inventer.

        La bonne réponse n'est **pas** « un plus gros modèle ». C'est : **n'envoyer que ce
        qu'il faut** — une *vue* de la donnée, pas la donnée entière.

        ```
          MAUVAIS                                 BON
          ┌──────────────┐                        ┌──────────────┐
          │ tout le      │  ──► modèle (sature)   │ une VUE      │ ──► modèle (léger)
          │ fichier brut │                        │ agrégée      │
          └──────────────┘                        └──────────────┘
        ```
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        r"""
        ---
        # 2. La solution : exposer des *vues*, pas le brut

        Une « vue » est une fonction qui renvoie un **résumé gouverné** de la donnée :
        un total, une moyenne, un décompte — jamais la liste nominative. C'est exactement
        ce qu'un serveur **MCP** publierait comme « outils » à destination d'un agent.

        Deux principes d'auditeur :

        - **Agréger** : on renvoie « la masse salariale par établissement », pas les
          bulletins un par un.
        - **Minimiser** : au pire on expose un `Matricule` (pseudonyme), **jamais** un nom.

        ## La syntaxe, expliquée

        `groupby` regroupe les lignes ; `.agg(...)` calcule un résumé par groupe :

        ```python
        def vue_par_etablissement() -> str:
            resume = (df.groupby("Etablissement")["Brut"]
                        .agg(nb="size", masse="sum")   # nb de bulletins + total
                        .reset_index())
            return resume.to_string(index=False)       # un petit tableau lisible
        ```
        """
    )
    return


@app.cell
def _(mo):
    mo.callout(
        mo.md(
            r"""
            ## 🎯 Exercice 1 — une vue *par sexe*, avec refus propre

            **Ce qu'on cherche à faire :** écrire `masse_par_sexe(etablissement)` qui renvoie
            la masse salariale ventilée **H / F** pour **un** établissement — et qui **refuse
            proprement** si l'établissement n'existe pas (un outil qui plante casse l'agent).

            ```
            entrée : "Le Chaudron"
                       │
                       ▼
              établissement connu ?
                ├─ non ─► "établissement inconnu"        (refus propre)
                └─ oui ─► groupby(Sexe).Brut.sum()
                          └─► {"M": 8430, "F": 6350}
            ```

            Complétez la cellule ci-dessous. Testez avec `"Le Chaudron"` puis `"Chez Paul"`.
            """
        ),
        kind="info",
    )
    return


@app.cell
def _(df):
    # ✏️  À TOI DE JOUER — une version qui marche est fournie ; réécris-la pour t'entraîner.
    def masse_par_sexe(etablissement: str):
        sous_ensemble = df[df["Etablissement"] == etablissement]
        if len(sous_ensemble) == 0:
            return "Établissement inconnu (refus propre) — vérifiez le nom."
        ventilation = sous_ensemble.groupby("Sexe")["Brut"].sum().to_dict()
        return {"etablissement": etablissement, "masse_par_sexe": ventilation}

    masse_par_sexe("Le Chaudron")
    return (masse_par_sexe,)


@app.cell
def _(mo):
    mo.accordion(
        {
            "🔓 Solution — Exercice 1": mo.md(
                r"""
                ```python
                def masse_par_sexe(etablissement: str):
                    sous_ensemble = df[df["Etablissement"] == etablissement]
                    if len(sous_ensemble) == 0:                       # refus D'ABORD
                        return "Établissement inconnu (refus propre)."
                    ventilation = sous_ensemble.groupby("Sexe")["Brut"].sum().to_dict()
                    return {"etablissement": etablissement, "masse_par_sexe": ventilation}
                ```

                **Pourquoi le refus est essentiel :** un serveur MCP « accepte les demandes
                gouvernées et refuse le reste ». Une vue qui répond `None` ou qui plante sur
                un mauvais paramètre casse tout le flow de l'agent. Refuser *proprement*, avec
                un message clair, fait partie du contrat de l'outil.
                """
            )
        }
    )
    return


@app.cell
def _(masse_par_sexe, mo):
    mo.md(
        f"""
        **Vérifions les deux cas :**

        - connu → `{masse_par_sexe("Le Chaudron")}`
        - inconnu → *{masse_par_sexe("Chez Paul")}*

        Aucune ligne nominative ne sort : juste deux totaux. C'est une **vue**.
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        r"""
        ---
        # 3. Mesurer le coût : brut contre vue

        Parlons **tokens**. Un token ≈ un petit morceau de mot ; un modèle « lit » et
        « facture » en tokens. Règle de poche : **~4 caractères = 1 token**. (Les vrais
        outils comme `tiktoken` comptent exactement, mais l'approximation suffit pour saisir
        l'ordre de grandeur — et elle marche partout, y compris dans le navigateur.)

        Comparons le coût d'envoyer **tout le fichier** contre celui d'envoyer **une vue**.
        Comme notre extrait est petit, on le **répète** pour simuler un vrai fichier
        volumineux — l'écart de proportion, lui, est bien réel.

        ```python
        def compter_tokens(texte: str) -> int:
            return len(texte) // 4        # approximation ~4 caractères / token
        ```
        """
    )
    return


@app.cell
def _(mo):
    mo.callout(
        mo.md(
            r"""
            ## 🎯 Exercice 2 — chiffrer l'écart

            **Ce qu'on cherche à faire :** comparer le nombre de tokens de
            **(a)** tout le brut, **(b)** le brut répété ×200 (≈ un gros fichier),
            **(c)** la vue agrégée par établissement. Puis conclure sur le coût.

            La cellule ci-dessous le fait déjà — lisez-la, exécutez-la, et regardez le
            rapport entre (b) et (c).
            """
        ),
        kind="info",
    )
    return


@app.cell
def _(df, pd):
    # ✏️  Zone d'expérimentation : change le facteur de répétition et observe.
    def compter_tokens(texte: str) -> int:
        return len(texte) // 4  # ~4 caractères / token

    brut = df.to_csv(index=False)
    gros_fichier = brut * 200  # on simule un fichier volumineux
    vue = (df.groupby("Etablissement")["Brut"]
             .agg(nb="size", masse="sum").reset_index().to_csv(index=False))

    comparaison = pd.DataFrame([
        {"contenu": "brut (notre extrait)", "caractères": len(brut), "tokens≈": compter_tokens(brut)},
        {"contenu": "gros fichier (×200)", "caractères": len(gros_fichier), "tokens≈": compter_tokens(gros_fichier)},
        {"contenu": "vue agrégée", "caractères": len(vue), "tokens≈": compter_tokens(vue)},
    ])
    comparaison
    return comparaison, compter_tokens


@app.cell
def _(comparaison, mo):
    _gros = int(comparaison.loc[comparaison["contenu"] == "gros fichier (×200)", "tokens≈"].iloc[0])
    _vue = int(comparaison.loc[comparaison["contenu"] == "vue agrégée", "tokens≈"].iloc[0])
    mo.md(
        f"""
        ## Ce que révèlent les chiffres

        Le « gros fichier » pèse ≈ **{_gros:,} tokens** — au-delà de ce que beaucoup de
        modèles acceptent en entrée : **il ne rentre même pas**. La vue agrégée, elle, tient
        en ≈ **{_vue} tokens**, soit **~{_gros // max(_vue,1):,}× moins**, tout en répondant à
        la même question d'audit (« quelle masse par établissement ? »).

        > La leçon d'ingénierie : **le filtrage et l'agrégation se font côté *outil* (dans la
        > requête), jamais dans le prompt.** Un prompt n'est pas un moteur de requête.
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        r"""
        ---
        # 4. Le lien avec le MCP (et Flowise)

        Ce que vous venez d'écrire — des fonctions qui renvoient des **vues** — c'est
        *exactement* ce qu'un **serveur MCP** expose à un agent. Le MCP (Model Context
        Protocol) est simplement un **standard** : « voici mes outils, voici comment les
        appeler ». Un serveur minimal, c'est un décorateur autour de vos fonctions :

        ```python
        from mcp.server.fastmcp import FastMCP
        serveur = FastMCP("liora-paie")
        serveur.tool()(masse_par_sexe)     # votre vue devient un outil MCP
        # serveur.run()                    # ...que Flowise (node « Custom MCP ») consomme
        ```

        Le node « Custom MCP » de Flowise et ce serveur parlent le **même** protocole.
        Vous n'avez pas quitté la formation — vous en avez ouvert le capot.

        ---
        ## ✅ À emporter
        - On **n'envoie jamais** un gros fichier au modèle : on expose une **vue** agrégée.
        - Une bonne vue **minimise** (pas de noms) et **refuse proprement** l'invalide.
        - Le volume a un **coût mesurable** en tokens : agrégez **en amont**.
        - Le MCP standardise le branchement de ces vues à un agent.
        """
    )
    return


if __name__ == "__main__":
    app.run()
