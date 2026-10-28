# Spec — Aula 6: Exportação CSV, dashboard e deploy

**Projeto:** Controle de Gastos Pessoais
**Stack:** Python 3.11+ · FastAPI · SQLite · Pydantic

## Convenções gerais do projeto (valem para todas as specs)
- API REST em FastAPI; respostas em JSON; datas no formato ISO `YYYY-MM-DD`.
- Persistência em SQLite num arquivo local do projeto; a estrutura do banco é criada na inicialização se não existir.
- Valores monetários tratados com 2 casas decimais; `tipo` sempre `"entrada"` ou `"saida"`.
- Erros de validação retornam HTTP 422 com corpo `{ "erro": "<mensagem clara>" }`.
- Código organizado em módulos (rotas, modelos, acesso a dados) e versionado no Git a cada aula.

---

**Objetivo (por quê):** entregar valor final ao usuário — levar os dados para fora do app e visualizá-los — e publicar o projeto.

**Contexto:** app completo e testado (Aulas 1–5). Falta exportação, visualização e publicação.

**Requisitos funcionais:**
1. Exportar o extrato de transações em **CSV** (respeitando os mesmos filtros da Aula 5, quando informados).
2. Servir um **mini-dashboard HTML** com um gráfico de gastos por categoria e o saldo atual.
3. Preparar o app para **deploy**: rodar via Uvicorn, configurações sensíveis por variável de ambiente.

**Contrato de API:**
- `GET /export.csv` — retorna o extrato em CSV (`Content-Type: text/csv`), aceitando os filtros da Aula 5.
- `GET /` (ou `/dashboard`) — serve a página HTML do dashboard.

**Critérios de aceite:**
- `GET /export.csv` baixa um CSV válido com as colunas das transações; filtros aplicados afetam o conteúdo.
- O dashboard exibe o gráfico de gastos por categoria e o saldo atual, consumindo os endpoints existentes.
- O app roda fora da máquina local (deploy), com a porta e configs vindo de variáveis de ambiente.

**Fora de escopo:** autenticação, multiusuário, banco externo (ficam como extensões avançadas).

**Restrições técnicas:** CSV via biblioteca padrão (`csv`); dashboard como HTML estático simples servido pelo FastAPI, com gráfico via uma lib JS leve (ex.: Chart.js por CDN); nenhuma credencial hardcoded no código.
