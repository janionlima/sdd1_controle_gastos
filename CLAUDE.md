# Controle de Gastos Pessoais — API

API REST para registrar e consultar gastos e receitas pessoais. O projeto é construído aula a aula
seguindo Spec-Driven Development (SDD): cada feature tem uma spec em `specs/`, implementada uma por vez.

## Stack
- Python 3.11+
- FastAPI (rotas) + Pydantic (schemas/validação)
- SQLite via `sqlite3` da biblioteca padrão
- Uvicorn (servidor ASGI)

## Como rodar
```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt
uvicorn app.main:app --reload    # desenvolvimento
python -m app                    # host/porta vindos do ambiente (HOST, PORT)
```
Dashboard: http://127.0.0.1:8000/ · Documentação interativa: http://127.0.0.1:8000/docs ·
Extrato: http://127.0.0.1:8000/export.csv

Para publicar fora da máquina local, ver **Deploy** abaixo.

## Deploy
Toda configuração vem de **variáveis de ambiente** — nada a editar no código. O app não usa
credenciais/segredos; `.env.example` documenta as variáveis e `.env` está no `.gitignore`.

| Variável | Padrão | Uso |
|---|---|---|
| `HOST` | `127.0.0.1` (imagem Docker: `0.0.0.0`) | interface de rede; `0.0.0.0` para aceitar conexões externas |
| `PORT` | `8000` | porta HTTP (Render/Railway/Heroku definem sozinhas) |
| `GASTOS_DB_PATH` | `./gastos.db` (imagem Docker: `/data/gastos.db`) | arquivo SQLite — **sempre num disco/volume persistente** |

> ⚠️ SQLite é um arquivo: sem volume persistente, os dados **somem a cada deploy/novo container**.
> Rode **uma única instância** (sem escalar horizontalmente) — várias instâncias não compartilham o arquivo.

### Opção A — Docker em qualquer servidor/VM
```bash
docker build -t controle-gastos .
docker volume create gastos-dados
docker run -d --name controle-gastos --restart unless-stopped \
  -e PORT=8000 -p 8000:8000 -v gastos-dados:/data controle-gastos
docker logs controle-gastos        # deve mostrar: Uvicorn running on http://0.0.0.0:8000
```
Trocar a porta: `-e PORT=9000 -p 9000:9000`. Atualizar versão: `docker build` de novo,
`docker rm -f controle-gastos` e o mesmo `docker run` (o volume mantém os dados).

### Opção B — PaaS (Render, Railway, Fly.io…)
1. Subir o repositório para o GitHub e criar um serviço web apontando para ele.
2. Build: **Dockerfile** (detectado automaticamente) — ou, sem Docker, ambiente Python com
   build `pip install -r requirements.txt` e start `python -m app` (já está no `Procfile`).
3. Variáveis: a plataforma define `PORT`. Sem Docker, definir `HOST=0.0.0.0`.
4. Criar um **disco persistente** (Render: *Disks*; Railway: *Volumes*; Fly: `fly volumes create`)
   montado em `/data` e definir `GASTOS_DB_PATH=/data/gastos.db` (já é o padrão da imagem Docker).
5. Instâncias: 1. Health check: `GET /saldo` (200 com JSON).

### Conferir depois do deploy
```bash
curl https://<seu-app>/saldo          # {"entradas": ..., "saidas": ..., "saldo": ...}
curl -OJ https://<seu-app>/export.csv # baixa extrato.csv
```
e abrir `https://<seu-app>/` (dashboard) e `/docs`. **Atenção:** a API não tem autenticação (fora de
escopo); quem tiver a URL lê e altera os dados — em produção, restrinja o acesso (rede privada, proxy
com senha da plataforma) até existir autenticação. Backup: copiar o arquivo de `GASTOS_DB_PATH`
(ex.: `docker cp controle-gastos:/data/gastos.db ./backup.db`).

