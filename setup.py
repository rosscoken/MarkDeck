"""
MarkDeck Setup Script

Legacy setup.py for compatibility with older pip versions.
Modern installations should use pyproject.toml.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

# Read requirements
requirements = []
requirements_file = this_directory / "requirements.txt"
if requirements_file.exists():
    with open(requirements_file, "r", encoding="utf-8") as f:
        requirements = [
            line.strip()
            for line in f
            if line.strip() and not line.startswith("#")
        ]

setup(
    name="markdeck",
    version="0.1.0",
    author="Ross",
    author_email="ross@example.com",
    description="A sophisticated command-line tool that converts Markdown files into professional PowerPoint presentations",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/rosscoken/MarkDeck",
    project_urls={
        "Bug Tracker": "https://github.com/rosscoken/MarkDeck/issues",
        "Documentation": "https://markdeck.readthedocs.io",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Documentation",
        "Topic :: Multimedia :: Graphics :: Presentation",
        "Topic :: Office/Business",
        "Topic :: Software Development :: Documentation",
        "Topic :: Text Processing :: Markup",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "mypy>=1.0.0",
            "ruff>=0.1.0",
        ],
        "docs": [
            "sphinx>=7.0.0",
            "sphinx-rtd-theme>=1.3.0",
            "myst-parser>=2.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "markdeck=markdeck.cli.main:main",
        ],
    },
    package_data={
        "markdeck": [
            "themes/defaults/*.json",
            "schemas/*.json",
            "config/defaults.py",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)