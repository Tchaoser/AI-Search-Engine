"""Simple test runner script."""
import subprocess
import sys
import os

# Change to the backend directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

result = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
    capture_output=False,
    text=True
)

sys.exit(result.returncode)