Testes (dependências de desenvolvimento ficam em `requirements-dev.txt`):
```bash
pip install -r requirements-dev.txt
python -m pytest                          # suíte inteira (usa banco temporário por teste; nunca toca o gastos.db)
python -m pytest -v tests/test_filtros.py # um arquivo, mostrando cada teste
python -m pytest -k resumo                # só os testes cujo nome contém "resumo"
```
Convenções da suíte: um arquivo `test_<área>.py` por recurso/aula; cada teste começa com banco vazio e
cria seus dados via API (fixtures `criar_transacao`/`criar_categoria`); casos de erro usam
`@pytest.mark.parametrize` e conferem o corpo exato `{"erro": ...}`; listas são comparadas por ids na
ordem da API (`data DESC, id DESC`).

## Estrutura de pastas
```
app/
  main.py        # cria o FastAPI, inicializa o banco (lifespan), handler de erro 422, inclui routers
  database.py    # acesso a dados: DB_PATH, get_connection(), SCHEMA, init_db()
  models.py      # schemas Pydantic de entrada/saída
  __main__.py    # `python -m app`: uvicorn com HOST/PORT do ambiente
  routes/        # um router por recurso: transacoes, categorias, resumo (/saldo, /resumo),
                 #   export (/export.csv), dashboard (/)
  static/        # dashboard.html (HTML estático + Chart.js por CDN)
Dockerfile, .dockerignore, Procfile, .env.example   # deploy
tests/           # pytest + TestClient (ver "Testes" abaixo)
  conftest.py         # fixtures: client (banco temporário), criar_transacao, criar_categoria; helper ids()
  test_transacoes.py  # Aulas 1–2: CRUD, ordenação, 404, validação 422 (POST e PUT)
  test_categorias.py  # Aula 3: categorias, nome único, categoria_id opcional/inexistente
  test_filtros.py     # Aulas 3 e 5: filtros isolados e combinados, limites inclusivos, 422
  test_resumo.py      # Aula 4: /saldo e /resumo (mês cheio, vazio, mes inválido)
  test_export.py      # Aula 6: CSV (colunas, BOM, filtros, 422, injeção de fórmula)
  test_dashboard.py   # Aula 6: GET / serve o HTML que consome /saldo e /resumo
  test_config.py      # Aula 6: `python -m app` lê HOST/PORT do ambiente
specs/           # specs de cada aula (fonte de verdade dos requisitos)
docs/            # roteiro de prompts
.claude/commands # slash commands do projeto (/implementar-spec)
```

## Convenções
- Datas sempre em ISO `YYYY-MM-DD`.
- Valores monetários com 2 casas decimais.
- `tipo` é sempre `"entrada"` ou `"saida"`.
- Erros de validação retornam HTTP 422 com corpo `{ "erro": "<mensagem>" }`
  (handler global de `RequestValidationError` em `app/main.py`; erros de regra de negócio devem seguir o mesmo formato).
- Banco SQLite em arquivo local, criado na inicialização se não existir (`CREATE TABLE IF NOT EXISTS` em `SCHEMA`).
- SQL sempre com parâmetros vinculados (`?`), nunca concatenando valores na query.
- Código organizado em módulos: rotas (`routes/`), modelos (`models.py`), acesso a dados (`database.py`).

## Decisões registradas
- **`sqlite3` (stdlib) em vez de SQLModel:** sem dependência extra, SQL explícito e fácil de acompanhar;
  os schemas da API continuam em Pydantic.
- **Caminho do banco:** `gastos.db` na raiz do projeto, sobrescrevível pela variável de ambiente
  `GASTOS_DB_PATH` (usada para banco de teste e deploy). O arquivo `.db` não é versionado.
- **Valores em centavos no banco:** a coluna é `valor_centavos INTEGER`; a conversão reais ↔ centavos
  acontece só em `database.py` (`round(valor * 100)` / `centavos / 100`). Na API o campo é `valor` (número).
