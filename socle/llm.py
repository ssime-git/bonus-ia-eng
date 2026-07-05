"""
Socle LLM — un mince client compatible OpenAI, partagé par les fiches J4→J7.

Objectif pédagogique : montrer que « l'IA », côté code, c'est UN appel HTTP à
un endpoint de type OpenAI. Flowise fait exactement ça sous le capot ; ici on
le fait à la main pour voir la mécanique (messages, tools, tool_calls).

Configuration par variables d'environnement :
    LLM_BASE_URL   ex. https://api.openai.com/v1  (ou l'endpoint interne AIChat)
    LLM_API_KEY    votre clé
    LLM_MODEL      ex. gpt-4o-mini  (défaut)

Si le paquet openai n'est pas installé :  pip install openai
Aucune clé ?  Les parties « pur Python » des fiches (données, tokens, routing,
éval) tournent SANS LLM. Seuls les appels chat() en ont besoin.
"""
from __future__ import annotations
import os

_DEFAULTS = {
    "base_url": os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1"),
    "api_key": os.environ.get("LLM_API_KEY", ""),
    "model": os.environ.get("LLM_MODEL", "gpt-4o-mini"),
}


def get_client():
    """Retourne un client OpenAI configuré. Lève une erreur claire si mal réglé."""
    try:
        from openai import OpenAI
    except ImportError as e:
        raise ImportError("Installez le client :  pip install openai") from e
    if not _DEFAULTS["api_key"]:
        raise RuntimeError(
            "Aucune clé LLM. Exportez LLM_API_KEY (et éventuellement LLM_BASE_URL, "
            "LLM_MODEL). Les exercices sans LLM tournent quand même."
        )
    return OpenAI(base_url=_DEFAULTS["base_url"], api_key=_DEFAULTS["api_key"])


def chat(messages, tools=None, temperature=0, model=None):
    """
    Un tour de conversation. Renvoie l'objet message brut de l'API
    (avec .content et éventuellement .tool_calls) — on veut voir la mécanique.
    """
    client = get_client()
    kwargs = dict(model=model or _DEFAULTS["model"], messages=messages,
                  temperature=temperature)
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"
    resp = client.chat.completions.create(**kwargs)
    return resp.choices[0].message


def model_name() -> str:
    return _DEFAULTS["model"]
