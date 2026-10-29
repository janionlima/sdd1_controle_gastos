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
  | campo ausente | `<campo>: campo obrigatório` |
  | JSON inválido | `corpo da requisição não é um JSON válido` |
  | outros | `<campo>: <mensagem original do Pydantic>` |
- **`descricao` é gravada sem espaços nas pontas** (`strip_whitespace`); `data` só aceita string ISO estrita.
- **`valor` é estrito** (`strict=True`): aceita só número JSON (int ou float); booleano e número em string são recusados.

## Fluxo de trabalho
- Implementar uma spec por vez com `/implementar-spec specs/<arquivo>.md`: plano → aprovação → implementação → verificação dos critérios de aceite → commit.
- Não adiantar features de aulas futuras.
- Toda nova decisão de projeto (formato de mensagens, regras ambíguas etc.) deve ser registrada neste arquivo.