- **Ordenação de `GET /transacoes`:** `ORDER BY data DESC, id DESC` (mesma data → a criada por último primeiro).
- **`GET /transacoes/{id}`:** existe para permitir "buscar" uma transação (e confirmar 404 após exclusão).
- **`PUT` é substituição completa:** mesmo schema e mesmas validações do `POST` (`TransacaoCreate`).
- **Todo erro usa o corpo `{"erro": ...}`**, não só o 422: um handler de `HTTPException` em `app/main.py`
  converte `detail` → `erro` mantendo o status (ex.: 404 `{"erro": "Transação 7 não encontrada"}`).
- **Validação antes da existência:** em `PUT /transacoes/{id}` o corpo é validado primeiro; corpo inválido
  responde 422 mesmo que o `id` não exista. Só com corpo válido o `id` inexistente responde 404.
- **Mensagens de validação em português**, formato `"<campo>: <mensagem>"` (só o primeiro erro).
  Tradução por tipo de erro do Pydantic em `_MENSAGENS` (`app/main.py`):

  | Situação | Mensagem |
  |---|---|
  | `valor` ≤ 0 | `valor: deve ser maior que 0` |
  | `valor` não numérico | `valor: deve ser um número` |
  | `tipo` inválido | `tipo: deve ser 'entrada' ou 'saida'` |
  | `data` fora de `YYYY-MM-DD` ou inexistente | `data: deve ser uma data válida no formato YYYY-MM-DD` |
  | `descricao` vazia/só espaços | `descricao: não pode ser vazia` |
  | `id` da rota não inteiro | `id: deve ser um número inteiro` |
  | `categoria_id` não inteiro (inclui booleano e string) | `categoria_id: deve ser um número inteiro` |
  | `categoria_id` inexistente | `categoria_id: categoria <id> não existe` |
  | `nome` de categoria vazio / só dígitos | `nome: não pode ser vazia` / `nome: não pode conter apenas dígitos` |
  | `nome` de categoria repetido | `nome: categoria '<nome>' já existe` |
  | `?categoria=` vazio | `categoria: não pode ser vazia` |
  | `?mes=` fora de `YYYY-MM` (mês 01–12) | `mes: deve ser um mês válido no formato YYYY-MM` |
  | `data_inicio` > `data_fim` | `data_inicio: não pode ser posterior a data_fim` |
  | `valor_min` > `valor_max` | `valor_min: não pode ser maior que valor_max` |
  | `valor` que arredonda para 0 centavos (ex.: 0.001) | `valor: deve ser no mínimo 0.01` |
  | `valor`, `valor_min`, `valor_max` > R$ 1 bilhão | `<campo>: deve ser no máximo 1000000000` |
  | query param desconhecido (ex.: `data_inicial`) | `<param>: parâmetro desconhecido` |
  | campo ausente | `<campo>: campo obrigatório` |
  | JSON inválido | `corpo da requisição não é um JSON válido` |
  | outros | `<campo>: <mensagem original do Pydantic>` |
- **`descricao` é gravada sem espaços nas pontas** (`strip_whitespace`); `data` só aceita string ISO estrita.
- **`valor` é estrito** (`strict=True`): aceita só número JSON (int ou float); booleano e número em string são recusados.
- **(Aula 3) `categoria_id` é opcional** (pode ser `null`): mantém compatíveis as transações antigas e os
  clientes das Aulas 1–2, e o `PUT` (substituição completa) não obriga a escolher categoria. Um `categoria_id`
  enviado com id inexistente responde 422 `{"erro": "categoria_id: categoria <id> não existe"}`.
- **(Aula 3) Filtro por categoria inexistente retorna `200 []`**, não 404: `categoria` é um filtro de busca
  sobre `/transacoes`, que existe, e fica consistente com os filtros combináveis da Aula 5.
- **(Aula 3) `?categoria=<valor>`: só dígitos = id, qualquer outro valor = nome.** Por isso o nome de uma
  categoria não pode ser só dígitos (422).
- **(Aula 3) Nome de categoria é único sem diferenciar maiúsculas** (`COLLATE NOCASE` na coluna; vale também
  no filtro). É gravado sem espaços nas pontas; acentos diferenciam ("alimentação" ≠ "alimentacao").
  Duplicado é regra de negócio: 422 via `HTTPException`.
