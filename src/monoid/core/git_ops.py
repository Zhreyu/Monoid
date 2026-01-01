"""Git operations for note versioning."""
import subprocess
from pathlib import Path
from typing import Optional


def is_git_repo(path: Path) -> bool:
    """Check if the given path is inside a git repository."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            cwd=path,
            capture_output=True,
            check=False
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def git_commit_note(note_path: str, message: str) -> bool:
    """
    Commit a single note file with the given message.

    Returns True if commit succeeded, False otherwise.
    """
    path = Path(note_path)
    if not path.exists():
        return False

    cwd = path.parent

    # Check if we're in a git repo
    if not is_git_repo(cwd):
        return False

    try:
        # Stage the file
        subprocess.run(
            ["git", "add", path.name],
            cwd=cwd,
            capture_output=True,
            check=True
        )

        # Check if there are changes to commit
        status = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            cwd=cwd,
            capture_output=True,
            check=False
        )

        if status.returncode == 0:
            # No changes staged
            return True  # Nothing to commit, but not an error

        # Commit
        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=cwd,
            capture_output=True,
            check=True
        )
        return True
    except subprocess.CalledProcessError:
        return False


def git_revert_note(note_path: str) -> bool:
    """
    Revert a note to its previous committed state (HEAD~1).

    Returns True if revert succeeded, False otherwise.
    """
    path = Path(note_path)
    cwd = path.parent

    if not is_git_repo(cwd):
        return False

    try:
        # Checkout the file from previous commit
        subprocess.run(
            ["git", "checkout", "HEAD~1", "--", path.name],
            cwd=cwd,
            capture_output=True,
            check=True
        )
        return True
    except subprocess.CalledProcessError:
        return False


def get_note_git_history(note_path: str, limit: int = 5) -> list[dict[str, str]]:
    """
    Get git history for a specific note file.

    Returns list of commits with hash and message.
    """
    path = Path(note_path)
    cwd = path.parent

    if not is_git_repo(cwd):
        return []

    try:
        result = subprocess.run(
            ["git", "log", f"-{limit}", "--pretty=format:%h|%s", "--", path.name],
            cwd=cwd,
            capture_output=True,
            check=True,
            text=True
        )

        history = []
        for line in result.stdout.strip().split("\n"):
            if line and "|" in line:
                hash_val, message = line.split("|", 1)
                history.append({"hash": hash_val, "message": message})
        return history
    except subprocess.CalledProcessError:
        return []
