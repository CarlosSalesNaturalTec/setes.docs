## Why

O Épico 8 (Administração do Sistema) está quase completo — cadastro, unidades, tipos de
processo, roteiros, configuração mínima e restauração de documento já foram entregues —
mas faltam **duas histórias de administração de usuário**: US 8.3 (conceder/revogar
permissão de auditoria) e US 8.4 (desativar usuário). Sem a US 8.3 o perfil **Auditor**
não existe no sistema: os specs arquivados já o citam em cenários de "acesso negado"
(ex.: `restauracao-documento`), mas nenhuma coluna, rota ou mecanismo o materializa — e
ele é **pré-requisito rígido do Épico 9** (Auditoria e Relatórios), que não pode começar
sem uma permissão concedível. Sem a US 8.4 não há como revogar o acesso de um usuário ao
sistema de forma controlada (com guarda contra órfãos de processo).

Este change entrega **apenas o mecanismo de concessão** da permissão de auditoria e a
desativação de usuário. O **consumo** dessa permissão — ver processos sigilosos (US 9.1),
gerar relatórios consolidados (US 9.2) — é o Épico 9 e fica **fora deste escopo**.

## What Changes

- **US 8.3 — Permissão de auditoria (mecanismo):** o Administrador pode **conceder** e
  **revogar** a permissão de auditoria de qualquer usuário. A permissão é uma flag
  booleana `usuario.pode_auditar`, **ortogonal ao `perfil`** (Servidor/Gestor/Administrador
  permanecem intactos; revogar apenas volta a flag a `false`, sem "lembrar" perfil
  anterior). Toda concessão e toda revogação são registradas como evento imutável em
  `log_seguranca`. Não-Administrador que tente conceder/revogar recebe **acesso negado**
  (registrado).
- **US 8.4 — Desativação de usuário:** o Administrador pode desativar um usuário
  (`status` → `inativo`), com **guarda de processos pendentes**: se o usuário for o
  responsável atual por processos **em andamento** (`aberto`/`em_tramitacao`), a
  desativação é bloqueada com a mensagem "Este usuário possui X processo(s) em andamento.
  Reatribua os processos antes de desativar." O login de usuário inativo já é rejeitado
  (`auth.py`), então a desativação encerra o acesso imediatamente. A desativação é
  registrada em `log_seguranca`.
- **Escopo negativo (explícito):** este change **não** implementa nenhuma leitura de
  processo sigiloso, nenhum relatório consolidado, nem a UI/rota de auditoria. Apenas o
  gancho (`pode_auditar`) fica pronto para o Épico 9 consumir.

## Capabilities

### New Capabilities
- `permissao-auditoria`: mecanismo de concessão/revogação da permissão de auditoria por
  Administrador (flag `pode_auditar`, ortogonal ao perfil), com registro imutável e
  cenário de acesso negado para não-Administrador. Cobre US 8.3. **Não** cobre o consumo
  da permissão (Épico 9).

### Modified Capabilities
- `gestao-usuarios`: adiciona o requisito de **desativação de usuário** com guarda de
  processos em andamento sob responsabilidade (US 8.4).

## Impact

- **Requer (arquivados):** `identidade-e-estrutura-organizacional` (usuário, perfil,
  `log_seguranca`, `StatusUsuario`) e `processos-e-workflow` (`processo`, `tramitacao`,
  `StatusProcesso`, base para contar processos em andamento sob responsabilidade).
- **Tabelas PostgreSQL afetadas:**
  - `usuario` — **nova coluna** `pode_auditar BOOLEAN NOT NULL DEFAULT false`.
  - `log_seguranca` — sem colunas novas; **novos valores** no enum `TipoEventoLog`:
    `permissao_auditoria_concedida`, `permissao_auditoria_revogada`, `usuario_desativado`
    (ALTER TYPE ... ADD VALUE, não retroativo).
  - `usuario.status` (enum `StatusUsuario`, já existente) passa a ser transicionado para
    `inativo` pela rota de desativação. Sem tabela nova.
- **API (FastAPI):** novas rotas Admin-only em `routers/usuarios.py` —
  `POST /usuarios/{id}/permissao-auditoria` (conceder), `DELETE /usuarios/{id}/permissao-auditoria`
  (revogar), `POST /usuarios/{id}/desativar`. `UsuarioResponse` passa a expor `pode_auditar`.
  Novo seam de leitura para contar processos em andamento sob responsabilidade do usuário.
- **Contrato:** muda schema/rotas do FastAPI → **regenerar** `packages/api-types`
  (`pnpm gen:types`); o CI `types-drift` falha se defasado.
- **Frontend (Next.js):** `apps/web/app/admin/usuarios/page.tsx` ganha ações "Conceder/
  Revogar Permissão de Auditoria" e "Desativar Usuário" (Admin-only), com a mensagem de
  guarda de processos pendentes.
- **Segredos/buckets:** nenhum novo segredo no Secret Manager, nenhum novo bucket.
- **LGPD:** não coleta nem trata dado pessoal de titular/interessado (CPF/CNPJ, nome de
  interessado). `pode_auditar` e `status` são atributos administrativos do usuário
  interno; os registros em `log_seguranca` são trilha de segurança (retenção conforme a
  política de log já vigente), não dado de titular.
