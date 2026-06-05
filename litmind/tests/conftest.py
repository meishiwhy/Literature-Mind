"""conftest: 自动添加 src 到 sys.path"""
import sys
import os
from pathlib import Path

# 获取项目根目录 (litmind/)
project_root = Path(__file__).resolve().parent.parent
src_path = project_root / "src"
if src_path.exists() and str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))
