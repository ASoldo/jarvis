from langchain.tools import tool
import subprocess

@tool
def codex_cli_task(command: str) -> str:
    """
    Runs the `codex` CLI tool with --full-auto mode and the provided command.

    Example commands:
    - 'use linux commands to use filesystem'
    - 'generate a new React app'
    - 'create a FastAPI endpoint for user login'
    - 'initialize a Rust CLI project with clap'

    Input should be a plain English description of what codex should do.
    """
    try:
        full_cmd = f"codex --full-auto \"{command}\""
        result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, timeout=120)
        output = result.stdout.strip()
        error = result.stderr.strip()
        if result.returncode != 0:
            return f"Codex error {result.returncode}: {error or 'No error message'}"
        return output or error or "Codex ran successfully with no output."
    except subprocess.TimeoutExpired:
        return "Codex timed out. Try a simpler or shorter instruction."
    except Exception as e:
        return f"Codex failed: {e}"
