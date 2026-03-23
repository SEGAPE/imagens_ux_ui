# -*- coding: utf-8 -*-
"""
Gerenciador de assets visuais para painéis do MEC no Looker Studio.

Script CLI principal com subcomandos para organizar, catalogar,
adicionar e publicar imagens do repositório.
"""

import argparse
import json
import logging
import re
import shutil
import subprocess
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger(__name__)

try:
    from unidecode import unidecode
except ImportError:
    print(
        "Dependência 'unidecode' não encontrada. Execute: pip install -r requirements.txt"
    )
    sys.exit(1)


REPOSITORIO = "SEGAPE/imagens_ux_ui"
BRANCH = "main"
URL_RAW_BASE = "https://raw.githubusercontent.com/{repo}/{branch}"
URL_CDN_BASE = "https://cdn.jsdelivr.net/gh/{repo}@{branch}"
DIRETORIO_ASSETS = Path("assets")
ARQUIVO_CATALOGO = Path("catalogo.json")
TIPOS_VALIDOS = ["logo", "icon"]
EXTENSOES_IMAGEM = [".png", ".jpeg", ".jpg", ".svg", ".gif", ".webp"]

MAGIC_BYTES = {
    b"\x89PNG": ".png",
    b"\xff\xd8\xff": ".jpg",
    b"GIF87a": ".gif",
    b"GIF89a": ".gif",
    b"RIFF": ".webp",
}


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


def extrair_metadados_nome(nome_arquivo: str) -> dict | None:
    """Extrai programa, tipo e variante de um nome padronizado."""
    caminho = Path(nome_arquivo)
    nome_sem_ext = caminho.stem

    partes = nome_sem_ext.split("_")
    if len(partes) < 2:
        return None

    for i in range(1, len(partes)):
        tipo_candidato = partes[i]
        if tipo_candidato in TIPOS_VALIDOS:
            programa = "_".join(partes[:i])
            tipo = tipo_candidato
            variante_partes = partes[i + 1 :]
            variante = "_".join(variante_partes) if variante_partes else None
            return {
                "programa": programa,
                "tipo": tipo,
                "variante": variante,
            }

    return None


def gerar_url_raw(caminho_relativo: str) -> str:
    """Retorna URL raw do GitHub para o caminho."""
    base = URL_RAW_BASE.format(repo=REPOSITORIO, branch=BRANCH)
    caminho_limpo = caminho_relativo.replace("\\", "/")
    return f"{base}/{caminho_limpo}"


def gerar_url_cdn(caminho_relativo: str) -> str:
    """Retorna URL jsDelivr CDN para o caminho."""
    base = URL_CDN_BASE.format(repo=REPOSITORIO, branch=BRANCH)
    caminho_limpo = caminho_relativo.replace("\\", "/")
    return f"{base}/{caminho_limpo}"


def perguntar(
    mensagem: str, opcoes: list[str] | None = None, obrigatorio: bool = True
) -> str | None:
    """Input interativo com validação opcional de opções."""
    sufixo = ""
    if opcoes:
        sufixo = f" ({'/'.join(opcoes)})"

    while True:
        resposta = input(f"{mensagem}{sufixo}: ").strip()

        if not resposta:
            if not obrigatorio:
                return None
            print("  Valor obrigatório. Tente novamente.")
            continue

        if opcoes and resposta not in opcoes:
            print(f"  Opção inválida. Escolha entre: {', '.join(opcoes)}")
            continue

        return resposta


def detectar_extensao_magic(caminho: Path) -> str | None:
    """Detecta extensão de imagem pelos primeiros bytes (magic bytes)."""
    try:
        with open(caminho, "rb") as f:
            cabecalho = f.read(12)
    except OSError:
        return None

    for assinatura, extensao in MAGIC_BYTES.items():
        if cabecalho.startswith(assinatura):
            return extensao

    if b"<svg" in cabecalho or cabecalho.strip().startswith(b"<?xml"):
        return ".svg"

    return None


def eh_imagem_valida(caminho: Path) -> tuple[bool, str | None]:
    """Verifica se o arquivo é uma imagem válida. Retorna (valido, extensao)."""
    extensao = caminho.suffix.lower()

    if extensao in EXTENSOES_IMAGEM:
        return True, extensao

    if not extensao:
        extensao_detectada = detectar_extensao_magic(caminho)
        if extensao_detectada:
            return True, extensao_detectada

    return False, None


