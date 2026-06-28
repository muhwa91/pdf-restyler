# -*- coding: utf-8 -*-
"""H SECURITY 명함 생성기 런처.

실행: python main.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from gui import main  # noqa: E402

if __name__ == "__main__":
    main()
