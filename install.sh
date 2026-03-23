#!/usr/bin/env bash
# Instalação do ambiente de desenvolvimento
# Cria venv, instala dependências

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VERSAO_MINIMA="3.10"

# Verificar se Python 3 está disponível
if ! command -v python3 &> /dev/null; then
    echo "Erro: python3 não encontrado no PATH."
    echo "Instale o Python ${VERSAO_MINIMA} ou superior antes de continuar."
    exit 1
fi

# Verificar versão mínima do Python
VERSAO_PYTHON=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
if [ "$(printf '%s\n' "$VERSAO_MINIMA" "$VERSAO_PYTHON" | sort -V | head -1)" != "$VERSAO_MINIMA" ]; then
    echo "Erro: Python ${VERSAO_MINIMA} ou superior é necessário. Versão encontrada: ${VERSAO_PYTHON}"
    exit 1
fi
echo "Python ${VERSAO_PYTHON} encontrado."

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
echo "Para usar: python main.py"
