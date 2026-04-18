"""追跑f_ruhe_s010_v005_d0403_册复审净助_λFX_βoc_git_commit_seq001_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import subprocess

def git_commit_changes(root: Path, message: str) -> bool:
    """Stage and commit all changes made by the heal pipeline."""
    try:
        # Stage MANIFEST.md files and any renamed .py files
        subprocess.run(['git', 'add', '-A'], cwd=str(root),
                       capture_output=True, timeout=30)

        # Check if there are changes to commit
        result = subprocess.run(
            ['git', 'diff', '--cached', '--quiet'],
            cwd=str(root), capture_output=True, timeout=10,
        )
        if result.returncode == 0:
            print('No changes to commit.')
            return False

        subprocess.run(
            ['git', 'commit', '-m', message],
            cwd=str(root), capture_output=True, timeout=30,
        )
        print(f'Committed: {message}')
        return True
    except Exception as e:
        print(f'Git commit failed: {e}')
        return False
