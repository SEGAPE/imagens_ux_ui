@echo off
call .venv\Scripts\deactivate.bat 2>nul

if exist .venv (
    echo Removendo ambiente virtual...
    rmdir /s /q .venv
)

if exist catalogo.json (
    echo Removendo catalogo gerado...
    del /f catalogo.json
)

echo Ambiente removido com sucesso.
