import sys
from pathlib import Path

# Ensure both backend directory and project root directory are in sys.path
_current_file = Path(__file__).resolve()
_backend_dir = _current_file.parent.parent
_root_dir = _backend_dir.parent

if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))
if str(_root_dir) not in sys.path:
    sys.path.insert(0, str(_root_dir))
