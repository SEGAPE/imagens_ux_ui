# -*- coding: utf-8 -*-
"""
Gerenciador de upload de imagens ao GitHub a partir de notebooks Python do BigQuery.

Permite enviar assets visuais diretamente para o repositório SEGAPE/imagens_ux_ui
sem depender de clone local, usando a API de conteúdo do GitHub.
"""

import base64
import json
import logging
import os
import sys
import time
import webbrowser
from pathlib import Path

try:
    import requests
except ImportError:
    raise ImportError(
        "Dependência 'requests' não encontrada. "
        "Execute: pip install requests"
    )

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger(__name__)

try:
    from scripts.gerenciador import sanitizar_nome, montar_nome_arquivo
except ImportError:
    logger.info(
        "Módulo scripts.gerenciador não disponível — "
        "usando implementação local das funções de sanitização"
    )

    import re

    try:
        from unidecode import unidecode
    except ImportError:
        def unidecode(texto: str) -> str:
            """Fallback básico para ambientes sem unidecode."""
            mapa = {
                "á": "a", "à": "a", "â": "a", "ã": "a",
                "é": "e", "ê": "e",
                "í": "i",
                "ó": "o", "ô": "o", "õ": "o",
                "ú": "u",
                "ç": "c",
                "Á": "A", "À": "A", "Â": "A", "Ã": "A",
                "É": "E", "Ê": "E",
                "Í": "I",
                "Ó": "O", "Ô": "O", "Õ": "O",
                "Ú": "U",
                "Ç": "C",
            }
            return "".join(mapa.get(c, c) for c in texto)

    def sanitizar_nome(texto: str) -> str:
        """Remove acentos, converte para snake_case limpo."""
        resultado = unidecode(texto)
        resultado = resultado.lower()
        resultado = re.sub(r"[\s\-\.]+", "_", resultado)
        resultado = re.sub(r"[^a-z0-9_]", "_", resultado)
        resultado = re.sub(r"_+", "_", resultado)
        resultado = resultado.strip("_")
        return resultado

    def montar_nome_arquivo(
        programa: str, tipo: str, variante: str | None, extensao: str
    ) -> str:
        """Monta nome padronizado: {programa}_{tipo}[_{variante}].{extensao}"""
        programa_san = sanitizar_nome(programa)
        tipo_san = sanitizar_nome(tipo)
        extensao = extensao.lstrip(".")

        if variante:
            variante_san = sanitizar_nome(variante)
            return f"{programa_san}_{tipo_san}_{variante_san}.{extensao}"

        return f"{programa_san}_{tipo_san}.{extensao}"


REPOSITORIO = "SEGAPE/imagens_ux_ui"
BRANCH = "main"
URL_CDN_BASE = "https://cdn.jsdelivr.net/gh/{repo}@{branch}"
GITHUB_API_BASE = "https://api.github.com"
OAUTH_CLIENT_ID = ""
ARQUIVO_TOKEN = Path.home() / ".imagens_ux_ui_token"


def obter_token_device_flow(client_id: str) -> str:
    """Autentica via GitHub OAuth Device Flow (interativo).

    Solicita que o usuário acesse uma URL e insira um código de verificação.
    Após autorização, salva o token em disco para reutilização.
    """
    if not client_id:
        raise ValueError(
            "OAUTH_CLIENT_ID não configurado. "
            "Preencha a constante no script ou registre um OAuth App na organização SEGAPE."
        )

    resposta_codigo = requests.post(
        "https://github.com/login/device/code",
        data={"client_id": client_id, "scope": "repo"},
        headers={"Accept": "application/json"},
        timeout=30,
    )
    resposta_codigo.raise_for_status()
    dados_codigo = resposta_codigo.json()

    device_code = dados_codigo["device_code"]
    user_code = dados_codigo["user_code"]
    verification_uri = dados_codigo["verification_uri"]
    interval = dados_codigo.get("interval", 5)

    logger.info(
        "Acesse %s e insira o código: %s",
        verification_uri,
        user_code,
    )

    try:
        webbrowser.open(verification_uri)
    except Exception:
        logger.info("Não foi possível abrir o navegador automaticamente")

    while True:
        time.sleep(interval)

        resposta_token = requests.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": client_id,
                "device_code": device_code,
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            },
            headers={"Accept": "application/json"},
            timeout=30,
        )
        resposta_token.raise_for_status()
        dados_token = resposta_token.json()

        if "access_token" in dados_token:
            token = dados_token["access_token"]
            ARQUIVO_TOKEN.write_text(token, encoding="utf-8")
            ARQUIVO_TOKEN.chmod(0o600)
            logger.info("Token salvo em %s", ARQUIVO_TOKEN)
            return token

        erro = dados_token.get("error", "")
        if erro == "authorization_pending":
            continue
        if erro == "slow_down":
            interval += 5
            continue
        if erro == "expired_token":
            raise TimeoutError("Código de verificação expirou. Tente novamente.")
        if erro == "access_denied":
            raise PermissionError("Autorização negada pelo usuário.")

        raise RuntimeError(f"Erro inesperado no Device Flow: {dados_token}")


