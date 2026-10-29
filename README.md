# Controle de Gastos Pessoais

API REST com mini-dashboard para registrar e consultar gastos e receitas pessoais: lançamentos
categorizados, saldo, resumo mensal por categoria, filtros e exportação do extrato em CSV.

O projeto foi construído aula a aula com **Spec-Driven Development (SDD)**: cada funcionalidade tem uma
spec em [`specs/`](specs/) implementada uma por vez, e as decisões de projeto ficam registradas no
[`CLAUDE.md`](CLAUDE.md).

## Funcionalidades
- **Transações** (entradas e saídas): criar, listar, buscar, editar e excluir, com validação e mensagens de
  erro em português.
- **Categorias**: criar e listar; cada transação pode ter uma categoria (opcional).
- **Filtros** combináveis na listagem: categoria, período e faixa de valor.
- **Saldo total** e **resumo mensal** com a quebra de gastos por categoria.
- **Exportação CSV** do extrato, respeitando os mesmos filtros.
- **Dashboard** web: saldo atual, gráfico de gastos do mês por categoria e formulário para adicionar
  transações (inclusive criando uma categoria nova na hora).

## Stack
- Python 3.11+ · [FastAPI](https://fastapi.tiangolo.com/) · Pydantic · Uvicorn
- SQLite (módulo `sqlite3` da biblioteca padrão) — sem banco externo
- Dashboard em HTML/JS estático com [Chart.js](https://www.chartjs.org/) via CDN
- Testes com pytest + TestClient

## Rodando localmente
```bash
python -m venv .venv
.venv\Scripts\activate            # Windows  (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt
uvicorn app.main:app --reload      # desenvolvimento (recarrega ao salvar)
# ou
python -m app                      # usa HOST/PORT das variáveis de ambiente
```

| Endereço | O que é |
|---|---|
| http://127.0.0.1:8000/ | Dashboard |
| http://127.0.0.1:8000/docs | Documentação interativa (Swagger) — dá para testar todos os endpoints |
| http://127.0.0.1:8000/export.csv | Extrato em CSV |

O banco `gastos.db` é criado automaticamente na raiz do projeto na primeira execução.

## Endpoints

| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/transacoes` | Cria uma transação |
| `GET` | `/transacoes` | Lista transações (filtros opcionais, veja abaixo) |
| `GET` | `/transacoes/{id}` | Busca uma transação |
| `PUT` | `/transacoes/{id}` | Substitui todos os campos de uma transação |
| `DELETE` | `/transacoes/{id}` | Exclui uma transação (204) |
| `POST` | `/categorias` | Cria uma categoria (`{"nome": "alimentação"}`) |
| `GET` | `/categorias` | Lista as categorias |
| `GET` | `/saldo` | Entradas, saídas e saldo de todas as transações |
| `GET` | `/resumo?mes=YYYY-MM` | Totais do mês e gastos por categoria |
| `GET` | `/export.csv` | Extrato em CSV (mesmos filtros de `GET /transacoes`) |
| `GET` | `/` | Dashboard |

**Transação** (corpo de `POST`/`PUT`):
```json
{ "data": "2026-10-02", "descricao": "Mercado", "valor": 182.40, "tipo": "saida", "categoria_id": 1 }
```
- `data` no formato `YYYY-MM-DD`; `valor` > 0, com 2 casas decimais (entre 0,01 e 1 bilhão);
  `tipo` é `"entrada"` ou `"saida"`; `descricao` não pode ser vazia; `categoria_id` é opcional (`null`).

**Filtros** de `GET /transacoes` e `GET /export.csv` — todos opcionais, combinados por E, limites inclusivos:

| Parâmetro | Exemplo | Observação |
|---|---|---|
| `categoria` | `alimentação` ou `1` | nome (sem diferenciar maiúsculas) ou id; inexistente → lista vazia |
| `data_inicio` / `data_fim` | `2026-10-01` | período invertido → 422 |
| `valor_min` / `valor_max` | `20` / `200` | faixa invertida → 422 |

```bash
curl "http://127.0.0.1:8000/transacoes?categoria=transporte&data_inicio=2026-10-01&data_fim=2026-10-31"
```

**Erros** sempre no formato `{"erro": "<mensagem>"}`, com status 422 (validação) ou 404 (não encontrado):
```json
{ "erro": "valor: deve ser maior que 0" }
```

**CSV**: padrão RFC 4180 (vírgula, ponto decimal), UTF-8 com BOM, colunas
`id,data,descricao,valor,tipo,categoria_id,categoria`. No Excel em português, use
*Dados > De texto/CSV* para separar as colunas.

## Testes
```bash
pip install -r requirements-dev.txt
python -m pytest                 # suíte completa — cada teste usa um banco temporário próprio
python -m pytest -k resumo       # só os testes cujo nome contém "resumo"
```

## Deploy
Toda a configuração vem de **variáveis de ambiente** — não há nada a editar no código e o app não usa
credenciais nem segredos. O arquivo [`.env.example`](.env.example) documenta as variáveis.

| Variável | Padrão | Para que serve |
|---|---|---|
| `HOST` | `127.0.0.1` (na imagem Docker: `0.0.0.0`) | Interface de rede. Use `0.0.0.0` para aceitar conexões externas |
| `PORT` | `8000` | Porta HTTP. Plataformas como Render, Railway e Heroku definem sozinhas |
| `GASTOS_DB_PATH` | `./gastos.db` (na imagem Docker: `/data/gastos.db`) | Caminho do arquivo SQLite |

> [!IMPORTANT]
> O SQLite é um arquivo: **coloque `GASTOS_DB_PATH` num disco/volume persistente**, senão os dados somem a
> cada deploy ou novo container. Rode **uma única instância** — várias instâncias não compartilham o arquivo.

### Opção A — Docker (qualquer servidor ou VM)
```bash
docker build -t controle-gastos .
docker volume create gastos-dados
docker run -d --name controle-gastos --restart unless-stopped \
  -e PORT=8000 -p 8000:8000 -v gastos-dados:/data controle-gastos
docker logs controle-gastos       # deve mostrar: Uvicorn running on http://0.0.0.0:8000
```
- **Outra porta:** `-e PORT=9000 -p 9000:9000`.
- **Atualizar a versão:** rode `docker build` de novo, depois `docker rm -f controle-gastos` e o mesmo
  `docker run` — os dados ficam no volume `gastos-dados`.
- A imagem usa `python:3.12-slim` e roda com um usuário sem privilégios de root.

### Opção B — Plataforma (Render, Railway, Fly.io…)
1. Publique o repositório no GitHub e crie um **serviço web** apontando para ele.
2. **Build:** a plataforma detecta o `Dockerfile` automaticamente. Sem Docker, use um ambiente Python com
   build `pip install -r requirements.txt` e comando de start `python -m app` (já definido no `Procfile`).
3. **Variáveis:** a plataforma define `PORT`. Sem Docker, defina também `HOST=0.0.0.0`.
4. **Disco persistente:** crie um disco/volume (Render: *Disks*; Railway: *Volumes*; Fly: `fly volumes create`)
   montado em `/data` e defina `GASTOS_DB_PATH=/data/gastos.db` (já é o padrão da imagem Docker).
5. **Instâncias:** 1. **Health check:** `GET /saldo` (responde 200 com JSON).

### Conferindo o deploy
```bash
curl https://<seu-app>/saldo            # {"entradas": ..., "saidas": ..., "saldo": ...}
curl -OJ https://<seu-app>/export.csv   # baixa extrato.csv
```
Depois abra `https://<seu-app>/` (dashboard) e `https://<seu-app>/docs`.

### Cuidados em produção
- **Sem autenticação:** a API ainda não tem login — quem tiver a URL consegue ler e alterar os dados.
  Restrinja o acesso (rede privada, VPN ou a proteção por senha da plataforma) até existir autenticação.
- **Backup:** basta copiar o arquivo do banco, por exemplo
  `docker cp controle-gastos:/data/gastos.db ./backup.db`.

## Estrutura do projeto
```
app/
  main.py          # cria o FastAPI, inicializa o banco, trata erros, inclui as rotas
  __main__.py      # `python -m app`: sobe o Uvicorn com HOST/PORT do ambiente
  database.py      # acesso ao SQLite (schema, consultas, agregações)
  models.py        # schemas Pydantic (validação de entrada e saída)
  routes/          # transacoes, categorias, resumo, export, dashboard
  static/          # dashboard.html
tests/             # suíte pytest
specs/             # specs de cada aula (requisitos)
Dockerfile, Procfile, .env.example   # deploy
CLAUDE.md          # convenções e decisões de projeto
```

## Desenvolvimento
Cada funcionalidade nasce de uma spec em `specs/` e segue o ciclo **plano → aprovação → implementação →
verificação dos critérios de aceite → commit** (slash command `/implementar-spec` em `.claude/commands`).
Convenções de código e todas as decisões de projeto (formato das mensagens de erro, regras de validação,
arredondamento etc.) estão no [`CLAUDE.md`](CLAUDE.md).
