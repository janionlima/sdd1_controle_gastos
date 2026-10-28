# Spec — Aula 3: Categorias e filtro por categoria

**Projeto:** Controle de Gastos Pessoais
**Stack:** Python 3.11+ · FastAPI · SQLite · Pydantic

## Convenções gerais do projeto (valem para todas as specs)
- API REST em FastAPI; respostas em JSON; datas no formato ISO `YYYY-MM-DD`.
- Persistência em SQLite num arquivo local do projeto; a estrutura do banco é criada na inicialização se não existir.
- Valores monetários tratados com 2 casas decimais; `tipo` sempre `"entrada"` ou `"saida"`.
- Erros de validação retornam HTTP 422 com corpo `{ "erro": "<mensagem clara>" }`.
- Código organizado em módulos (rotas, modelos, acesso a dados) e versionado no Git a cada aula.

---

**Objetivo (por quê):** organizar as transações por categoria para permitir enxergar em que o dinheiro é gasto.

**Contexto:** CRUD de transações completo e validado (Aulas 1–2). Ainda não há categorias.

**Requisitos funcionais:**
1. Gerenciar categorias: criar e listar categorias (ex.: alimentação, transporte, salário).
2. Associar uma categoria a cada transação (campo `categoria_id` opcional na transação, ou obrigatório — decidir e registrar no `CLAUDE.md`).
3. Filtrar transações por categoria.

**Modelo de dados — `categoria`:**
- `id` (inteiro, automático)
- `nome` (texto, único)

**Alteração em `transacao`:** adicionar `categoria_id` (referência a `categoria`).

**Contrato de API:**
- `POST /categorias` — cria `{nome}`; nome duplicado retorna 422.
- `GET /categorias` — lista as categorias.
- `GET /transacoes?categoria=<nome ou id>` — retorna só as transações daquela categoria.
- Criar/editar transação passa a aceitar `categoria_id`.

**Critérios de aceite:**
- Criar categorias e associá-las a transações funciona.
- `GET /transacoes?categoria=alimentacao` retorna apenas as transações dessa categoria.
- Filtrar por categoria inexistente retorna lista vazia (ou 404 — decidir e registrar), sem quebrar.
- Criar categoria com nome repetido retorna 422.

**Fora de escopo:** cálculos e resumos, filtros por data/valor.

**Restrições técnicas:** relacionamento por chave estrangeira no SQLite; manter compatibilidade com as transações já criadas (categoria pode ser nula para as antigas).

**Decisões a tomar antes de implementar (registrar no `CLAUDE.md`):**
- (a) categoria em transação é obrigatória ou opcional?
- (b) filtrar por categoria inexistente retorna lista vazia ou 404?
