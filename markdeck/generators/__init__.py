"""
MarkDeck Slide Generators

PowerPoint slide generation using python-pptx integration.
"""

from markdeck.generators.pptx_generator import PPTXGenerator
from markdeck.generators.layout_manager import LayoutManager

__all__ = [
    "PPTXGenerator",
    "LayoutManager",
]