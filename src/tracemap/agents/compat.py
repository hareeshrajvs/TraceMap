"""Optional CrewAI integration — lazy imports for environments without crewai installed."""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])

_crewai_available: bool | None = None


def crewai_available() -> bool:
    global _crewai_available
    if _crewai_available is None:
        try:
            import crewai  # noqa: F401

            _crewai_available = True
        except ImportError:
            _crewai_available = False
    return _crewai_available


def tool(name: str) -> Callable[[F], F]:
    """Use CrewAI @tool when available; otherwise preserve callable for direct use."""
    if crewai_available():
        from crewai.tools import tool as crewai_tool

        return crewai_tool(name)

    def decorator(func: F) -> F:
        func.__tool_name__ = name  # type: ignore[attr-defined]
        return func

    return decorator


def get_llm():
    if not crewai_available():
        raise ImportError(
            "crewai is not installed. Install with Python 3.10+: pip install -e '.[dev]'"
        )
    from crewai import LLM

    from tracemap.config import get_settings

    settings = get_settings()
    return LLM(
        model=f"ollama/{settings.ollama_model}",
        base_url=settings.ollama_base_url,
        temperature=0.2,
    )


def get_agent(**kwargs):
    if not crewai_available():
        raise ImportError("crewai is not installed.")
    from crewai import Agent

    return Agent(**kwargs)


def get_task(**kwargs):
    if not crewai_available():
        raise ImportError("crewai is not installed.")
    from crewai import Task

    return Task(**kwargs)


def get_crew(**kwargs):
    if not crewai_available():
        raise ImportError("crewai is not installed.")
    from crewai import Crew

    return Crew(**kwargs)


def get_process_sequential():
    from crewai import Process

    return Process.sequential
