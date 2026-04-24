from pathlib import Path
import sys


def test_app_package_importable() -> None:
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    import app  # noqa: F401
