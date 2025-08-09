#!/usr/bin/env python3
"""
Setup script for MarkDeck

This script handles installation and setup of MarkDeck dependencies.
"""

import sys
import subprocess
import shutil
import tempfile
from pathlib import Path


def check_python_version():
    """Check if Python version is 3.10+"""
    if sys.version_info < (3, 10):
        print("❌ Error: Python 3.10 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✅ Python {sys.version.split()[0]} detected")
    return True


def check_pandoc():
    """Check if pandoc is installed"""
    if shutil.which("pandoc"):
        try:
            result = subprocess.run(["pandoc", "--version"], capture_output=True, text=True)
            version = result.stdout.split("\n")[0]
            print(f"✅ {version} detected")
            return True
        except Exception:
            pass
    
    print("❌ Pandoc not found")
    print("📥 Please install Pandoc:")
    print("   • Ubuntu/Debian: sudo apt install pandoc")
    print("   • macOS: brew install pandoc")
    print("   • Windows: choco install pandoc")
    print("   • Or download from: https://pandoc.org/installing.html")
    return False


def install_dependencies():
    """Install Python dependencies"""
    dependencies = [
        "python-pptx>=1.0.0",
        "jsonschema>=4.0.0",
        "typer>=0.9.0",
        "rich>=13.0.0",
        "pyyaml>=6.0.0",
        "toml>=0.10.0"
    ]
    
    print("📦 Installing Python dependencies...")
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "--upgrade", "pip"
        ], check=True)
        
        subprocess.run([
            sys.executable, "-m", "pip", "install"
        ] + dependencies, check=True)
        
        print("✅ Python dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False


def test_installation():
    """Test the installation"""
    print("🧪 Testing installation...")
    
    try:
        # Test CLI
        result = subprocess.run([
            sys.executable, "markdeck_cli.py", "--help"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ CLI working correctly")
        else:
            print("❌ CLI test failed")
            return False
        
        # Test init command
        # Create a temporary directory for testing
        test_dir_path = tempfile.mkdtemp(prefix="markdeck_test_")
        subprocess.run([
            sys.executable, "markdeck_cli.py", "init", "--dir", test_dir_path
        ], check=True, capture_output=True)
        
        test_dir = Path(test_dir_path)
        if (test_dir / "examples" / "basic.md").exists():
            print("✅ Init command working")
            # Cleanup
            shutil.rmtree(test_dir, ignore_errors=True)
        else:
            print("❌ Init command failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Installation test failed: {e}")
        return False


def main():
    """Main setup function"""
    print("🚀 MarkDeck Setup")
    print("=" * 50)
    
    # Check requirements
    if not check_python_version():
        sys.exit(1)
    
    if not check_pandoc():
        print("\n⚠️  Pandoc is required but not found.")
        response = input("Continue anyway? (y/N): ").lower().strip()
        if response not in ['y', 'yes']:
            sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Test installation
    if not test_installation():
        print("\n⚠️  Installation test failed, but dependencies are installed.")
        print("   You can try running markdeck_cli.py manually.")
    else:
        print("\n🎉 Setup completed successfully!")
        print("\nQuick start:")
        print("1. python markdeck_cli.py init")
        print("2. python markdeck_cli.py build examples/basic.md --theme examples/theme.json")
        print("\nFor more information, see README.md")


if __name__ == "__main__":
    main()