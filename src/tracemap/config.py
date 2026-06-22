"""Application configuration via environment variables and pydantic-settings."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ollama_base_url: str = "http://localhost:11434/v1"
    ollama_model: str = "qwen2.5-coder:14b"

    database_url: str = "sqlite:///data/tracemap.db"
    chroma_path: str = "data/chroma"
    embedding_model: str = "BAAI/bge-large-en-v1.5"

    confluence_url: str = ""
    confluence_user: str = ""
    confluence_api_token: str = ""

    jira_url: str = ""
    jira_user: str = ""
    jira_api_token: str = ""
    jira_project_key: str = "PROJ"

    @property
    def db_path(self) -> Path:
        url = self.database_url
        if url.startswith("sqlite:///"):
            rel = url.replace("sqlite:///", "")
            path = Path(rel)
            if not path.is_absolute():
                path = PROJECT_ROOT / path
            return path
        return PROJECT_ROOT / "data" / "tracemap.db"

    @property
    def chroma_dir(self) -> Path:
        path = Path(self.chroma_path)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        return path

    @property
    def jira_configured(self) -> bool:
        return bool(self.jira_url and self.jira_user and self.jira_api_token)

    @property
    def confluence_configured(self) -> bool:
        return bool(
            self.confluence_url and self.confluence_user and self.confluence_api_token
        )


def get_settings() -> Settings:
    return Settings()


def ensure_data_dirs() -> None:
    settings = get_settings()
    settings.db_path.parent.mkdir(parents=True, exist_ok=True)
    settings.chroma_dir.mkdir(parents=True, exist_ok=True)
