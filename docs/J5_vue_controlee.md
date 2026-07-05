# J5 · Bonus rapides — La vue contrôlée *sous le capot* (MCP & coût réel)

> **Prolonge** : J5 S04 (document/outil/vue), S15-S18 (50 000 lignes dans un prompt ?),
> S24-S26 (node Custom MCP, les 5 outils), S28 (stratégies d'échelle).
> **Pour qui** : vous avez branché l'agent au serveur MCP et posé vos questions ciblées.
> **Durée** : 30–45 min. **Fichier** : `code/j5_tools.py` (tourne **sans LLM**, `make j5`).

## Pourquoi cette fiche

La slide dit *« un MCP, c'est une API pour les agents »* et *« on expose une vue,
pas la base entière »*. Deux choses restent abstraites tant qu'on ne code pas :
(1) à quoi ressemble concrètement « un outil » côté serveur, et (2) *pourquoi*
exactement envoyer le fichier brut échoue. Cette fiche rend les deux tangibles —
avec des **tokens et des euros**, pas des mains agitées.

## Objectif

Écrire les outils qu'un serveur MCP publierait sur la paie LIORA (`get_audit_scope`,
`aggregate_masse_salariale`, `dossiers_exception`), puis **mesurer** le coût du brut
vs celui de la vue.

---

## Étape 1 — La démo qui tue le débat (sans LLM)

```bash
make j5
```

Regardez le tableau final :

| Contenu | Lignes | Tokens | Coût/appel |
|---|---:|---:|---:|
| Brut LIORA (~7 200 lignes) | 7 219 | ~660 000 | ~0,10 € |
| Gros lot (~50 000 lignes) | 50 533 | **~4 620 000** | ~0,69 € |
| Vue agrégée (16 lignes) | 1 | **~655** | ~0,0001 € |

(Ordres de grandeur — recalculez avec `make j5`, `_n_tokens` dépend de la
version de `tiktoken` et du contenu exact des CSV.)

**Le point à faire passer** : 4,6 M de tokens, *ça ne rentre dans aucun modèle*
(la fenêtre sature — S15). Ce n'est donc pas « un plus gros modèle » la réponse
(S16), c'est **exposer une vue**. La vue agrégée répond à la même question
d'audit (masse salariale par établissement) pour ~7 000× moins cher, **et** sans
sortir une seule ligne nominative. C'est S28 « pré-agrégation / filtrage côté
outil » démontré, pas affirmé.

## Étape 2 — Lire les outils comme des endpoints MCP

Dans `j5_tools.py`, chaque fonction = **un outil** que le node Custom MCP
appellerait. Notez le principe de **minimisation** (S29/RGPD) :

- `get_audit_scope()` ne renvoie que des compteurs et la liste des établissements.
- `aggregate_masse_salariale()` agrège par établissement — aucun salarié isolé.
- `dossiers_exception()` expose le **matricule** (pseudonyme), *jamais* le nom.

**À faire** : ajoutez un outil `masse_par_sexe(etablissement)` qui renvoie la masse
brute ventilée H/F pour **un** établissement. Contrainte d'audit : refusez (message
d'erreur clair) si l'établissement demandé n'existe pas — un outil MCP doit
**refuser proprement**, pas planter (S29 « ce que l'agent accepte / refuse »).

## Étape 3 — Rigueur d'ingénieur : où placer le filtre ?

La slide S31 dit *« la qualité chute avec le volume »*. Démontrez-le :

1. Écrivez une fonction `vue_brute_tronquee(n)` qui renvoie les `n` premières
   lignes brutes en texte. Faites varier `n` (100, 1 000, 5 000) et **comptez les
   tokens** avec `_n_tokens`. Tracez tokens = f(n) : c'est linéaire, donc le coût
   et le risque de dilution le sont aussi.

2. Formulez la règle d'ingénieur : *le filtrage/agrégation doit se faire **côté
   outil** (dans la requête), jamais dans le prompt* (S28). Un prompt n'est pas un
   moteur de requête.

3. **Optionnel, avec LLM** : posez à un modèle « quelle est la masse salariale du
   Carré Gourmand ? » en lui collant (a) le brut tronqué à 2 000 lignes, puis (b)
   la sortie de `aggregate_masse_salariale()`. Comparez justesse **et** coût.

## Étape 4 — Pont vers un vrai serveur MCP (démonstration)

Vos fonctions sont déjà « MCP-ready ». Pour le montrer, un serveur MCP minimal
n'est qu'un décorateur autour d'elles :

```python
# pip install "mcp[cli]"   —  esquisse, à discuter, pas à déployer en formation
from mcp.server.fastmcp import FastMCP
from code.j5_tools import get_audit_scope, aggregate_masse_salariale

srv = FastMCP("liora-dsn")
srv.tool()(get_audit_scope)
srv.tool()(aggregate_masse_salariale)
# srv.run()  -> stdio, exactement le transport de la slide S13
```

Message clé : **le node « Custom MCP » de Flowise et ce serveur parlent le même
protocole**. Vous n'avez pas quitté le monde de la formation, vous en avez ouvert
le capot (S13 « transport stdio : un sous-process, un tuyau »).

---

## Critères de réussite

- [ ] Je peux chiffrer, en tokens et en €, pourquoi le brut ne passe pas (S15-S18).
- [ ] Mes outils renvoient des **vues** (agrégées / pseudonymisées), jamais le brut.
- [ ] Mon outil **refuse proprement** un périmètre invalide.
- [ ] Je sais dire où placer le filtre (côté outil) et pourquoi (S28/S31).

## Pièges à signaler au groupe

- Compter les tokens « à la louche » (chars/4) suffit pour l'intuition, mais
  `tiktoken` donne le vrai chiffre — la différence n'est pas anecdotique sur du CSV.
- Agréger ne suffit pas à la conformité : vérifiez qu'aucune agrégation ne
  ré-identifie un individu (petit effectif = risque, à relier à J7/RGPD).
