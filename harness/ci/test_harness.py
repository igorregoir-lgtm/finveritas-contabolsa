# Simple CI harness stub
import subprocess
import sys

def run():
    print("Running FinVeritas CI harness...")
    result = subprocess.run([sys.executable, "-m", "pytest", "tests/", "-q"], capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print("Tests failed")
        sys.exit(1)
    print("✅ All checks passed")
if __name__ == "__main__":
    run()
