# J4 · Bonus rapides — La boucle agentique *sous le capot*

> **Prolonge** : J4 S05 (function calling), S06 (la boucle modèle ≠ harnais),
> S08 (anatomie d'un tour), S09/S17 (prompt système), S16 (« votre cas : débug »).
> **Pour qui** : vous avez fini l'atelier « agent simple → agent RAG » et vous codez.
> **Durée** : 30–45 min. **Fichier** : `code/j4_agent.py`.

## Pourquoi cette fiche

En slide, on a dit : *« Flowise est un harnais — comme Claude Code »*, et *« le
modèle nomme, le harnais exécute »*. Ici vous **écrivez ce harnais**. À la fin,
vous saurez que l'« agent » de Flowise n'est pas magique : c'est une boucle
`while` de ~15 lignes autour d'un appel HTTP.

## Objectif

Reproduire en Python la boucle agentique qui, sur les données de paie LIORA,
enchaîne : *le modèle décide → appelle un outil → lit le résultat → répond*.
Puis l'attaquer comme un ingénieur : retirer les garde-fous et observer la casse.

---

## Étape 1 — Les outils d'abord (sans LLM)

Ouvrez `code/j4_agent.py`. Un « outil », côté code, c'est **juste une fonction**
plus un schéma JSON qui la décrit au modèle. Lancez :

```bash
python3 code/j4_agent.py
```

Vous devez voir `calculatrice(...)` et `masse_salariale('Le Chaudron')` répondre
**sans aucun modèle**. C'est le point clé de la slide S06 : l'outil est du code
déterministe ; le modèle ne fait que **choisir** de l'appeler.

**À faire** : ajoutez un troisième outil `compte_effectif(etablissement)` qui
renvoie le nombre de bulletins et la répartition H/F (colonne `Sexe`). Déclarez-le
dans `TOOLS_SPEC` **et** dans le registre `OUTILS`. Testez-le seul.

## Étape 2 — La boucle (avec LLM)

Configurez une clé (voir README), puis décommentez le bloc `run_agent(...)` en bas
du fichier et relancez. Posez :

> « Quelle est la masse salariale brute du Chaudron, et combien font 15,3 % de ce
> montant ? »

Lisez la **trace** imprimée : c'est l'équivalent exact des *intermediate steps*
que vous regardiez dans Flowise (S14). Vous devez voir **deux** appels d'outils
enchaînés : `masse_salariale` puis `calculatrice`, le second réutilisant le
résultat du premier.

**Question de compréhension** : dans `run_agent`, repérez la ligne qui distingue
« le modèle répond » de « le modèle appelle un outil ». C'est le `if not
msg.tool_calls`. C'est *toute* la logique de décision de la S11.

## Étape 3 — Rigueur d'ingénieur : casser pour comprendre

Trois manipulations, à faire et à **noter** (une phrase d'observation chacune) :

1. **Sans prompt système.** Remplacez `SYSTEM` par `""`. Reposez la même question
   plusieurs fois. Le modèle calcule-t-il encore *via l'outil*, ou tente-t-il de
   répondre de tête ? → illustre S09 : le prompt système *fabrique* l'agent.

2. **Garde-fou anti-invention.** Demandez la masse salariale d'un établissement
   **qui n'existe pas** (« Chez Bernard »). Bien conçu, l'outil renvoie une erreur
   listant les établissements ; observez si le modèle **s'arrête et le dit** ou
   s'il invente un chiffre. Renforcez le prompt jusqu'à obtenir le bon réflexe
   (« signale toute donnée manquante plutôt que d'inventer », S18).

3. **Boucle infinie.** Baissez `max_tours` à 1 et posez une question à deux
   étapes. Que se passe-t-il ? → pourquoi un harnais a *toujours* une limite de
   tours (sécurité, coût).

## Étape 4 — Trace exploitable (pont vers l'audit)

La `trace` est une liste de dicts JSON. Sérialisez-la dans un fichier
`trace.json`. En audit, **c'est votre piste d'audit** : qui (quel outil) a produit
quel chiffre, à partir de quels arguments. Reliez-le à J7 (traçabilité notée).

---

## Corrigé

`code/j4_agent.py` contient déjà la boucle complète et deux outils. Le corrigé de
l'outil `compte_effectif` :

```python
def compte_effectif(etablissement: str) -> str:
    sub = DF[DF["Etablissement"].str.lower() == etablissement.strip().lower()]
    if sub.empty:
        return "ERREUR: établissement inconnu"
    rep = sub["Sexe"].value_counts().to_dict()
    return json.dumps({"nb_bulletins": int(len(sub)), "repartition": rep},
                      ensure_ascii=False)
```

## Critères de réussite

- [ ] Je sais montrer, sans LLM, qu'un « outil » est une fonction + un schéma.
- [ ] Ma boucle enchaîne deux outils et je lis la trace comme des *intermediate steps*.
- [ ] J'ai observé l'effet du prompt système (avec / sans) sur le recours à l'outil.
- [ ] J'ai un garde-fou qui empêche l'agent d'inventer un chiffre absent.

## Pour aller encore plus loin (si vraiment très rapide)

- Faites `temperature=0` vs `0.9` : mesurez la stabilité des réponses sur 5 essais.
- Ajoutez un outil `top_bruts(etablissement, n)` **mais agrégé/anonymisé** (pas de
  noms) et discutez le lien avec la slide RGPD/NIR (S29).
