# Parcours « Pour les rapides » — J4 → J7

Activités bonus pour les participant·e·s qui **codent déjà** (Python, Qlik) et qui
finissent les labs Flowise en avance.

## L'idée en une phrase

Chaque jour, Flowise vous a fait *manipuler* un objet (agent, MCP, superviseur,
prototype) sans écrire de code. Ces fiches vous font **recoder le même objet à la
main, en Python**, pour voir ce que le node no-code fait *sous le capot* — puis y
ajouter la **rigueur d'ingénieur** que le no-code laisse de côté (évaluation,
garde-fous, traçabilité, coût).

> Ce n'est pas « la vraie version » opposée à « la version jouet ». Flowise *est*
> un harnais qui exécute exactement cette boucle. Le but : que vous fassiez
> confiance à l'outil parce que vous savez ce qu'il y a dedans.

## Correspondance avec les journées

| Jour | Lab no-code (Flowise) | Fiche bonus | Sous le capot | Rigueur d'ingénieur |
|------|----------------------|-------------|---------------|---------------------|
| **J4** | Agent simple + Agent RAG | `J4_boucle_agentique.md` | La boucle agentique & le *function calling* en Python brut | Agent sans prompt système ; garde-fous ; trace JSON des `intermediate steps` |
| **J5** | Node Custom MCP, vue contrôlée DSN | `J5_vue_controlee.md` | Écrire les *outils* (`get_audit_scope`, `aggregate_…`) qu'un serveur MCP exposerait | Mesurer pourquoi 50 000 lignes explosent le contexte (tokens & coût réels) |
| **J6** | Superviseur + workers + Human Input | `J6_superviseur_hitl.md` | La boucle du superviseur comme machine à états (`DOC/CALC/REPORT/FIN`) + HITL | Journal de traçabilité « qui a fait quoi » ; test du routing sans LLM |
| **J7** | Projet Product Build | `J7_eval_fiabilite.md` | Un **harnais d'évaluation** : golden questions, assertions, scorecard | Détection d'hallucination de source ; note de fiabilité reproductible |

## Deux niveaux d'exécution

Les fiches sont conçues pour tourner **même sans clé LLM** :

- **Pur Python** (données, vues, comptage de tokens, logique de routing, harnais
  d'éval) — tourne partout, tout de suite. C'est là qu'est l'essentiel de la
  valeur pédagogique.
- **Avec LLM** (les tours de `chat()` qui font vraiment appeler un modèle) —
  nécessite une clé. Chaque fiche indique clairement quelle partie en a besoin.

## Mise en route (5 min)

```bash
cd bonus_rapides

# Vérifier que les données se chargent (aucun LLM requis) :
uv run socle/liora_data.py
# -> 7217 bulletins · 16 établissements
```

**C'est tout.** Chaque script porte ses dépendances *en tête de fichier* (norme
PEP 723). `uv run` crée un environnement isolé, installe pandas/tiktoken/openai
au premier lancement, les met en cache, puis exécute. Aucun `pip install`, aucun
`venv` à gérer.

```bash
uv run code/j4_agent.py     # J4 · boucle agentique (outils sans LLM)
uv run code/j5_tools.py     # J5 · vue contrôlée + coût tokens
uv run code/j6_supervisor.py# J6 · superviseur + traçabilité
uv run code/j7_eval.py      # J7 · harnais d'évaluation
```

Encore plus court, via **Makefile** :

```bash
make help   # liste les cibles
make j4     # une journée
make all    # les 4 démos non interactives d'affilée
make j6-hitl# J6 avec validation humaine (interactif)
```

Pas encore `uv` ?  `curl -LsSf https://astral.sh/uv/install.sh | sh`
(ou `brew install uv` / `pipx install uv`).

```bash
# (Optionnel) pour les parties LLM — variables d'environnement :
export LLM_BASE_URL="https://api.openai.com/v1"   # ou l'endpoint interne AIChat
export LLM_API_KEY="votre-cle"
export LLM_MODEL="gpt-4o-mini"
```

> **Sans uv ?** Tout marche aussi en classique :
> `pip install -r socle/requirements.txt` puis `python3 code/j4_agent.py`.

Les 16 journaux de paie anonymisés sont déjà dézippés dans `data/`.

## Arborescence

