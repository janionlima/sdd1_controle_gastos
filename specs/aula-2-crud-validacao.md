# Spec — Aula 2: CRUD completo com validação

**Projeto:** Controle de Gastos Pessoais
**Stack:** Python 3.11+ · FastAPI · SQLite · Pydantic

## Convenções gerais do projeto (valem para todas as specs)
- API REST em FastAPI; respostas em JSON; datas no formato ISO `YYYY-MM-DD`.
- Persistência em SQLite num arquivo local do projeto; a estrutura do banco é criada na inicialização se não existir.
- Valores monetários tratados com 2 casas decimais; `tipo` sempre `"entrada"` ou `"saida"`.
- Erros de validação retornam HTTP 422 com corpo `{ "erro": "<mensagem clara>" }`.
- Código organizado em módulos (rotas, modelos, acesso a dados) e versionado no Git a cada aula.

---

**Objetivo (por quê):** permitir corrigir e remover lançamentos e garantir que só entrem dados válidos, tornando o app confiável.

**Contexto:** já existe `POST /transacoes` e `GET /transacoes` (Aula 1). Esta spec adiciona edição, exclusão e validação.

**Requisitos funcionais:**
1. Editar uma transação existente pelo `id` (todos os campos editáveis).
2. Excluir uma transação pelo `id`.
3. Validar em todas as escritas (criar e editar):
   - `valor` deve ser > 0;
   - `tipo` deve ser `entrada` ou `saida`;
   - `data` deve ser uma data ISO válida;
   - `descricao` não pode ser vazia.

**Contrato de API:**
- `PUT /transacoes/{id}` — atualiza a transação; retorna 200 com o objeto atualizado, ou 404 se não existir.
- `DELETE /transacoes/{id}` — remove; retorna 204, ou 404 se não existir.
- `POST`/`PUT` inválidos retornam 422 com `{ "erro": "<mensagem>" }`.

**Critérios de aceite:**
- `PUT /transacoes/{id}` altera os campos e reflete em `GET /transacoes`.
- `DELETE /transacoes/{id}` remove a transação; buscar depois retorna 404.
- Enviar `valor` ≤ 0, `tipo` inválido, `data` malformada ou `descricao` vazia retorna 422 com mensagem clara.
- Operar sobre um `id` inexistente retorna 404.

**Fora de escopo:** categorias, cálculos, filtros.

**Restrições técnicas:** centralizar a validação nos schemas Pydantic; mensagens de erro legíveis para humanos.
