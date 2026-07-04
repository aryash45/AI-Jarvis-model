"""
jarvis_core/ollama_manager.py — backward-compatibility shim
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
OllamaManager has been renamed to RouterLLM in router_llm.py.
This shim re-exports the new class under the old name so that any
external callers (third-party integrations, old scripts) continue
to work without modification.
"""
from jarvis_core.router_llm import RouterLLM as OllamaManager  # noqa: F401

__all__ = ["OllamaManager"]