def obter_token_github_app() -> str:
    """Gera token via GitHub App (automação sem interação).

    Requer variáveis de ambiente:
    - GITHUB_APP_ID
    - GITHUB_APP_PRIVATE_KEY
    - GITHUB_APP_INSTALLATION_ID

    Depende de PyJWT e cryptography.
    """
    try:
        import jwt
    except ImportError:
        raise ImportError(
            "Dependências 'PyJWT' e 'cryptography' necessárias para autenticação via GitHub App. "
            "Execute: pip install PyJWT cryptography"
        )

    app_id = os.environ["GITHUB_APP_ID"]
    chave_privada = os.environ["GITHUB_APP_PRIVATE_KEY"]
    installation_id = os.environ["GITHUB_APP_INSTALLATION_ID"]

    agora = int(time.time())
    payload = {
        "iat": agora - 60,
        "exp": agora + (10 * 60),
        "iss": app_id,
    }

    token_jwt = jwt.encode(payload, chave_privada, algorithm="RS256")

    resposta = requests.post(
        f"{GITHUB_API_BASE}/app/installations/{installation_id}/access_tokens",
        headers={
            "Authorization": f"Bearer {token_jwt}",
            "Accept": "application/vnd.github+json",
        },
        timeout=30,
    )
    resposta.raise_for_status()

    return resposta.json()["token"]


def obter_token() -> str:
    """Obtém token de autenticação GitHub usando o método disponível.

    Ordem de prioridade:
    1. Token salvo em disco (se existir e não estiver vazio)
    2. GitHub App (se variáveis de ambiente configuradas)
    3. OAuth Device Flow (interativo)
    """
    if ARQUIVO_TOKEN.exists():
        token_salvo = ARQUIVO_TOKEN.read_text(encoding="utf-8").strip()
        if token_salvo:
            logger.info("Reutilizando token salvo em %s", ARQUIVO_TOKEN)
            return token_salvo

    variaveis_app = {"GITHUB_APP_ID", "GITHUB_APP_PRIVATE_KEY", "GITHUB_APP_INSTALLATION_ID"}
    if variaveis_app.issubset(os.environ.keys()):
        logger.info("Autenticando via GitHub App")
        return obter_token_github_app()

    logger.info("Iniciando autenticação via OAuth Device Flow")
    return obter_token_device_flow(OAUTH_CLIENT_ID)


def upload_asset(
    caminho_arquivo: str,
    programa: str,
    tipo: str,
    variante: str | None = None,
) -> str:
    """Faz upload de um asset para o repositório via API do GitHub.

    Args:
        caminho_arquivo: Caminho local do arquivo de imagem.
        programa: Nome do programa (ex: cnca, painel_ministro).
        tipo: Tipo do asset (ex: logo, icon).
        variante: Diferenciador opcional (ex: bronze, escuro).

    Returns:
        URL jsDelivr CDN do asset publicado.
    """
    arquivo = Path(caminho_arquivo)
    if not arquivo.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {arquivo}")

    extensao = arquivo.suffix
    if not extensao:
        raise ValueError(f"Arquivo sem extensão: {arquivo}")

    nome_padronizado = montar_nome_arquivo(programa, tipo, variante, extensao)
    programa_san = sanitizar_nome(programa)
    caminho_remoto = f"assets/{programa_san}/{nome_padronizado}"

    token = obter_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }

    url_api = f"{GITHUB_API_BASE}/repos/{REPOSITORIO}/contents/{caminho_remoto}"

    sha_existente = None
    resposta_get = requests.get(
        url_api,
        headers=headers,
        params={"ref": BRANCH},
        timeout=30,
    )
    if resposta_get.status_code == 200:
        sha_existente = resposta_get.json().get("sha")
        logger.info("Arquivo já existe no repositório — será atualizado (sha: %s)", sha_existente)

    conteudo_base64 = base64.b64encode(arquivo.read_bytes()).decode("ascii")

    corpo = {
        "message": f"feat: adiciona {nome_padronizado}",
        "content": conteudo_base64,
        "branch": BRANCH,
    }
    if sha_existente:
        corpo["sha"] = sha_existente

    resposta_put = requests.put(
        url_api,
        headers=headers,
        json=corpo,
        timeout=60,
    )
    resposta_put.raise_for_status()

    url_cdn = URL_CDN_BASE.format(repo=REPOSITORIO, branch=BRANCH)
    url_final = f"{url_cdn}/{caminho_remoto}"

    logger.info("Upload concluído: %s", url_final)
    return url_final


# Exemplo de uso em notebook BigQuery:
# url = upload_asset("/tmp/novo_selo.png", "cnca", "logo", "diamante")
# print(f"URL para Looker Studio: {url}")


# "Aquele que tem um porquê para viver pode suportar quase qualquer como." -- Friedrich Nietzsche
