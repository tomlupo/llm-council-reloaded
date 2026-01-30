"""Settings model for LLM Council Plus."""

import json
import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field

# If set, load/save settings from this path (e.g. in .env: COUNCIL_SETTINGS_PATH=config/settings.json).
SETTINGS_PATH_ENV = "COUNCIL_SETTINGS_PATH"


class ModelConfig(BaseModel):
    name: str
    provider: str  # "openai", "google", "anthropic", "deepseek", "minimax"
    model: str
    endpoint: str
    api_key_env: str
    enabled: bool = True


class ModelSettings(BaseModel):
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout_seconds: int = 180


class PeerReviewScoring(BaseModel):
    criteria: list[str] = Field(default_factory=lambda: ["accuracy", "completeness", "clarity", "insight"])
    scale: int = 10


class PeerReviewConfig(BaseModel):
    enabled: bool = True
    anonymize: bool = True
    scoring: PeerReviewScoring = Field(default_factory=PeerReviewScoring)


class SynthesisConfig(BaseModel):
    highlight_consensus: bool = True
    explain_disagreements: bool = True
    include_unique_insights: bool = True


class CouncilConfig(BaseModel):
    chairman_strategy: str = "rotating"  # "rotating" or "fixed"
    chairman_fixed_model: Optional[str] = None
    peer_review: PeerReviewConfig = Field(default_factory=PeerReviewConfig)
    synthesis: SynthesisConfig = Field(default_factory=SynthesisConfig)


class DebateDefaults(BaseModel):
    rounds: int = 2
    positions: Optional[list[str]] = None


class DecideDefaults(BaseModel):
    criteria: list[str] = Field(default_factory=lambda: ["feasibility", "cost", "complexity", "maintainability"])


class BrainstormDefaults(BaseModel):
    style: str = "balanced"  # "wild", "practical", "balanced"
    rounds: int = 2


class Settings(BaseModel):
    models: list[ModelConfig] = Field(default_factory=list)
    model_settings: ModelSettings = Field(default_factory=ModelSettings)
    council: CouncilConfig = Field(default_factory=CouncilConfig)
    default_deliberation_mode: str = "ask"
    debate_defaults: DebateDefaults = Field(default_factory=DebateDefaults)
    decide_defaults: DecideDefaults = Field(default_factory=DecideDefaults)
    brainstorm_defaults: BrainstormDefaults = Field(default_factory=BrainstormDefaults)


_settings: Optional[Settings] = None
_settings_path: Optional[Path] = None


def _default_settings_path() -> Path:
    env_path = os.environ.get(SETTINGS_PATH_ENV)
    if env_path:
        p = Path(env_path)
        return p.resolve() if not p.is_absolute() else p
    return Path(__file__).parent / "data" / "settings.json"


def load_settings(path: Optional[Path] = None) -> Settings:
    global _settings, _settings_path
    _settings_path = path or _default_settings_path()
    if _settings_path.exists():
        data = json.loads(_settings_path.read_text())
        _settings = Settings(**data)
    else:
        _settings = Settings(
            models=[
                ModelConfig(
                    name="gpt",
                    provider="openai",
                    model="gpt-4o",
                    endpoint="https://api.openai.com/v1/chat/completions",
                    api_key_env="OPENAI_API_KEY",
                ),
                ModelConfig(
                    name="gemini",
                    provider="google",
                    model="gemini-2.5-flash",
                    endpoint="https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
                    api_key_env="GOOGLE_API_KEY",
                ),
                ModelConfig(
                    name="claude",
                    provider="anthropic",
                    model="claude-sonnet-4-20250514",
                    endpoint="https://api.anthropic.com/v1/messages",
                    api_key_env="ANTHROPIC_API_KEY",
                ),
                ModelConfig(
                    name="deepseek",
                    provider="deepseek",
                    model="deepseek-reasoner",
                    endpoint="https://api.deepseek.com/chat/completions",
                    api_key_env="DEEPSEEK_API_KEY",
                ),
                ModelConfig(
                    name="minimax",
                    provider="minimax",
                    model="MiniMax-M2.1",
                    endpoint="https://api.minimax.io/v1/chat/completions",
                    api_key_env="MINIMAX_API_KEY",
                ),
            ]
        )
    return _settings


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        return load_settings()
    return _settings


def save_settings(settings: Settings, path: Optional[Path] = None) -> None:
    global _settings, _settings_path
    _settings = settings
    p = path or _settings_path or _default_settings_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(settings.model_dump_json(indent=2))
