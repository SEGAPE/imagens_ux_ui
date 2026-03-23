@echo off

where python >nul 2>nul
if errorlevel 1 (
    echo Erro: python nao encontrado no PATH.
    echo Instale o Python 3.10 ou superior antes de continuar.
    exit /b 1
)

python -c "import sys; assert sys.version_info >= (3, 10), f'Requer Python 3.10+. Encontrado: {sys.version_info.major}.{sys.version_info.minor}'"
if errorlevel 1 (
    echo Erro: versao do Python incompativel. Requer 3.10 ou superior.
    exit /b 1
)

echo Criando ambiente virtual...
python -m venv .venv
if errorlevel 1 (
    echo Erro ao criar ambiente virtual.
    exit /b 1
)

echo Ativando ambiente virtual...
call .venv\Scripts\activate.bat

echo Atualizando pip...
pip install --upgrade pip --quiet

echo Instalando dependencias...
pip install -r requirements.txt --quiet

echo.
echo Ambiente instalado com sucesso!
echo Para ativar: .venv\Scripts\activate.bat
echo Para usar: python main.py
