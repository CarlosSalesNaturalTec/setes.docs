## 1. Pré-requisitos

- [ ] 1.1 Confirmar que `manual-mkdocs` está arquivado e que o site publica.
  **Aceite**: `openspec/changes/archive/2026-08-04-manual-mkdocs/` existe;
  `mkdocs.yml`, `requirements-docs.txt` e `.github/workflows/publicar-manual.yml`
  estão na árvore. Sem isso a regra não tem objeto.
- [ ] 1.2 Rodar `mkdocs build --strict` localmente **antes de qualquer alteração**,
  para estabelecer a linha de base. **Aceite**: o build passa sem erro. Se já
  falhar aqui, o defeito é pré-existente e deve ser registrado separadamente — não
  é regressão introduzida por este change, e a tarefa 4.2 partiria de premissa
  errada.

## 2. Regra no `openspec/config.yaml` (D1, D2)

- [ ] 2.1 Acrescentar a `rules.tasks` a regra de atualização de `docs/manual/**`,
  com a formulação vinculante usada pelas três regras vizinhas ("não é opcional").
  **Aceite**: a regra está em `rules.tasks`, não em `rules.proposal` nem em
  `rules.design`; o texto exige **tarefa** correspondente no change, não apenas
  menção na proposta.
- [ ] 2.2 Incluir na mesma regra o gatilho enunciado **por exclusão** (D2): o que
  dispara (tela nova/removida, passo a passo alterado, campo/botão/menu alterado,
  texto exibido ao usuário, mudança no que um perfil pode fazer) e o que **não**
  dispara (refatoração sem efeito visível, correção de bug que restaura
  comportamento já documentado, migration/schema interno, infraestrutura, CI,
  Terraform, mudança de teste, performance sem mudança de UI). **Aceite**: o caso
  da correção de bug aparece explicitamente no lado "não dispara" — é o caso
  decisivo de D2.
- [ ] 2.3 Incluir na regra o critério de aceite padrão da tarefa que ela gera:
  execução de `mkdocs build --strict` local (D5). **Aceite**: a regra não se
  contenta com "o manual foi atualizado"; exige a verificação.
- [ ] 2.4 Validar que o `config.yaml` continua sendo lido pela CLI após a edição.
  **Aceite**: `openspec list` e `openspec status --change manual-sempre-atualizado`
  executam sem erro de parsing de YAML.

## 3. Seção no `CLAUDE.md` (D4)

- [ ] 3.1 Acrescentar seção sobre a documentação do usuário cobrindo os quatro
  pontos: onde o manual vive (`docs/manual/`), que é publicado como site MkDocs no
  GitHub Pages, que a publicação ocorre **apenas após merge em `main`**
  (`publicar-manual.yml`, `on: push: branches: [main]` + path filter), e como
  validá-lo localmente (`mkdocs build --strict`). **Aceite**: quem lê o `CLAUDE.md`
  passa a saber que o manual existe — hoje o arquivo não o menciona em lugar algum.
- [ ] 3.2 Replicar na seção o alerta sobre o `docs_dir` (D4): ele aponta para
  `docs/manual/` por **controle de segurança**, nunca para `docs/`, porque o site
  do Pages é público e `docs/` contém PRD, URLs de produção, configuração de
  provedor de e-mail e o PDF comercial do cliente. **Aceite**: o alerta está no
  `CLAUDE.md` além do comentário já existente no `mkdocs.yml`; a duplicação é
  deliberada e está justificada em D4.
- [ ] 3.3 Referenciar a regra nova do `config.yaml` a partir da seção, para que os
  dois arquivos não descrevam a obrigação de formas divergentes. **Aceite**: o
  `CLAUDE.md` aponta para a regra em vez de reenunciá-la com outras palavras.

## 4. Job de validação no CI (D3)

- [ ] 4.1 Adicionar o filtro `manual` ao job `changes` de
  `.github/workflows/ci.yml`, cobrindo `docs/manual/**`, `mkdocs.yml` e
  `requirements-docs.txt`, e expor a saída correspondente. **Aceite**: o filtro
  segue o padrão dos filtros `api` e `web` já existentes (`dorny/paths-filter@v3`),
  e `outputs` declara `manual`.
- [ ] 4.2 Adicionar o job `manual` executando `pip install -r requirements-docs.txt`
  e `mkdocs build --strict`, condicionado a `needs.changes.outputs.manual == 'true'`,
  com `actions/setup-python@v5` na mesma versão `3.12` usada por
  `publicar-manual.yml`. **Aceite**: o job **não** faz upload de artefato, **não**
  publica e **não** declara `pages: write` nem `id-token: write` — apenas valida.
- [ ] 4.3 Confirmar que `.github/workflows/publicar-manual.yml` permanece
  **inalterado**. **Aceite**: `git diff` não mostra alteração nesse arquivo; a
  publicação continua ocorrendo exclusivamente após merge em `main` (item 4.2 do
  pedido original preservado).
- [ ] 4.4 Verificar que o job **falha** quando deve: em branch de teste, introduzir
  um link quebrado numa página de `docs/manual/` e confirmar que o job `manual`
  reprova o PR; desfazer em seguida. **Aceite**: houve uma execução vermelha
  observada por essa causa. Sem isso, a única evidência é um job verde — que também
  é o resultado de um job que não testa nada (Migration Plan do design).
- [ ] 4.5 Verificar que o job **não roda** quando não deve: PR que toca apenas
  `apps/api/**` ou `apps/web/**` não dispara o job `manual`. **Aceite**: o job
  aparece como ignorado na execução do CI desse PR.

## 5. Fechamento

- [ ] 5.1 Rodar `mkdocs build --strict` localmente uma última vez. **Aceite**: passa
  — este change não altera conteúdo do manual, então o resultado deve ser idêntico
  ao da linha de base da tarefa 1.2.
- [ ] 5.2 Conferir a coerência entre `proposal.md`, `design.md` e o que foi
  implementado quanto ao job de CI. **Aceite**: a proposta descreve o job de
  validação em PR (foi emendada por D3) e não afirma mais "nenhuma automação nova
  de CI".
- [ ] 5.3 Registrar que este change deve ser aplicado **antes** de
  `marca-visual-despapelize` e `responsividade-mobile`. **Aceite**: ambos alteram
  telas descritas no manual; aplicados antes desta regra, ela nasceria já com duas
  exceções (Migration Plan do design).

<!-- Regras de tasks do projeto não aplicáveis, declaradas para que a ausência não
seja lida como omissão: não há tarefa de migration/schema a separar de tarefa de
endpoint/UI (nenhuma migration Alembic, nenhum endpoint); nenhuma tarefa toca
histórico de tramitação ou dados pessoais, logo não há teste automatizado
correspondente exigido; nenhuma tarefa implementa ou altera login, tramitação,
documentos ou consulta pública, logo não há teste E2E Playwright exigido; nenhuma
tarefa muda rota ou schema do FastAPI, logo `pnpm gen:types` não se aplica. Este
change não toca código de aplicação. -->