def cmd_organizar(args: argparse.Namespace) -> None:
    """Organiza arquivos soltos em assets/ conforme a taxonomia."""
    if not DIRETORIO_ASSETS.exists():
        print(f"Diretório '{DIRETORIO_ASSETS}' não encontrado.")
        return

    arquivos_raiz = [
        f for f in DIRETORIO_ASSETS.iterdir()
        if f.is_file()
    ]

    if not arquivos_raiz:
        print("Nenhum arquivo solto encontrado na raiz de assets/.")
        return

    organizados = 0
    ignorados = 0

    for arquivo in sorted(arquivos_raiz):
        valido, extensao = eh_imagem_valida(arquivo)
        if not valido:
            logger.info("Ignorando '%s' (não é imagem válida)", arquivo.name)
            ignorados += 1
            continue

        print(f"\nArquivo: {arquivo.name}")

        programa = perguntar("Programa (ex: cnca, painel_ministro)")
        tipo = perguntar("Tipo", opcoes=TIPOS_VALIDOS)
        variante = perguntar(
            "Variante (opcional, ex: bronze, escuro)", obrigatorio=False
        )

        nome_final = montar_nome_arquivo(programa, tipo, variante, extensao)
        programa_san = sanitizar_nome(programa)
        caminho_destino = DIRETORIO_ASSETS / programa_san / nome_final

        print(f"Nome proposto: {programa_san}/{nome_final}")

        confirmacao = perguntar("Confirmar?", opcoes=["s", "n"])
        if confirmacao != "s":
            ignorados += 1
            continue

        caminho_destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(arquivo), str(caminho_destino))
        print(f"  Movido para: {caminho_destino}")
        organizados += 1

    cmd_catalogo(args)
    print(f"\n{organizados} arquivos organizados, {ignorados} ignorados")


def cmd_catalogo(args: argparse.Namespace) -> None:
    """Gera o catálogo JSON com URLs de todos os assets."""
    if not DIRETORIO_ASSETS.exists():
        print(f"Diretório '{DIRETORIO_ASSETS}' não encontrado.")
        return

    assets = []

    for subpasta in sorted(DIRETORIO_ASSETS.iterdir()):
        if not subpasta.is_dir():
            continue

        for arquivo in sorted(subpasta.rglob("*")):
            if not arquivo.is_file():
                continue

            extensao = arquivo.suffix.lower()
            if extensao not in EXTENSOES_IMAGEM:
                continue

            metadados = extrair_metadados_nome(arquivo.name)
            caminho_relativo = str(arquivo).replace("\\", "/")

            entrada = {
                "programa": metadados["programa"] if metadados else subpasta.name,
                "tipo": metadados["tipo"] if metadados else None,
                "variante": metadados["variante"] if metadados else None,
                "arquivo": arquivo.name,
                "caminho": caminho_relativo,
                "url_raw": gerar_url_raw(caminho_relativo),
                "url_cdn": gerar_url_cdn(caminho_relativo),
            }
            assets.append(entrada)

    with open(ARQUIVO_CATALOGO, "w", encoding="utf-8") as f:
        json.dump(assets, f, indent=2, ensure_ascii=False)

    print(f"Catálogo gerado com {len(assets)} assets em {ARQUIVO_CATALOGO}")


def cmd_adicionar(args: argparse.Namespace) -> None:
    """Adiciona um novo asset ao repositório."""
    arquivo_origem = Path(args.arquivo)

    if not arquivo_origem.exists():
        print(f"Arquivo não encontrado: {arquivo_origem}")
        return

    valido, extensao = eh_imagem_valida(arquivo_origem)
    if not valido:
        print(f"Arquivo '{arquivo_origem.name}' não é uma imagem válida.")
        return

    print(f"\nArquivo: {arquivo_origem.name}")

    programa = perguntar("Programa (ex: cnca, painel_ministro)")
    tipo = perguntar("Tipo", opcoes=TIPOS_VALIDOS)
    variante = perguntar(
        "Variante (opcional, ex: bronze, escuro)", obrigatorio=False
    )

    nome_final = montar_nome_arquivo(programa, tipo, variante, extensao)
    programa_san = sanitizar_nome(programa)
    caminho_destino = DIRETORIO_ASSETS / programa_san / nome_final

    print(f"Nome proposto: {programa_san}/{nome_final}")

    confirmacao = perguntar("Confirmar?", opcoes=["s", "n"])
    if confirmacao != "s":
        print("Operação cancelada.")
        return

    caminho_destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(arquivo_origem), str(caminho_destino))

    cmd_catalogo(args)

    caminho_relativo = str(caminho_destino).replace("\\", "/")
    url_cdn = gerar_url_cdn(caminho_relativo)

    print(f"Asset adicionado: {caminho_destino}")
    print(f"URL CDN: {url_cdn}")


