#!/usr/bin/env python3
"""Setup script for Noah Reading Agent Python backend using uv."""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command: str, cwd: str = None) -> bool:
    """Run a shell command and return success status."""
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
            shell=True
        )
        print(f"✓ {command}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {command}")
        print(f"Error: {e.stderr}")
        return False


def check_uv_installed() -> bool:
    """Check if uv is installed."""
    try:
        subprocess.run(["uv", "--version"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def install_uv():
    """Install uv package manager."""
    print("📦 Installing uv package manager...")

    # Try different installation methods
    install_commands = [
        "curl -LsSf https://astral.sh/uv/install.sh | sh",
        "pip install uv",
        "pipx install uv"
    ]

    for cmd in install_commands:
        print(f"Trying: {cmd}")
        if run_command(cmd):
            return True

    print("❌ Failed to install uv. Please install manually:")
    print("   Visit: https://docs.astral.sh/uv/getting-started/installation/")
    return False


def main():
    """Main setup function."""
    print("🚀 Setting up Noah Reading Agent Python Backend with uv...")

    # Check Python version
    if sys.version_info < (3, 9):
        print("❌ Python 3.9 or higher is required")
        sys.exit(1)

    print(
        f"✓ Python {sys.version_info.major}.{sys.version_info.minor} detected")

    # Check if uv is installed
    if not check_uv_installed():
        print("📦 uv not found, installing...")
        if not install_uv():
            sys.exit(1)
    else:
        print("✓ uv package manager found")

    # Create virtual environment with uv
    print("🔧 Creating virtual environment with uv...")
    if not run_command("uv venv"):
        sys.exit(1)

    # Install dependencies with uv
    print("📚 Installing dependencies with uv...")
    if not run_command("uv pip install -e ."):
        sys.exit(1)

    # Install development dependencies
    print("🔧 Installing development dependencies...")
    if not run_command("uv pip install -e .[dev,test]"):
        sys.exit(1)

    # Create .env file if it doesn't exist
    env_file = Path(".env")
    if not env_file.exists():
        print("⚙️ Creating .env file...")
        if Path(".env.example").exists():
            run_command("cp .env.example .env")
            print("📝 Please update .env file with your configuration")
        else:
            print("⚠️ .env.example not found, please create .env manually")

    print("\n🎉 Setup complete!")
    print("\nNext steps:")
    print("1. Update .env file with your configuration")
    print("2. Set up PostgreSQL database")
    print("3. Activate virtual environment:")
    print("   source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate")
    print("4. Run the server:")
    print("   uv run python -m uvicorn src.main:app --reload")
    print("\nOr use uv directly:")
    print("   uv run src/main.py")


if __name__ == "__main__":
    main()
