# /// script
# requires-python = ">=3.10"
# dependencies = ["pandas>=2.0", "openai>=1.30"]
# ///
"""
J4 — La boucle agentique SOUS LE CAPOT.

Ce que Flowise appelle « un agent » = un modèle + un harnais qui exécute une
boucle : le modèle NOMME un outil (function calling), le harnais l'EXÉCUTE, on
renvoie le résultat, on recommence — jusqu'à ce que le modèle réponde sans outil.

Ici, ~60 lignes suffisent à reproduire ça. Les OUTILS (bas du fichier) sont du
pur Python testable sans LLM. La BOUCLE (run_agent) a besoin d'une clé LLM.

Slides de référence : J4 S05 (function calling), S06 (boucle modèle≠harnais),
S08 (anatomie d'un tour), S09/S17 (prompt système).
"""
from __future__ import annotations
import json
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "socle"))
import liora_data  # noqa: E402

DF = liora_data.load_all()

# ─────────────────────────────────────────────────────────────────────────────
# 1) LES OUTILS  (pur Python — testables sans LLM)
# ─────────────────────────────────────────────────────────────────────────────

def calculatrice(expression: str) -> str:
    """Évalue une expression arithmétique simple. Exact, contrairement au modèle."""
    autorises = set("0123456789.+-*/() ")
    if not set(expression) <= autorises:
        return "ERREUR: caractères non autorisés"
    try:
        return str(round(eval(expression, {"__builtins__": {}}, {}), 2))
    except Exception as e:
        return f"ERREUR: {e}"


def masse_salariale(etablissement: str) -> str:
    """Somme du Brut pour un établissement (vue agrégée, pas de ligne nominative)."""
    sub = DF[DF["Etablissement"].str.lower() == etablissement.strip().lower()]
    if sub.empty:
        dispo = ", ".join(sorted(DF["Etablissement"].unique()))
        return f"ERREUR: établissement inconnu. Disponibles: {dispo}"
    return json.dumps({
        "etablissement": sub["Etablissement"].iloc[0],
        "nb_bulletins": int(len(sub)),
        "masse_salariale_brute": round(float(sub["Brut"].sum()), 2),
        "brut_moyen": round(float(sub["Brut"].mean()), 2),
    }, ensure_ascii=False)


# Registre : nom -> fonction. Le harnais s'en sert pour exécuter.
OUTILS = {"calculatrice": calculatrice, "masse_salariale": masse_salariale}

# Schéma JSON des outils, tel qu'on le déclare au modèle (format OpenAI).
TOOLS_SPEC = [
    {"type": "function", "function": {
        "name": "calculatrice",
        "description": "Évalue une expression arithmétique exacte (ex. '1234.5*0.153').",
        "parameters": {"type": "object", "properties": {
            "expression": {"type": "string"}}, "required": ["expression"]}}},
    {"type": "function", "function": {
        "name": "masse_salariale",
        "description": "Vue agrégée de la masse salariale brute d'un établissement.",
        "parameters": {"type": "object", "properties": {
            "etablissement": {"type": "string"}}, "required": ["etablissement"]}}},
]

SYSTEM = (
    "Tu es un assistant d'audit paie/DSN. Tu ne DEVINES jamais un chiffre : "
    "tu utilises l'outil masse_salariale pour les données, et calculatrice pour "
    "tout calcul exact. Si une donnée manque, dis-le plutôt que d'inventer. "
    "Pas de conseil juridique."
)

# ─────────────────────────────────────────────────────────────────────────────
# 2) LA BOUCLE AGENTIQUE  (le harnais — nécessite un LLM)
# ─────────────────────────────────────────────────────────────────────────────

def run_agent(question: str, max_tours: int = 5, verbose: bool = True):
    """Reproduit la boucle qu'exécute Flowise. Retourne (reponse, trace)."""
    import llm  # importé ici pour que le fichier se charge sans clé
    messages = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": question}]
    trace = []  # les « intermediate steps » que Flowise affiche
    for tour in range(1, max_tours + 1):
        msg = llm.chat(messages, tools=TOOLS_SPEC)
        # Cas 1 : le modèle répond directement -> fin de boucle
        if not msg.tool_calls:
            if verbose:
                print(f"[tour {tour}] réponse directe")
            return msg.content, trace
        # Cas 2 : le modèle NOMME un/des outils -> le harnais EXÉCUTE
        messages.append(msg.model_dump(exclude_none=True))
        for call in msg.tool_calls:
            nom = call.function.name
            args = json.loads(call.function.arguments or "{}")
            resultat = OUTILS[nom](**args)          # <- exécution côté harnais
            trace.append({"tour": tour, "outil": nom, "args": args,
                          "resultat": resultat})
            if verbose:
                print(f"[tour {tour}] outil={nom} args={args} -> {resultat}")
            messages.append({"role": "tool", "tool_call_id": call.id,
                             "content": resultat})
    return "Abandon: trop de tours.", trace


if __name__ == "__main__":
    # Partie SANS LLM : on prouve que les outils marchent seuls.
    print("== Outils (sans LLM) ==")
    print("calculatrice('35640*0.153') =", calculatrice("35640*0.153"))
    print("masse_salariale('Le Chaudron') =", masse_salariale("Le Chaudron"))

    # Partie AVEC LLM (décommenter si clé configurée) :
    # q = "Quelle est la masse salariale brute du Chaudron, et combien font 15,3% de ce montant ?"
    # rep, trace = run_agent(q)
    # print("\nRÉPONSE:", rep)
    # print("TRACE:", json.dumps(trace, ensure_ascii=False, indent=2))
