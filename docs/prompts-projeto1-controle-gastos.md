# Roteiro de Prompts — Projeto 1 (Controle de Gastos, Python)

Prompts sugeridos para o Claude Code, aula a aula, seguindo o fluxo completo de SDD:

> **Plano → (revisar) → Escopo → Implementação → Verificação → Commit**

Copie e cole, ajustando os caminhos dos arquivos de spec ao seu repositório. Os prompts são propositalmente **magros**: o peso mora nas specs e no `CLAUDE.md`. Se precisar explicar muita coisa no chat, atualize a spec.

---

## Atalho reutilizável (opcional, mas recomendado)

Crie um slash command para não digitar o ritual toda aula. No projeto: `.claude/commands/implementar-spec.md` com o conteúdo:

```
Leia a spec em: $ARGUMENTS

1. Entre em plan mode e me proponha o plano de implementação. NÃO altere arquivos ainda.
2. Aguarde minha aprovação.
3. Implemente APENAS o que está nesta spec — não adiante features de aulas futuras.
4. Respeite as convenções e decisões registradas no CLAUDE.md.
5. Ao final, verifique o resultado contra os "Critérios de aceite" da spec e me diga, item a item, se cada um passou.
```

Uso em aula: `/implementar-spec specs/aula-3-categorias.md`

---

## Aula 1 — Setup + CLAUDE.md + primeira spec

**Passo 1 — Criar o esqueleto e o CLAUDE.md (antes de qualquer feature):**
```
Vamos iniciar um projeto de API "Controle de Gastos Pessoais".
Stack: Python 3.11+, FastAPI, SQLite, Pydantic.

Antes de implementar qualquer coisa, crie o esqueleto do projeto e um arquivo CLAUDE.md
com: descrição do projeto, stack, como rodar (uvicorn), estrutura de pastas,
e estas convenções — datas em ISO YYYY-MM-DD; valores com 2 casas decimais;
tipo sempre "entrada" ou "saida"; erros de validação em HTTP 422 no formato
{ "erro": "<mensagem>" }; banco SQLite em arquivo local criado na inicialização.
Entre em plan mode primeiro e me mostre o plano antes de criar os arquivos.
```

**Passo 2 — Implementar a primeira spec:**
```
Lembrar de adicionar /reload-skills
/implementar-spec specs/aula-1-transacoes.md
```
(ou, sem o slash command, o prompt equivalente: "Leia a spec em specs/aula-1-transacoes.md, entre em plan mode, mostre o plano, implemente só esta spec respeitando o CLAUDE.md e verifique os critérios de aceite.")

**Passo 3 — Fechar a aula:**
```
Suba o servidor e me mostre como testar POST /transacoes e GET /transacoes.
Depois faça o commit inicial com uma mensagem descritiva.
```

---

## Aula 2 — CRUD completo com validação

**Plano + implementação:**
```
/implementar-spec specs/aula-2-crud-validacao.md
```

**Se o plano estiver incompleto (exemplo de ajuste em plan mode):**
```
No plano, garanta que a validação (valor > 0, tipo válido, data ISO válida,
descrição não vazia) valha tanto para POST quanto para PUT, e que operações
sobre id inexistente retornem 404. Ajuste o plano antes de implementar.
```

**Verificação + memória + commit:**
```
Rode um teste manual de cada critério de aceite e me mostre o resultado.
Se surgiu alguma decisão nova (ex.: formato exato das mensagens de erro),
registre no CLAUDE.md. Depois faça o commit.
```

---

## Aula 3 — Categorias e filtro por categoria

**Decisão de spec antes de codar (bom momento didático):**
```
Antes de implementar, me ajude a decidir dois pontos ambíguos da spec e a
registrá-los no CLAUDE.md: (a) categoria em transação é obrigatória ou opcional?
(b) filtrar por categoria inexistente retorna lista vazia ou 404?
Recomende uma opção para cada e explique o porquê.
```

**Plano + implementação:**
```
/implementar-spec specs/aula-3-categorias.md
```

**Verificação + commit:**
```
Verifique os critérios de aceite, incluindo GET /transacoes?categoria=alimentacao
e criar categoria com nome repetido (deve dar 422). Atualize o CLAUDE.md com as
decisões tomadas e faça o commit.
```

---

## Aula 4 — Saldo e resumo mensal

**Plano + implementação:**
```
/implementar-spec specs/aula-4-saldo-resumo.md
```

**Reforço de restrição no plano:**
```
No plano, faça os cálculos via SQL (agregações), não em laços Python, e arredonde
para 2 casas. Confirme isso antes de implementar.
```

**Verificação + commit:**
```
Teste GET /saldo e GET /resumo?mes=2026-08, e também um mês sem transações
(deve retornar zeros, sem erro). Registre no CLAUDE.md o contrato de resposta
do resumo e faça o commit.
```

---

## Aula 5 — Filtros avançados + testes automatizados

**Plano + implementação:**
```
/implementar-spec specs/aula-5-filtros-testes.md
```

**Verificação com subagente (a novidade desta aula):**
```
Rode a suíte de testes (pytest) e me mostre o resultado. Em seguida, use um
subagente para revisar o código desta feature contra a spec e apontar problemas
de correção ou casos não cobertos. Itere no que ele encontrar.
```

**Commit:**
```
Com os testes passando, atualize o CLAUDE.md com o comando de testes e a estrutura
da suíte, e faça o commit.
```

---

## Aula 6 — Exportação CSV, dashboard e deploy

**Plano + implementação:**
```
/implementar-spec specs/aula-6-export-dashboard-deploy.md
```

**Cuidados no plano:**
```
No plano, garanta: CSV via biblioteca padrão respeitando os filtros da Aula 5;
dashboard como HTML simples servido pelo FastAPI com gráfico via Chart.js (CDN);
nenhuma credencial ou config sensível hardcoded — tudo por variável de ambiente.
```

**Verificação + entrega:**
```
Teste GET /export.csv (com e sem filtros) e abra o dashboard para conferir o
gráfico por categoria e o saldo. Depois me guie no deploy usando variáveis de
ambiente para porta e configs. Atualize o CLAUDE.md com as instruções de deploy
e faça o commit final.
```

---

## Lembretes para conduzir em aula

- **Sempre revise o plano** antes de deixar implementar — é o ponto mais barato para corrigir rumo.
- **Escopo travado:** se o Claude começar a adiantar features de aulas futuras, corte e reaponte para a spec da aula.
- **Chat magro, spec gorda:** precisou explicar muito no chat? Leve isso para a spec ou para o CLAUDE.md.
- **CLAUDE.md ao fim de cada aula:** toda decisão nova vira uma linha lá — é o que faz a aula seguinte "já saber".
- **Commit por aula:** cada incremento fechado é um commit; a spec correspondente entra versionada junto.
