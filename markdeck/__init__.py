"""
MarkDeck - Markdown to PowerPoint Converter

A sophisticated command-line tool that converts Markdown files into professional
PowerPoint presentations with optional PDF export.
"""

__version__ = "0.1.0"
__author__ = "Ross"
__license__ = "MIT"

from markdeck.core.engine import MarkDeckEngine
from markdeck.core.exceptions import MarkDeckError

__all__ = ["MarkDeckEngine", "MarkDeckError"]