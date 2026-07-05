# J6 · Bonus rapides — Le superviseur *sous le capot* (routing + HITL)

> **Prolonge** : J6 S06/S10 (le superviseur répartit, il ne fait pas), S13 (« la
> même boucle, l'outil = un agent »), S11-S12 (3 workers spécialisés),
> S14-S16 (node Human Input), S24 (traçabilité notée).
> **Pour qui** : vous avez construit la mini-chaîne détecter → vérifier → restituer.
> **Durée** : 40–50 min. **Fichier** : `code/j6_supervisor.py` (tourne **sans LLM**).

## Pourquoi cette fiche

La slide S13 énonce une idée forte : *le superviseur, c'est la même boucle
agentique que J4 — sauf que ses « outils » sont des agents*. Tant qu'on ne l'écrit
pas, ça reste une formule. Ici, le superviseur devient ce qu'il est vraiment :
une **machine à états** qui, à chaque tour, choisit `DOC / CALC / REPORT / FIN`.
Et vous branchez le **human-in-the-loop** exactement là où la slide le place.

## Objectif

Coder un superviseur qui orchestre 3 workers sur la paie LIORA, produire un
**journal de traçabilité** « qui a fait quoi », et insérer un point de validation
humaine avant la restitution.

---

## Étape 1 — Faire tourner la chaîne (sans LLM)

```bash
python3 code/j6_supervisor.py
```

Lisez le **journal de traçabilité**. Vous voyez le superviseur choisir un état par
tour (`DOC` → `CALC` → `REPORT` → `FIN`) et chaque worker produire sa brique. Sur
les données réelles, la détection sort **Brasserie Dorée** (brut moyen ~7× la
médiane du secteur) — un cas d'audit plausible (primes ? régularisations ? saisie ?).

**Le point à faire passer** : ce journal *est* le livrable d'audit. La slide S24
dit « traçabilité : on sait quel agent a produit quoi » — ici c'est un objet JSON
que vous pouvez archiver, diff, rejouer. Le multi-agent no-code produit la même
chose ; vous en tenez maintenant la structure.

## Étape 2 — Lire le superviseur comme une machine à états

Regardez la fonction `superviseur(etat)`. Elle ne « fait » rien : elle **lit
l'état** et renvoie le prochain nœud. C'est *toute* la logique de la S10 (« il
tranche pour exactement un état suivant »). Notez qu'elle est **déterministe** :
mêmes entrées → même routing. C'est pourquoi on peut la **tester** (étape 4).

**À faire** : ajoutez un état `VERIF_SOURCE` entre `CALC` et `REPORT`, avec un
worker `worker_verif_source(etat)` qui vérifie une condition simple (ex. le
nombre de bulletins de l'alerte est cohérent avec `get_audit_scope`). Mettez à
jour `superviseur()` pour l'insérer dans le flux. Vous venez d'ajouter un agent à
la chaîne **sans toucher aux autres** — c'est le bénéfice de la spécialisation (S25).

## Étape 3 — Le human-in-the-loop, au bon endroit

Relancez en mode interactif :

```python
from code.j6_supervisor import run
etat, journal = run(hitl=True)     # demande la validation dans le terminal
```

`demande_validation_humaine` = l'équivalent code du **node Human Input** (S15).
Observez : la décision humaine (`VALIDÉ` / `REJETÉ`) **entre dans le journal**.
En audit, la validation n'est pas un clic perdu, c'est une trace signée.

**Discussion (S16)** : *quelles* anomalies devraient déclencher le HITL ? Modifiez
le code pour que la validation ne soit demandée **que** si le ratio dépasse un
seuil (ex. 3×) ou si `part_brut_gt_10k` est élevé. Vous encodez ainsi la règle
« validation humaine sur les anomalies à fort enjeu » (S14).

## Étape 4 — Rigueur d'ingénieur : tester le routing sans LLM

Un superviseur LLM est difficile à tester (non déterministe). Un superviseur à
règles se teste en 5 lignes — faites-le :

```python
from code.j6_supervisor import superviseur
assert superviseur({}) == "DOC"
assert superviseur({"alerte": {}, "besoin_calcul": True}) == "CALC"
assert superviseur({"alerte": {}, "besoin_calcul": False}) == "REPORT"
assert superviseur({"alerte": {}, "besoin_calcul": False, "rapport": "x"}) == "FIN"
print("routing OK")
```

**Le message d'ingénierie** (à relier à J7) : plus la décision de routing est
*explicite et testable*, plus le système est auditable. Un superviseur LLM apporte
de la flexibilité mais coûte en contrôle — c'est exactement l'arbitrage
« contrôle vs flexibilité » de la S09.

## Étape 5 (optionnel, avec LLM) — Un vrai superviseur LLM

Remplacez la fonction `superviseur` par un appel `llm.chat(...)` dont le prompt
système est : *« Tu es un superviseur d'audit. Réponds UNIQUEMENT par un mot :
DOC, CALC, REPORT ou FIN, selon l'état fourni. »* Passez l'état en JSON dans le
message utilisateur. Comparez : le LLM route-t-il comme votre machine à états ?
Combien coûte un tour ? Vaut-il le coup ici ? (Souvent non — d'où S26.)

---

## Critères de réussite

- [ ] Je décris le superviseur comme une machine à états (un état/tour).
- [ ] Ma chaîne produit un journal de traçabilité archivable « qui a fait quoi ».
- [ ] Le HITL est placé avant la décision et sa réponse entre dans la trace.
- [ ] J'ai des tests de routing qui passent sans LLM.

## Pièges à signaler au groupe

- Un worker qui « déborde » (fait le calcul *et* la synthèse) casse la traçabilité :
  un agent = un rôle (S25).
- Le HITL n'a de valeur que si l'humain a le contexte pour trancher : le rapport
  doit être lisible et sourcé, sinon la validation est un tampon vide.