```
bonus_rapides/
├── README.md                  <- ce fichier
├── socle/
│   ├── liora_data.py          <- chargement des 16 CSV (aucun LLM)
│   ├── llm.py                 <- client compatible OpenAI (partagé)
│   └── requirements.txt
├── data/                      <- les 16 journaux de paie (.csv)
├── code/                      <- scripts de départ + corrigés
│   ├── j4_agent.py
│   ├── j5_tools.py
│   ├── j6_supervisor.py
│   └── j7_eval.py
├── notebooks/                 <- cours interactifs marimo (note + code fusionnés)
│   ├── J4_agents.py
│   ├── J5_mcp_vue.py
│   ├── J6_superviseur.py
│   └── J7_evaluation.py
├── public/data/               <- données MINIMISÉES versionnées (sans noms)
│   └── liora_paie.csv
├── docs/                      <- fiches Markdown (version imprimable)
│   ├── J4_boucle_agentique.md
│   ├── J5_vue_controlee.md
│   ├── J6_superviseur_hitl.md
│   └── J7_eval_fiabilite.md
├── .github/                   <- build + workflow GitHub Pages (WASM)
│   ├── scripts/build.py
│   └── workflows/deploy.yml
├── Makefile
└── data/                      <- données NOMINATIVES complètes (git-ignorées)
```

## Publier les notebooks (exécution 100 % navigateur, zéro install)

Les notebooks lisent leurs données via `mo.notebook_location()` : ils tournent
donc **en local** (`data/` ou `public/data/`) **et en WebAssembly** (depuis
`public/data/` servi à côté du notebook). Deux façons de les héberger :

**1. molab — lien instantané, zéro config.** Une fois le repo sur GitHub, remplacez
`github.com` par `molab.marimo.io/github` et ajoutez `/wasm` :

```
https://molab.marimo.io/github/<user>/<repo>/blob/main/notebooks/J4_agents.py/wasm
```

**2. GitHub Pages — site permanent, multi-notebooks.** Le workflow
`.github/workflows/deploy.yml` exporte tous les notebooks en HTML-WASM à chaque
push sur `main` et publie un `index.html`. À activer une fois : **Settings → Pages →
Source : GitHub Actions**. Build local pour tester : `uv run .github/scripts/build.py`.

> ⚠️ **Données publiques.** L'hébergement WASM est **public et sans authentification**.
> Le dépôt ne versionne donc que `public/data/liora_paie.csv`, **minimisé** (colonne
> nominative `Salarie` retirée, matricules pseudonymes conservés). Les données
> nominatives complètes (`data/`) sont **git-ignorées** et ne quittent pas votre poste.
> `tiktoken` (non dispo dans Pyodide) a été retiré des notebooks : J5 estime les tokens
> (~4 caractères/token) en WASM, exactement via `tiktoken` en local si installé.

## Notebooks marimo (recommandé pour l'atelier)

Chaque journée existe aussi en **notebook-cours marimo** qui *fusionne la fiche et
le code* en un seul livrable interactif. Chaque notion suit 5 temps :
**① présentation · ② syntaxe · ③ exercice · ④ solution repliée · ⑤ commentaire**,
avec schémas ASCII / **mermaid** et cellules exécutables (sliders, dropdowns).

```bash
make nb-j4          # éditer le notebook J4 (uvx marimo edit --sandbox)
make nb-run-j4      # le présenter en mode app (lecture seule)
```

`--sandbox` fait installer à marimo les dépendances déclarées *dans le notebook*
(bloc PEP 723 en tête) — rien à installer soi-même. Sans `make` :
`uvx marimo edit --sandbox notebooks/J4_agents.py`.

> Les notebooks tournent **sans clé LLM** : la boucle agentique (J4) et l'agent
> évalué (J7) utilisent un *modèle simulé* pour rester exécutables hors ligne.

## Posture d'animation

- Ces fiches sont **facultatives** et **autoportantes** : un rapide peut s'y mettre
  seul pendant que le reste du groupe finit le lab Flowise.
- Chaque fiche a un **objectif**, des **consignes progressives**, un **corrigé**
  (`code/`), et des **critères de réussite**.
- Le fil rouge « sédentarité cognitive » évoqué par le groupe : ici on ne délègue
  pas, on *ouvre la boîte noire*. C'est l'antidote.