- **(Aula 3) `PUT` sem `categoria_id` deixa a transação sem categoria** (consequência da substituição completa).
  No `PUT`, a checagem de `categoria_id` inexistente (422) vem antes da de transação inexistente (404).
- **(Aula 3) Migração de schema:** `init_db()` adiciona `categoria_id` com `ALTER TABLE` em bancos antigos
  (as transações existentes ficam com `null`). `PRAGMA foreign_keys = ON` em toda conexão (`get_connection`).
- **(Aula 4) Agregações em SQL sobre centavos:** `SUM(valor_centavos)` (inteiro) e conversão `/ 100` só no fim,
  em `database.py` — sem erro de ponto flutuante; vazio vira 0 via `COALESCE`. `saidas` é positivo e
  `saldo = entradas - saidas` pode ser negativo.
- **(Aula 4) `por_categoria` do `/resumo` soma só saídas** ("gastos"); saídas sem categoria aparecem como
  `{"categoria": null, "total": ...}`, então a soma de `por_categoria` é igual a `saidas`.
  Ordenação: `total DESC`, depois nome. Mês sem saídas → `[]`.
- **(Aula 4) `mes` é obrigatório e estrito** (`YYYY-MM`, mês 01–12; tipo `Mes` em `models.py`); o mês é
  filtrado com `substr(data, 1, 7) = ?`.
- **(Aula 4) Contrato de resposta** (schemas `Saldo`, `Resumo` e `TotalCategoria` em `models.py`):

  ```jsonc
  // GET /saldo  → 200 (todas as transações; banco vazio → zeros)
  { "entradas": 4000.3, "saidas": 5200.29, "saldo": -1199.99 }

  // GET /resumo?mes=2026-08  → 200
  {
    "mes": "2026-08",               // eco do parâmetro
    "entradas": 3000.3,             // soma das entradas do mês
    "saidas": 200.29,               // soma das saídas do mês (positivo)
    "saldo": 2800.01,               // entradas - saidas (pode ser negativo)
    "por_categoria": [              // só saídas; total DESC, depois nome
      { "categoria": "transporte", "total": 150.0 },
      { "categoria": null, "total": 49.99 },        // saídas sem categoria
      { "categoria": "alimentacao", "total": 0.3 }
    ]
  }

  // Mês sem transações → 200
  { "mes": "2026-01", "entradas": 0.0, "saidas": 0.0, "saldo": 0.0, "por_categoria": [] }

  // mes malformado → 422 {"erro": "mes: deve ser um mês válido no formato YYYY-MM"}
  // mes ausente    → 422 {"erro": "mes: campo obrigatório"}
  ```
  Valores são números com até 2 casas; `categoria` é o **nome** da categoria (ou `null`).
- **Query params com tipo validado usam `Annotated[Tipo, Query(...)]`**, nunca `param: Tipo = Query(...)`:
  na segunda forma o FastAPI descarta os validadores (`AfterValidator`) do tipo e aceita qualquer valor.
- **(Aula 5) Filtros de `GET /transacoes`** — `categoria`, `data_inicio`, `data_fim`, `valor_min`, `valor_max`:
  todos opcionais, combinados por E, **limites inclusivos** (`>=` / `<=`). Ficam no modelo `FiltrosTransacao`
  (`models.py`), recebido como `Annotated[FiltrosTransacao, Query()]`; um `model_validator` recusa faixa
  invertida (422). Início igual ao fim é válido (ex.: período de um dia).
  - `data_inicio`/`data_fim` usam o mesmo tipo `DataISO` do campo `data` (ISO estrito, mesma mensagem).
  - `valor_min`/`valor_max`: número finito > 0 (mesmas mensagens de `valor`). Por virem na URL, a string
    `"50"` é aceita — diferente do `valor` no corpo JSON, que é estrito.
  - Valor comparado em centavos (`valor_centavos >= ?` com `_para_centavos(...)`), mantendo a conversão só em `database.py`.
  - A query é montada em `listar_transacoes` juntando **apenas trechos fixos** com `AND`; todo valor vai por `?`.
