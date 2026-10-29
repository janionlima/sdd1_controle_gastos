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
uvicorn app.main:app --reload
```
Documentação interativa: http://127.0.0.1:8000/docs

## Estrutura de pastas
```
app/
  main.py        # cria o FastAPI, inicializa o banco (lifespan), handler de erro 422, inclui routers
  database.py    # acesso a dados: DB_PATH, get_connection(), SCHEMA, init_db()
  models.py      # schemas Pydantic de entrada/saída
  routes/        # um router por recurso (ex.: transacoes.py)
tests/           # testes pytest (a partir da Aula 5)
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

## Fluxo de trabalho
- Implementar uma spec por vez com `/implementar-spec specs/<arquivo>.md`: plano → aprovação → implementação → verificação dos critérios de aceite → commit.
- Não adiantar features de aulas futuras.
- Toda nova decisão de projeto (formato de mensagens, regras ambíguas etc.) deve ser registrada neste arquivo.
