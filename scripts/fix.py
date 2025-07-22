# scripts/fix.py
import subprocess
import sys

def run_command(cmd):
    """Run a command and print output."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"Warning: {cmd} failed with code {result.returncode}")
    return result.returncode

def main():
    """Run all formatting and linting fixes."""
    commands = [
        "ruff check --fix src",
        "black src",
        "isort src",
    ]
    
    for cmd in commands:
        run_command(cmd)
    
    # Show remaining issues
    print("\nChecking for remaining issues...")
    run_command("ruff check src")

if __name__ == "__main__":
    main()