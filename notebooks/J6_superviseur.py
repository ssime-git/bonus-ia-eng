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


@app.cell
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
        après. **Autoportant** : données incluses, aucune clé d'IA.
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


@app.cell
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


@app.cell
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


@app.cell
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


@app.cell
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
def _(WORKERS):
    # ✏️  À TOI DE JOUER — une version qui marche est fournie ; réécris-la pour t'entraîner.
    def superviseur(etat: dict) -> str:
        if "alerte" not in etat:
            return "DETECTION"
        if "controle" not in etat:
            return "CONTROLE"
        if "rapport" not in etat:
            return "SYNTHESE"
        return "FIN"

    def faire_tourner(max_tours: int = 5):
        etat, journal = {}, []
        for _ in range(max_tours):
            etape = superviseur(etat)
            journal.append({"superviseur_décide": etape})
            if etape == "FIN":
                break
            etat = WORKERS[etape](etat)
            journal.append({"worker_exécuté": etape})
        return etat, journal

    etat_final, journal = faire_tourner()
    {"journal": journal, "rapport": etat_final.get("rapport")}
    return etat_final, faire_tourner, journal, superviseur


@app.cell
def _(mo):
    mo.accordion(
        {
            "🔓 Solution — superviseur + boucle": mo.md(
                r"""
                ```python
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
                ```

                Remarquez que le superviseur **ne calcule rien** : il *lit* l'état et
                *oriente*. Toute l'intelligence de coordination tient dans ces quatre `if`.
                """
            )
        }
    )
    return


@app.cell
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


@app.cell
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


@app.cell
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


if __name__ == "__main__":
    app.run()
