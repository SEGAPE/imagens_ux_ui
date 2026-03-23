#!/usr/bin/env bash
# Remove o ambiente virtual e arquivos gerados

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

deactivate 2>/dev/null || true

if [ -d ".venv" ]; then
    echo "Removendo ambiente virtual..."
    rm -rf .venv
fi

if [ -f "catalogo.json" ]; then
    echo "Removendo catálogo gerado..."
    rm -f catalogo.json
fi

echo "Ambiente removido com sucesso."
