# Guia de contribuição

Bem-vindo ao repositório de assets visuais do MEC! Este guia explica como contribuir com o projeto.

## Pré-requisitos

- Python 3.10 ou superior
- Git configurado com identidade MEC (`[REDACTED] / [REDACTED]`)
- Acesso ao repositório SEGAPE no GitHub

## Configuração inicial

1. Clone o repositório:
```bash
git clone git@github.com:SEGAPE/imagens_ux_ui.git
cd imagens_ux_ui
```

2. Instale o ambiente:
```bash
# Linux / macOS
bash install.sh
source .venv/bin/activate

# Windows
install.bat
.venv\Scripts\activate.bat
```

3. Verifique que está funcionando:
```bash
python main.py --help
```

## Como adicionar um novo asset

### Opção 1 — Via script interativo (recomendado)

```bash
python main.py adicionar /caminho/para/imagem.png
```

O script vai perguntar:
- **Programa**: nome do programa (ex: `cnca`, `painel_ministro`)
- **Tipo**: `logo` ou `icon`
- **Variante**: diferenciador opcional (ex: `bronze`, `escuro`)

Depois, publique:
```bash
python main.py publicar -m "feat: adiciona logo do novo programa"
```

### Opção 2 — Via BigQuery Notebook

Se você está trabalhando num notebook Python do BigQuery, pode fazer upload direto:

```python
from scripts.gerenciador_bigquery import upload_asset

url = upload_asset("/tmp/imagem.png", "programa", "logo", "variante")
```

#### Configuração da autenticação (BigQuery)

O script suporta dois métodos:

**Método 1 — OAuth Device Flow (interativo)**
1. Registre um OAuth App na organização SEGAPE (ou peça ao administrador)
2. Preencha o `OAUTH_CLIENT_ID` no script `gerenciador_bigquery.py`
3. Na primeira execução, o script abrirá o navegador para autorização

**Método 2 — GitHub App (automação)**
1. Crie um GitHub App na organização SEGAPE
2. Configure as variáveis de ambiente:
   - `GITHUB_APP_ID`
   - `GITHUB_APP_PRIVATE_KEY`
   - `GITHUB_APP_INSTALLATION_ID`

## Taxonomia de nomes

Todos os arquivos devem seguir o padrão:

```
{programa}_{tipo}[_{variante}].{extensão}
```

### Regras
- Tudo em minúsculas, sem acentos, sem espaços
- Palavras separadas por `_` (snake_case)
- Extensão mantida original (`.png`, `.jpeg`, `.svg`)
- Tipo deve ser `logo` ou `icon`
- Variante é opcional — use quando há mais de um asset do mesmo programa e tipo

### Exemplos
| Arquivo original | Nome padronizado |
|---|---|
| `Selo CNCA Bronze.png` | `cnca_logo_bronze.png` |
| `ícone-aluno.jpeg` | `painel_ministro_icon_aluno.jpeg` |
| `Logo Mais Professores.svg` | `mais_professores_logo.svg` |

## Como usar as URLs no Looker Studio

### Passo 1 — Criar campo calculado
Na fonte de dados, crie um campo com a fórmula que retorna a URL CDN baseada num valor do registro.

### Passo 2 — Configurar tipo do campo
Altere o tipo do campo para **Imagem** na edição da fonte de dados.

### Passo 3 — Usar componente Tabela
Adicione um componente **Tabela** e coloque o campo de imagem como coluna.

> **Dica:** O Looker Studio renderiza imagens automaticamente em colunas do tipo Imagem dentro de Tabelas.

## Convenções do projeto

- **Commits** em PT-BR, sem emojis, formato: `tipo: descrição imperativa`
  - Exemplos: `feat: adiciona logo do programa X`, `fix: corrige nome do ícone Y`
- **Encoding**: UTF-8 em todos os arquivos de texto
- **Caminhos**: usar `pathlib.Path` no código Python (compatibilidade multiplataforma)
- **Validação**: sempre use `python main.py organizar` ou `adicionar` para novos assets — nunca copie manualmente para as pastas

## Estrutura do repositório

```
imagens_ux_ui/
├── README.md                    # Documentação principal
├── CONTRIBUTING.md              # Este guia
├── .gitignore
├── .gitattributes
├── requirements.txt
├── install.sh / install.bat     # Instalação
├── uninstall.sh / uninstall.bat # Desinstalação
├── main.py                      # Ponto de entrada CLI
├── scripts/
│   ├── gerenciador.py           # CLI principal
│   └── gerenciador_bigquery.py  # Upload via BigQuery
├── assets/                      # Imagens organizadas por programa
│   ├── cnca/
│   ├── painel_ministro/
│   └── ...
└── catalogo.json                # Catálogo gerado automaticamente
```

---

*"Código que não pode ser entendido não pode ser mantido."*
