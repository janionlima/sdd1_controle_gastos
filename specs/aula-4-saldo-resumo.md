# Spec — Aula 4: Saldo e resumo mensal

**Projeto:** Controle de Gastos Pessoais
**Stack:** Python 3.11+ · FastAPI · SQLite · Pydantic

## Convenções gerais do projeto (valem para todas as specs)
- API REST em FastAPI; respostas em JSON; datas no formato ISO `YYYY-MM-DD`.
- Persistência em SQLite num arquivo local do projeto; a estrutura do banco é criada na inicialização se não existir.
- Valores monetários tratados com 2 casas decimais; `tipo` sempre `"entrada"` ou `"saida"`.
- Erros de validação retornam HTTP 422 com corpo `{ "erro": "<mensagem clara>" }`.
- Código organizado em módulos (rotas, modelos, acesso a dados) e versionado no Git a cada aula.

---

**Objetivo (por quê):** transformar os lançamentos em informação útil — saldo atual e um panorama mensal por categoria.

**Contexto:** transações com categorias (Aulas 1–3). Ainda não há nenhum cálculo agregado.

**Requisitos funcionais:**
1. Calcular o **saldo total**: soma das entradas menos soma das saídas.
2. Gerar um **resumo mensal** para um mês informado: total de entradas, total de saídas, saldo do mês e quebra de gastos por categoria.

**Contrato de API:**
- `GET /saldo` — retorna `{ entradas, saidas, saldo }` de todas as transações.
- `GET /resumo?mes=YYYY-MM` — retorna `{ mes, entradas, saidas, saldo, por_categoria: [{categoria, total}] }` para o mês informado.

**Critérios de aceite:**
- `GET /saldo` retorna entradas, saídas e saldo corretos considerando todas as transações.
- `GET /resumo?mes=2026-08` retorna os totais do mês e a quebra por categoria corretos.
- Mês sem transações retorna zeros e lista de categorias vazia, sem erro.
- Parâmetro `mes` malformado retorna 422.

**Fora de escopo:** filtros avançados, exportação, gráficos.

**Restrições técnicas:** cálculos feitos preferencialmente via SQL (agregações), não em laços Python; arredondar para 2 casas.
