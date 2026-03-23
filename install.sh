#!/usr/bin/env bash
# Instalação do ambiente de desenvolvimento
# Cria venv, instala dependências

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Criando ambiente virtual..."
python3 -m venv .venv

echo "Ativando ambiente virtual..."
source .venv/bin/activate

echo "Atualizando pip..."
pip install --upgrade pip --quiet

echo "Instalando dependências..."
pip install -r requirements.txt --quiet

echo ""
echo "Ambiente instalado com sucesso!"
echo "Para ativar: source .venv/bin/activate"
echo "Para usar: python main.py --help"
