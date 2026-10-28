# Spec — Aula 1: Registrar e listar transações

**Projeto:** Controle de Gastos Pessoais
**Stack:** Python 3.11+ · FastAPI · SQLite · Pydantic

## Convenções gerais do projeto (valem para todas as specs)
- API REST em FastAPI; respostas em JSON; datas no formato ISO `YYYY-MM-DD`.
- Persistência em SQLite num arquivo local do projeto; a estrutura do banco é criada na inicialização se não existir.
- Valores monetários tratados com 2 casas decimais; `tipo` sempre `"entrada"` ou `"saida"`.
- Erros de validação retornam HTTP 422 com corpo `{ "erro": "<mensagem clara>" }`.
- Código organizado em módulos (rotas, modelos, acesso a dados) e versionado no Git a cada aula.

---

**Objetivo (por quê):** permitir que o usuário registre gastos e receitas e veja tudo o que registrou, estabelecendo a base persistente do app.

**Contexto:** projeto novo, ainda sem nada implementado. Esta é a primeira feature.

**Requisitos funcionais:**
1. Registrar uma transação com os campos: `data` (ISO), `descricao` (texto), `valor` (número > 0) e `tipo` (`entrada` ou `saida`).
2. Listar todas as transações registradas, mais recentes primeiro.
3. As transações persistem em SQLite e sobrevivem ao reinício do servidor.

**Modelo de dados — `transacao`:**
- `id` (inteiro, gerado automaticamente)
- `data` (texto ISO `YYYY-MM-DD`)
- `descricao` (texto)
- `valor` (decimal, 2 casas)
- `tipo` (texto: `entrada` | `saida`)

**Contrato de API:**
- `POST /transacoes` — recebe `{data, descricao, valor, tipo}`; retorna 201 com a transação criada (incluindo `id`).
- `GET /transacoes` — retorna a lista de transações ordenada por `data` decrescente.

**Critérios de aceite:**
- Criar uma transação via `POST /transacoes` retorna 201 e o objeto com `id`.
- `GET /transacoes` lista as transações criadas, mais recentes primeiro.
- Após reiniciar o servidor, as transações continuam disponíveis.

**Fora de escopo:** edição, exclusão, validação avançada, categorias, cálculos, autenticação.

**Restrições técnicas:** usar FastAPI + Pydantic para os schemas; SQLite via biblioteca padrão (`sqlite3`) ou SQLModel — escolher e registrar no `CLAUDE.md`.
