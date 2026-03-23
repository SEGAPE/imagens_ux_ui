# -*- coding: utf-8 -*-
"""Ponto de entrada principal do gerenciador de assets visuais."""

import sys
from pathlib import Path

# Adiciona o diretório raiz ao path para imports funcionarem
sys.path.insert(0, str(Path(__file__).resolve().parent))

from scripts.gerenciador import main

if __name__ == "__main__":
    main()
