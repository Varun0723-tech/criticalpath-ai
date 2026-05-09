from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parent
    frontend_dir = root / "frontend"
    dist_dir = frontend_dir / "dist"
    public_dir = root / "public"

    subprocess.run(["npm", "ci"], cwd=frontend_dir, check=True)
    subprocess.run(["npm", "run", "build"], cwd=frontend_dir, check=True)

    if public_dir.exists():
        shutil.rmtree(public_dir)

    shutil.copytree(dist_dir, public_dir)
    print(f"Prepared Vercel public assets in {public_dir}")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        print(f"Build failed while running: {exc.cmd}", file=sys.stderr)
        raise

