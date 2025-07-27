from langchain.tools import tool
import subprocess

@tool
def shell_task(command: str) -> str:
    """
    Run a raw Linux shell command. Examples:
    - 'ls -la'
    - 'pwd'
    - 'cat requirements.txt'

    Use this only for basic shell queries that do not require project generation.
    """
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        output = result.stdout.strip()
        error = result.stderr.strip()
        if result.returncode != 0:
            return f"Shell error {result.returncode}: {error or 'No error message'}"
        return output or error or "Command executed successfully with no output."
    except subprocess.TimeoutExpired:
        return "Shell command timed out."
    except Exception as e:
        return f"Shell task failed: {e}"
