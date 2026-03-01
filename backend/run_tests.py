"""Simple test runner script."""
import subprocess
import sys
import os

# Change to the project root directory (parent of backend/)
# so that 'backend' is importable as a package
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
os.chdir(project_root)

result = subprocess.run(
    [sys.executable, "-m", "pytest", "backend/tests/", "-v", "--tb=short",
     "-c", "backend/pytest.ini"],
    capture_output=False,
    text=True
)

sys.exit(result.returncode)
