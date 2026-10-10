"""FastAPI transport runtime for AI-COMP.

Import this package only when the optional server dependencies are installed.
"""

from ai_comp.api.app import app, create_app

__all__ = ["app", "create_app"]
