"""Deploy this app to its Hugging Face Space.

Replaces `fh_hf_deploy`, whose hardcoded ignore_patterns upload the entire
local `.venv/` (90+ MB of wrong-platform binaries) and would also publish
`deploy_hf.sh` — which holds the HF token. `upload_folder` does NOT read
`.gitignore`, so every excluded path must be listed here explicitly.

Run via `deploy_hf.sh`, which sets HF_TOKEN in the environment.
"""

import datetime
import os
import sys

from huggingface_hub import add_space_secret, create_repo, upload_folder, whoami

SPACE_ID = "redevil10/football-manager"

# Mirrors .gitignore (which upload_folder ignores) plus the deploy scripts.
IGNORE_PATTERNS = [
    ".venv/*",
    ".git/*",
    ".github/*",
    ".idea/*",
    ".claude/*",
    ".cursor/*",
    ".pytest_cache/*",
    ".ruff_cache/*",
    "__pycache__/*",
    "*.pyc",
    "*.pyo",
    "*.pyd",
    ".coverage",
    ".sesskey",
    "*.db",
    "*.db-journal",
    "data/*",
    "tests/*",
    "deploy_hf.sh",  # contains the HF token — must never be uploaded
    "deploy_hf.py",
]


def main() -> None:
    token = os.getenv("HF_TOKEN")
    if not token:
        sys.exit("No HF_TOKEN in environment")

    space_id = SPACE_ID if "/" in SPACE_ID else f"{whoami(token)['name']}/{SPACE_ID}"

    url = create_repo(
        space_id, token=token, repo_type="space", space_sdk="docker", exist_ok=True
    )
    upload_folder(
        folder_path=".",
        repo_id=space_id,
        repo_type="space",
        ignore_patterns=IGNORE_PATTERNS,
        commit_message=f"deploy at {datetime.datetime.now():%Y-%m-%d %H:%M:%S}",
        token=token,
    )
    add_space_secret(space_id, token=token, key="HF_TOKEN", value=token)
    print(f"Deployed space at {url}")


if __name__ == "__main__":
    main()
