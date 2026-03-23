@echo off
echo Criando ambiente virtual...
python -m venv .venv

echo Ativando ambiente virtual...
call .venv\Scripts\activate.bat

echo Atualizando pip...
pip install --upgrade pip --quiet

echo Instalando dependencias...
pip install -r requirements.txt --quiet

echo.
echo Ambiente instalado com sucesso!
echo Para ativar: .venv\Scripts\activate.bat
echo Para usar: python main.py --help
