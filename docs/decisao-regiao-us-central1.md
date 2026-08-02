# Decisão de região: `us-central1`

> Referenciado pelo change `openspec/changes/migracao-regiao-us-central1/`
> (tarefa 6.4). Registra o racional de custo × latência × conformidade para que a
> escolha não dependa da memória de quem participou.

## Decisão

A infraestrutura do SETES.DOCS passa de `southamerica-east1` (Osasco/SP) para
`us-central1` (Iowa/EUA) como região única de todos os recursos regionais.

## Racional

- **Custo**: `us-central1` é sensivelmente mais barata que `southamerica-east1`
  para os mesmos recursos (Cloud Run, Cloud SQL, Cloud Storage, Secret Manager) —
  motivação original do pedido do cliente, registrada em
  `docs/Ajustes SETES DOCS.pdf`: *"diminuir custo final, pois está em South
  América, é mais rápido nas respostas, porém mais caro"*.
- **Latência**: o próprio cliente reconhece, na mesma frase, que
  `southamerica-east1` responde mais rápido para usuários no Brasil. O cliente foi
  informado desse trade-off antes de decidir e optou conscientemente pelo custo
  menor em detrimento da latência menor. Não há medição formal de RTT registrada —
  a decisão foi tomada com base no reconhecimento qualitativo do próprio cliente,
  não em benchmark.
- **Conformidade**: a região `southamerica-east1` foi escolhida originalmente
  (change `bootstrap-infraestrutura`) sob a premissa de que o cliente era um órgão
  da administração pública, exigindo residência de dados em território brasileiro.
  Essa premissa se mostrou incorreta — o cliente é uma instituição privada — o que
  torna a residência nacional uma escolha, não uma obrigação legal. A transferência
  internacional resultante da mudança para `us-central1` está documentada e
  fundamentada (LGPD, Art. 33) em
  `docs/lgpd-transferencia-internacional-us-central1.md`, incluindo autorização
  expressa do cliente (Ricardo Pita, Diretor, 30/07/2026).

## Por que reconstruir em vez de migrar

Os dados existentes no ambiente `southamerica-east1` eram exclusivamente dados de
teste — o sistema ainda estava em fase de avaliação, não em produção real. O
cliente autorizou o descarte integral (banco e bucket), o que eliminou a
necessidade de *dump/restore*, cópia de objetos entre buckets ou janela de
indisponibilidade: o ambiente foi destruído (`terraform destroy`) e reconstruído
do zero em `us-central1`, com o schema recriado pelas migrations Alembic
existentes. Ver `openspec/changes/migracao-regiao-us-central1/design.md` (D1, D2)
para o detalhamento técnico da ordem de execução.

## Rastreabilidade

| Registro | Local |
|---|---|
| Pedido original do cliente | `docs/Ajustes SETES DOCS.pdf` |
| Base legal e autorização (transferência + descarte) | `docs/lgpd-transferencia-internacional-us-central1.md` |
| RNF de conformidade legal atualizado | `docs/PRD.md`, seção 6 |
| Decisões técnicas de execução (D1–D6) | `openspec/changes/migracao-regiao-us-central1/design.md` |
