# Imagens UX/UI — SEGAPE/MEC

Repositório de assets visuais (logos, ícones, selos) para painéis do MEC no Looker Studio.

As imagens são servidas via [jsDelivr CDN](https://www.jsdelivr.com/) para uso direto em campos do tipo Imagem no Looker Studio.

## Instalação

### Linux / macOS
```bash
git clone git@github.com:SEGAPE/imagens_ux_ui.git
cd imagens_ux_ui
bash install.sh
```

### Windows
```cmd
git clone git@github.com:SEGAPE/imagens_ux_ui.git
cd imagens_ux_ui
install.bat
```

## Uso rápido

### Organizar arquivos soltos
```bash
python main.py organizar
```
O script pergunta interativamente o programa, tipo e variante de cada arquivo.

### Adicionar um novo asset
```bash
python main.py adicionar /caminho/para/imagem.png
```

### Gerar catálogo de URLs
```bash
python main.py catalogo
```

### Listar URLs prontas para o Looker Studio
```bash
python main.py urls
python main.py urls --programa cnca
```

### Publicar alterações no GitHub
```bash
python main.py publicar
python main.py publicar -m "feat: adiciona novos ícones do painel ministro"
```

## Taxonomia de nomes

Padrão: `{programa}_{tipo}[_{variante}].{extensão}`

| Campo | Descrição | Exemplos |
|-------|-----------|----------|
| `programa` | Nome do programa em snake_case sem acentos | `cnca`, `painel_ministro`, `rede_federal` |
| `tipo` | Categoria do asset | `logo`, `icon` |
| `variante` | Diferenciador (opcional) | `bronze`, `prata`, `ouro`, `escuro` |
| `extensão` | Formato original mantido | `.png`, `.jpeg`, `.svg` |

Exemplos:
- `cnca_logo_bronze.png`
- `painel_ministro_icon_aluno.jpeg`
- `carteira_nacional_logo_escuro.jpeg`

## Como usar no Looker Studio

1. Na fonte de dados, crie um campo calculado do tipo **Texto** (não Imagem) que retorne a URL CDN:

```sql
CASE
  WHEN selo = "Bronze" THEN "https://cdn.jsdelivr.net/gh/SEGAPE/imagens_ux_ui@main/assets/cnca/cnca_logo_bronze.png"
  WHEN selo = "Prata" THEN "https://cdn.jsdelivr.net/gh/SEGAPE/imagens_ux_ui@main/assets/cnca/cnca_logo_prata.png"
  WHEN selo = "Ouro" THEN "https://cdn.jsdelivr.net/gh/SEGAPE/imagens_ux_ui@main/assets/cnca/cnca_logo_ouro.png"
  ELSE NULL
END
```

2. Altere o tipo do campo para **Imagem**

3. Use um componente **Tabela** com esse campo como coluna — as imagens serão renderizadas automaticamente

> **Dica:** Para esconder o cabeçalho da coluna, coloque um espaço em branco no nome. Para esconder a contagem de linhas, coloque um retângulo branco sobre ela.

## Como usar no BigQuery Notebook

Veja `scripts/gerenciador_bigquery.py` para upload direto de arquivos via API do GitHub.

```python
from scripts.gerenciador_bigquery import upload_asset

url = upload_asset("/tmp/nova_imagem.png", "cnca", "logo", "diamante")
print(f"URL para Looker Studio: {url}")
```

Configuração de autenticação descrita no [CONTRIBUTING.md](CONTRIBUTING.md).

## Catálogo de assets

O arquivo `catalogo.json` é gerado automaticamente pelo comando `catalogo` e contém URLs de todos os assets.

Para consultar rapidamente:
```bash
python main.py urls
```

## Desinstalação

### Linux / macOS
```bash
bash uninstall.sh
```

### Windows
```cmd
uninstall.bat
```

## Links úteis

- [jsDelivr CDN](https://www.jsdelivr.com/) — CDN usada para servir as imagens
- [GitHub Contents API](https://docs.github.com/en/rest/repos/contents) — API para upload de arquivos
- [Looker Studio — Tipos de campo](https://support.google.com/looker-studio/answer/6374482) — Documentação sobre tipos de campo
- [GitHub OAuth Device Flow](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps#device-flow) — Autenticação via Device Flow

---

*"A simplicidade é a sofisticação suprema." — Leonardo da Vinci*
