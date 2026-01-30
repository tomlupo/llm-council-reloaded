"""Full model lists per provider for searchable dropdowns."""

# Provider key -> list of { "id": model_id, "label": display_name }
# Endpoint and api_key_env are defaults for new entries.
PROVIDER_DEFAULTS = {
    "openai": {
        "endpoint": "https://api.openai.com/v1/chat/completions",
        "api_key_env": "OPENAI_API_KEY",
        "models": [
            {"id": "gpt-4o", "label": "GPT-4o"},
            {"id": "gpt-4o-mini", "label": "GPT-4o Mini"},
            {"id": "gpt-4-turbo", "label": "GPT-4 Turbo"},
            {"id": "gpt-4", "label": "GPT-4"},
            {"id": "gpt-3.5-turbo", "label": "GPT-3.5 Turbo"},
            {"id": "o1", "label": "o1"},
            {"id": "o1-mini", "label": "o1 Mini"},
        ],
    },
    "google": {
        "endpoint": "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        "api_key_env": "GOOGLE_API_KEY",
        "models": [
            {"id": "gemini-2.5-flash", "label": "Gemini 2.5 Flash"},
            {"id": "gemini-2.5-pro", "label": "Gemini 2.5 Pro"},
            {"id": "gemini-2.0-flash", "label": "Gemini 2.0 Flash"},
            {"id": "gemini-1.5-pro", "label": "Gemini 1.5 Pro"},
            {"id": "gemini-1.5-flash", "label": "Gemini 1.5 Flash"},
        ],
    },
    "anthropic": {
        "endpoint": "https://api.anthropic.com/v1/messages",
        "api_key_env": "ANTHROPIC_API_KEY",
        "models": [
            {"id": "claude-sonnet-4-20250514", "label": "Claude Sonnet 4"},
            {"id": "claude-opus-4-20250514", "label": "Claude Opus 4"},
            {"id": "claude-3-5-sonnet-20241022", "label": "Claude 3.5 Sonnet"},
            {"id": "claude-3-5-haiku-20241022", "label": "Claude 3.5 Haiku"},
            {"id": "claude-3-opus-20240229", "label": "Claude 3 Opus"},
        ],
    },
    "deepseek": {
        "endpoint": "https://api.deepseek.com/chat/completions",
        "api_key_env": "DEEPSEEK_API_KEY",
        "models": [
            {"id": "deepseek-reasoner", "label": "DeepSeek Reasoner"},
            {"id": "deepseek-chat", "label": "DeepSeek Chat"},
        ],
    },
    "minimax": {
        "endpoint": "https://api.minimax.io/v1/chat/completions",
        "api_key_env": "MINIMAX_API_KEY",
        "models": [
            {"id": "MiniMax-M2.1", "label": "MiniMax M2.1"},
            {"id": "MiniMax-M2.1-lightning", "label": "MiniMax M2.1 Lightning"},
            {"id": "MiniMax-M2", "label": "MiniMax M2"},
            {"id": "M2-her", "label": "M2-her"},
        ],
    },
}


def get_catalog() -> dict:
    """Return full catalog: providers list and per-provider models + defaults.
    Google models include per-model endpoint (URL varies by model id).
    """
    out = {"providers": list(PROVIDER_DEFAULTS.keys()), "provider_defaults": {}}
    google_base = "https://generativelanguage.googleapis.com/v1beta/models"
    for provider, data in PROVIDER_DEFAULTS.items():
        if provider == "google":
            models = [
                {**m, "endpoint": f"{google_base}/{m['id']}:generateContent"}
                for m in data["models"]
            ]
        else:
            models = [dict(m) for m in data["models"]]
        out["provider_defaults"][provider] = {
            "endpoint": data["endpoint"],
            "api_key_env": data["api_key_env"],
            "models": models,
        }
    return out
