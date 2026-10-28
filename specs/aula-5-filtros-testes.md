# Spec — Aula 5: Filtros avançados e testes automatizados

**Projeto:** Controle de Gastos Pessoais
**Stack:** Python 3.11+ · FastAPI · SQLite · Pydantic

## Convenções gerais do projeto (valem para todas as specs)
- API REST em FastAPI; respostas em JSON; datas no formato ISO `YYYY-MM-DD`.
- Persistência em SQLite num arquivo local do projeto; a estrutura do banco é criada na inicialização se não existir.
- Valores monetários tratados com 2 casas decimais; `tipo` sempre `"entrada"` ou `"saida"`.
- Erros de validação retornam HTTP 422 com corpo `{ "erro": "<mensagem clara>" }`.
- Código organizado em módulos (rotas, modelos, acesso a dados) e versionado no Git a cada aula.

---

**Objetivo (por quê):** permitir consultas mais ricas ao histórico e blindar o comportamento do app com testes.

**Contexto:** app com transações, categorias, saldo e resumo (Aulas 1–4). Ainda sem testes automatizados.

**Requisitos funcionais:**
1. Filtrar transações combinando: `categoria`, período (`data_inicio` e `data_fim`) e faixa de valor (`valor_min`, `valor_max`).
2. Todos os filtros são opcionais e combináveis numa mesma requisição.
3. Cobrir os fluxos principais com **testes automatizados** (criar, listar, filtrar, resumo, casos de erro).

**Contrato de API:**
- `GET /transacoes` aceita os parâmetros opcionais: `categoria`, `data_inicio`, `data_fim`, `valor_min`, `valor_max`, combinados por E lógico.

**Critérios de aceite:**
- Uma requisição com `categoria` + período + faixa de valor retorna exatamente as transações que satisfazem todas as condições.
- Cada filtro isolado também funciona.
- Período invertido ou valores inválidos retornam 422.
- A suíte de testes (pytest) cobre os fluxos principais e passa integralmente.

**Fora de escopo:** exportação, dashboard, deploy.

**Restrições técnicas:** testes com pytest e o TestClient do FastAPI, isolados do banco de produção (usar banco de teste/temporário); montar a query de filtros dinamicamente de forma segura (parâmetros vinculados, sem concatenar SQL).