def cmd_publicar(args: argparse.Namespace) -> None:
    """Publica alterações no GitHub (git add, commit, push)."""
    if not shutil.which("git"):
        print("Comando 'git' não encontrado no PATH. Instale o Git primeiro.")
        return

    resultado_status = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True,
    )

    if not resultado_status.stdout.strip():
        print("Nenhuma alteração para publicar.")
        return

    subprocess.run(["git", "add", "."], check=True)

    mensagem = args.mensagem if args.mensagem else "feat: atualiza assets visuais"

    resultado_commit = subprocess.run(
        ["git", "commit", "-m", mensagem],
        capture_output=True,
        text=True,
    )
    if resultado_commit.returncode != 0:
        print(f"Erro no commit: {resultado_commit.stderr}")
        return

    resultado_push = subprocess.run(
        ["git", "push"],
        capture_output=True,
        text=True,
    )
    if resultado_push.returncode != 0:
        print(f"Erro no push: {resultado_push.stderr}")
        return

    cmd_catalogo(args)

    print("Publicado com sucesso!")


def cmd_urls(args: argparse.Namespace) -> None:
    """Lista URLs CDN de todos os assets."""
    if not ARQUIVO_CATALOGO.exists():
        print(
            f"Catálogo não encontrado. Execute primeiro: "
            f"python {Path(__file__).name} catalogo"
        )
        return

    with open(ARQUIVO_CATALOGO, "r", encoding="utf-8") as f:
        assets = json.load(f)

    if args.programa:
        filtro = sanitizar_nome(args.programa)
        assets = [a for a in assets if a.get("programa") == filtro]

    if not assets:
        print("Nenhum asset encontrado.")
        return

    for asset in assets:
        programa = asset.get("programa", "desconhecido")
        tipo = asset.get("tipo", "")
        variante = asset.get("variante")
        url_cdn = asset.get("url_cdn", "")

        identificador = f"{programa}/{tipo}"
        if variante:
            identificador = f"{identificador}/{variante}"

        print(f"{identificador}")
        print(f"  CDN: {url_cdn}")


def main() -> None:
    """Ponto de entrada principal do CLI."""
    parser = argparse.ArgumentParser(
        description="Gerenciador de assets visuais para painéis do MEC no Looker Studio",
    )

    subparsers = parser.add_subparsers(dest="comando")

    sub_organizar = subparsers.add_parser(
        "organizar",
        help="Organiza arquivos soltos em assets/ conforme a taxonomia",
    )
    sub_organizar.set_defaults(func=cmd_organizar)

    sub_catalogo = subparsers.add_parser(
        "catalogo",
        help="Gera o catálogo JSON com URLs de todos os assets",
    )
    sub_catalogo.set_defaults(func=cmd_catalogo)

    sub_adicionar = subparsers.add_parser(
        "adicionar",
        help="Adiciona um novo asset ao repositório",
    )
    sub_adicionar.add_argument(
        "arquivo",
        help="Caminho do arquivo de imagem a adicionar",
    )
    sub_adicionar.set_defaults(func=cmd_adicionar)

    sub_publicar = subparsers.add_parser(
        "publicar",
        help="Publica alterações no GitHub (git add, commit, push)",
    )
    sub_publicar.add_argument(
        "--mensagem", "-m",
        default=None,
        help="Mensagem do commit (padrão: gerada automaticamente)",
    )
    sub_publicar.set_defaults(func=cmd_publicar)

    sub_urls = subparsers.add_parser(
        "urls",
        help="Lista URLs CDN de todos os assets",
    )
    sub_urls.add_argument(
        "--programa", "-p",
        default=None,
        help="Filtra por nome do programa",
    )
    sub_urls.set_defaults(func=cmd_urls)

    args = parser.parse_args()

    if not args.comando:
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperação cancelada pelo usuário.")
        sys.exit(130)


# "A liberdade e o preco da eterna vigilancia." -- Thomas Jefferson