- **(Aula 5, revisão) Limites numéricos e robustez** — nenhuma entrada pode gerar 500:
  - `valor` tem piso de **1 centavo** (validado após arredondar: 0.001 → 422, antes era gravado como 0 e
    quebrava toda listagem) e teto `VALOR_MAX` = **R$ 1 bilhão** (`models.py`), o mesmo teto vale para
    `valor_min`/`valor_max`. Mantém centavos e somas dentro do INTEGER de 64 bits do SQLite.
  - Ids fora do int64 (path, `categoria_id`, `?categoria=`) não existem: 404 / 422 "não existe" / `[]`
    (`_id_existe_no_sqlite` em `database.py`).
  - "Só dígitos" significa **dígitos ASCII 0-9** (`so_digitos` em `models.py`); `²` ou `١` são texto (nome).
  - Limites de valor fora do centavo arredondam **para dentro** da faixa: `valor_min` → teto, `valor_max` →
    piso (ex.: `valor_max=9.996` não traz 10.00).
  - `FiltrosTransacao` usa `extra="forbid"`: parâmetro com nome errado é 422, não filtro ignorado.
  - `?categoria=` recebe strip como os nomes gravados (`" transporte "` = `transporte`; só espaços → 422).
  - Mensagens de `_MENSAGENS` podem usar o `ctx` do erro Pydantic (ex.: `{le}`).
- **(Aula 6) `GET /export.csv`:** mesmos filtros (`FiltrosTransacao`) e mesma ordem de `GET /transacoes`;
  filtro inválido → 422 JSON. Formato **RFC 4180** via `csv` da stdlib: vírgula, `\r\n`, ponto decimal,
  **UTF-8 com BOM** (o Excel mostra acentos; no Excel pt-BR use "Dados > De texto/CSV" para separar colunas).
  Colunas `id,data,descricao,valor,tipo,categoria_id,categoria` — `valor` sempre com 2 casas (`50.50`),
  `categoria` é o nome (vazio sem categoria). `Content-Disposition: attachment; filename="extrato.csv"`.
  **Anti-injeção de fórmula:** `descricao`/`categoria` iniciadas por `= + - @ \t \r` ganham `'` na frente
  só no CSV (a API JSON devolve o texto original).
- **(Aula 6) Dashboard em `GET /`** (fora do OpenAPI): `app/static/dashboard.html`, HTML/CSS/JS inline sem build.
  Saldo atual via `/saldo`; gastos do mês por categoria via `/resumo?mes=` (seletor de mês, padrão = mês atual,
  `null` → "Sem categoria"); link para o CSV do mês. **Chart.js 4.4.1 fixo** por jsDelivr com hash SRI — ao
  trocar a versão, recalcular o `integrity`. Dados da API entram no DOM só por `textContent` (nunca `innerHTML`).
- **(Aula 6) Deploy configurado por ambiente:** `python -m app` lê `HOST`/`PORT`; `GASTOS_DB_PATH` aponta o
  SQLite. A imagem Docker (`python:3.12-slim`, usuário sem root) define `HOST=0.0.0.0` e grava em `/data`, que
  **deve ser um volume persistente** — sem ele, os dados somem a cada novo container/deploy. Nenhuma credencial
  no código (o app não usa segredos).
- **(Aula 5) Testes:** pytest + `TestClient` (o starlette 1.x exige o pacote `httpx2`). Cada teste recebe a
  fixture `client`, que faz `monkeypatch` de `app.database.DB_PATH` para um arquivo em `tmp_path` (banco novo e
  vazio por teste); `conftest.py` também define `GASTOS_DB_PATH` temporário antes de importar o app.
  Toda spec nova deve vir com testes em `tests/`.

## Fluxo de trabalho
- Implementar uma spec por vez com `/implementar-spec specs/<arquivo>.md`: plano → aprovação → implementação → verificação dos critérios de aceite → commit.
- Não adiantar features de aulas futuras.
- Toda nova decisão de projeto (formato de mensagens, regras ambíguas etc.) deve ser registrada neste arquivo.
