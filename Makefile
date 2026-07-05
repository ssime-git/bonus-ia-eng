# Makefile — Parcours « Pour les rapides » (J4 → J7)
# Lance les scripts via `uv run` (dépendances déclarées en tête de chaque fichier).
# Usage :  make help  |  make j4  |  make all  |  make check

RUN := uv run
CODE := code
NB := notebooks
# marimo lancé via uvx (aucune install préalable) ; --sandbox = deps isolées du notebook
MARIMO := uvx marimo

.DEFAULT_GOAL := help
.PHONY: help all check data j4 j5 j6 j7 j6-hitl clean \
        nb nb-j4 nb-j5 nb-j6 nb-j7 nb-run-j4 nb-run-j5 nb-run-j6 nb-run-j7

help:  ## Affiche cette aide
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	  | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

data:  ## Vérifie le chargement des données (aucun LLM)
	$(RUN) socle/liora_data.py

j4:  ## J4 · Boucle agentique sous le capot
	$(RUN) $(CODE)/j4_agent.py

j5:  ## J5 · Vue contrôlée (MCP) + coût tokens
	$(RUN) $(CODE)/j5_tools.py

j6:  ## J6 · Superviseur + traçabilité (non interactif)
	$(RUN) $(CODE)/j6_supervisor.py

j6-hitl:  ## J6 · Superviseur AVEC validation humaine (interactif)
	$(RUN) python -c "import sys; sys.path.insert(0,'$(CODE)'); import j6_supervisor as j; j.run(hitl=True)"

j7:  ## J7 · Harnais d'évaluation & scorecard
	$(RUN) $(CODE)/j7_eval.py

all: data j4 j5 j6 j7  ## Lance toutes les démos non interactives

check: all  ## Alias de `all` : sanity-check de bout en bout

## ─── Notebooks marimo (cours interactif) ───────────────────────────────────
nb:  ## Rappel des cibles notebook
	@echo "Éditer :  make nb-j4 | nb-j5 | nb-j6 | nb-j7"
	@echo "Présenter (lecture seule, mode app) :  make nb-run-j4 …"

nb-j4:  ## Éditer le notebook J4 (agents)
	$(MARIMO) edit --sandbox $(NB)/J4_agents.py
nb-j5:  ## Éditer le notebook J5 (MCP / vue)
	$(MARIMO) edit --sandbox $(NB)/J5_mcp_vue.py
nb-j6:  ## Éditer le notebook J6 (superviseur / HITL)
	$(MARIMO) edit --sandbox $(NB)/J6_superviseur.py
nb-j7:  ## Éditer le notebook J7 (évaluation)
	$(MARIMO) edit --sandbox $(NB)/J7_evaluation.py

nb-run-j4:  ## Présenter J4 en mode app (lecture seule)
	$(MARIMO) run --sandbox $(NB)/J4_agents.py
nb-run-j5:  ## Présenter J5 en mode app
	$(MARIMO) run --sandbox $(NB)/J5_mcp_vue.py
nb-run-j6:  ## Présenter J6 en mode app
	$(MARIMO) run --sandbox $(NB)/J6_superviseur.py
nb-run-j7:  ## Présenter J7 en mode app
	$(MARIMO) run --sandbox $(NB)/J7_evaluation.py

clean:  ## Supprime les caches Python
	find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
