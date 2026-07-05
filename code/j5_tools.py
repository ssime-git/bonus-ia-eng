# /// script
# requires-python = ">=3.10"
# dependencies = ["pandas>=2.0", "tiktoken>=0.5"]
# ///
"""
J5 — La VUE CONTRÔLÉE sous le capot : ce qu'un serveur MCP exposerait.

En J5 (S24-S26) le node « Custom MCP » branche l'agent à des outils qui ne
renvoient JAMAIS le fichier brut, seulement des vues gouvernées :
get_audit_scope, aggregate_..._dsn_like, etc.

Ici on écrit ces outils en Python (c'est exactement la « fonction » derrière un
outil MCP), et surtout on MESURE pourquoi coller 50 000 lignes dans le prompt
échoue (S15-S18) : tokens, coût, dilution.

Tout ce fichier tourne SANS LLM (le comptage de tokens utilise tiktoken).
"""
from __future__ import annotations
import json
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "socle"))
import liora_data  # noqa: E402

DF = liora_data.load_all()

# ─────────────────────────────────────────────────────────────────────────────
# LES OUTILS D'UNE « VUE CONTRÔLÉE » (ce que le serveur MCP publie)
# ─────────────────────────────────────────────────────────────────────────────

def get_audit_scope() -> str:
    """Le périmètre : nb d'établissements, de bulletins, plages. Aucune ligne nominative."""
    return json.dumps({
        "nb_etablissements": int(DF["Etablissement"].nunique()),
        "nb_bulletins": int(len(DF)),
        "masse_salariale_totale": round(float(DF["Brut"].sum()), 2),
        "etablissements": sorted(DF["Etablissement"].unique().tolist()),
    }, ensure_ascii=False)


def aggregate_masse_salariale() -> str:
    """Vue agrégée par établissement — pas de salarié individuel exposé."""
    g = (DF.groupby("Etablissement")
           .agg(nb_bulletins=("Brut", "size"),
                masse_brute=("Brut", "sum"),
                brut_moyen=("Brut", "mean"))
           .round(2).reset_index())
    return g.to_json(orient="records", force_ascii=False)


def dossiers_exception(seuil_brut: float = 10000.0) -> str:
    """Sous-ensemble ciblé : bulletins au brut anormalement élevé (à vérifier)."""
    sub = DF[DF["Brut"] > seuil_brut][["Etablissement", "Matricule", "Brut"]]
    return json.dumps({
        "seuil": seuil_brut,
        "nb_exceptions": int(len(sub)),
        # on expose le matricule (pseudonyme), pas le nom -> minimisation
        "apercu": sub.head(10).to_dict(orient="records"),
    }, ensure_ascii=False, default=float)


# ─────────────────────────────────────────────────────────────────────────────
# LA DÉMONSTRATION DU COÛT : brut vs vue
# ─────────────────────────────────────────────────────────────────────────────

def _n_tokens(texte: str) -> int:
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(texte))
    except Exception:
        # approximation si tiktoken indisponible : ~4 chars / token
        return len(texte) // 4


def compare_brut_vs_vue(prix_par_million_tokens: float = 0.15):
    """Combien coûte-t-il d'envoyer le brut vs une vue agrégée ? (S15-S18)"""
    # 1) tout le fichier brut collé dans le prompt
    brut = DF.to_csv(sep="|", index=False)
    # 2) simulation d'un vrai lot DSN (x7 pour approcher les ~50 000 lignes de la slide)
    gros = "\n".join([brut] * 7)
    # 3) la vue agrégée qu'un outil MCP renverrait à la place
    vue = aggregate_masse_salariale()

    lignes = [
        ("Brut LIORA (~7 200 lignes)", brut),
        ("Gros lot (~50 000 lignes)", gros),
        ("Vue agrégée (16 lignes)", vue),
    ]
    print(f"{'Contenu':<32}{'Lignes':>10}{'Tokens':>12}{'Coût/appel':>14}")
    print("-" * 68)
    for nom, contenu in lignes:
        nl = contenu.count("\n") + 1
        tok = _n_tokens(contenu)
        cout = tok / 1_000_000 * prix_par_million_tokens
        print(f"{nom:<32}{nl:>10,}{tok:>12,}{cout:>13.4f}€")
    print("\nLecture : la vue agrégée répond à la même question d'audit pour une")
    print("fraction du coût — et sans jamais exposer une ligne nominative.")


if __name__ == "__main__":
    print("== get_audit_scope ==");        print(get_audit_scope()[:300], "...\n")
    print("== aggregate_masse_salariale =="); print(aggregate_masse_salariale()[:300], "...\n")
    print("== dossiers_exception (>10000€) =="); print(dossiers_exception()[:300], "...\n")
    print("== Coût : brut vs vue ==")
    compare_brut_vs_vue()
