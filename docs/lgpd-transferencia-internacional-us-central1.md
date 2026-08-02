# LGPD — Transferência internacional de dados e descarte integral (migração para us-central1)

> Referenciado pelo change `openspec/changes/migracao-regiao-us-central1/` (D5).
> Pré-requisito obrigatório antes de qualquer `terraform destroy` do ambiente
> `southamerica-east1`.

## 1. Base legal da transferência internacional

O SETES.DOCS passa a operar com região única em `us-central1` (EUA), deixando de
manter residência de dados em território brasileiro. Isso configura **transferência
internacional de dados pessoais** nos termos do art. 33 da Lei Geral de Proteção de
Dados (Lei 13.709/2018).

- **Controlador**: instituição privada cliente do SETES.DOCS (não órgão da
  administração pública — ver correção de contexto em `openspec/config.yaml`, D6).
- **Fundamento legal adotado**: art. 33 da Lei 13.709/2018 — hipótese aplicável a
  transferência internacional realizada por controlador privado fora das restrições
  específicas do setor público, dispensando as exigências adicionais (cláusulas
  contratuais específicas, selo de conformidade, etc.) que incidiriam sobre dados
  de titulares em maior escala ou sensibilidade. Os dados atualmente tratados são
  dados de teste (ver seção 2).
- **Garantias técnicas mantidas** independentemente da região: acesso restrito por
  perfil/unidade, ausência de leitura pública direta do bucket
  (`public_access_prevention`), anonimização LGPD automática de processos
  arquivados, retenção e purga conforme prazos vigentes.

## 2. Autorização do cliente

| Item | Detalhe |
|---|---|
| Autorizado por | **Ricardo Pita**, Diretor |
| Meio | Mensagem escrita, aplicativo de mensagens |
| Data | **30/07/2026** |
| Decisão autorizada | (a) transferência internacional de dados para `us-central1`; (b) descarte integral dos dados existentes (banco de dados e bucket de documentos) |
| Motivação registrada pelo cliente | Redução de custo final de operação em nuvem, com reconhecimento explícito de que a região `southamerica-east1` (São Paulo/Osasco) responde mais rápido para usuários no Brasil, mas a um custo maior (`docs/Ajustes SETES DOCS.pdf`) |

Esta autorização cobre integralmente a exigência da tarefa 1.2 (autorização
explícita de descarte) — a mesma decisão do cliente autoriza tanto a mudança de
região quanto o descarte dos dados de teste que a viabiliza sem *dump/restore*.

## 3. Descarte integral dos dados existentes

Autorizado pelo mesmo responsável e no mesmo ato (seção 2). Escopo do descarte:

- Instância Cloud SQL (Postgres) do ambiente `southamerica-east1` — todos os dados
  são de teste, sistema ainda em fase de avaliação, não em produção.
- Bucket de documentos do ambiente `southamerica-east1` — todo o conteúdo.
- Os três segredos do Secret Manager (`db-password`, `jwt-signing-key`,
  `sendgrid-api-key`) são recriados na região nova; os dois primeiros são
  **regerados**, não reaproveitados (design D3).

Nenhum *dump*, exportação ou cópia é realizado antes do `terraform destroy` — a
reconstrução do ambiente em `us-central1` parte de estado vazio, com o schema
recriado pelas migrations Alembic existentes.

## 4. Aviso de tratamento (dados passam a ser tratados fora do território nacional)

A partir da execução deste change, os dados pessoais tratados pelo SETES.DOCS
(servidores, interessados e cidadãos que utilizam a consulta pública) passam a ser
processados em infraestrutura localizada em `us-central1` (Estados Unidos), e não
mais em território brasileiro.

O Requisito Não Funcional de Conformidade Legal do PRD (`docs/PRD.md`, seção 6) é
atualizado para refletir essa realidade — ver também tarefa 6.2 do change. As
garantias de proteção de dados (controle de acesso, anonimização, retenção, purga)
permanecem inalteradas; o que muda é exclusivamente a localização física do
processamento.
