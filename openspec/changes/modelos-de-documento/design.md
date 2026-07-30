## Context

`Documento` é hoje **estritamente um arquivo no Cloud Storage**:

```python
objeto_chave    String(500)  NOT NULL  UNIQUE   # chave opaca no bucket
tipo_conteudo   String(100)  NOT NULL           # MIME canônico
tamanho_bytes   BigInteger   NOT NULL           # CHECK > 0
hash_sha256     String(64)   NOT NULL
```

`services/documento.py::anexar` valida extensão contra a whitelist
**PDF/DOC/DOCX/JPG/PNG**, confirma o MIME por *sniffing* da assinatura binária
(proteção deliberada contra MIME falsificado, `gestao-documental` design.md
Riscos), grava no bucket e insere a linha. A purga apaga o objeto do bucket.

Não existe "documento de texto no banco" — e criar um seria abrir uma segunda
classe de documento com regras próprias de download, retenção e purga.

Fatos que enquadram o design:

- A whitelist e o *sniffing* são um **controle de segurança**, não uma
  formalidade. Aceitar HTML como formato de documento exigiria enfraquecê-lo.
- `hash_sha256` já existe em `Documento` — é exatamente o que a assinatura
  digital da Fase 2 (Épico 4) precisa. Um documento gerado que seja um arquivo
  real entra nesse caminho sem retrabalho.
- `Content-Disposition` já é exposto pelo CORS (D5 do change de sessão), então o
  download do documento gerado funciona sem nenhuma mudança de infraestrutura.
- Anexos já são imutáveis com soft-delete reversível pelo Administrador —
  há um caminho de correção pronto, sem precisar de versionamento.

## Goals / Non-Goals

**Goals:**

- Catálogo de modelos com CRUD do Administrador e desativação sem exclusão.
- Editor de texto com o subconjunto de formatação pedido pelo cliente.
- Geração do documento preenchido como **anexo real** do processo.
- Proveniência do modelo registrada no documento gerado.

**Non-Goals:**

- **Nenhum placeholder estruturado** (`{{nome}}`), parser de variáveis ou
  formulário dinâmico — decisão do cliente: as lacunas são preenchidas à mão.
- Nenhum versionamento de documento. Corrigir = remover e gerar de novo.
- Nenhum enfraquecimento da whitelist de formatos ou do *sniffing* de MIME.
- Nenhuma mudança em tramitação, quadro, dashboard, notificações ou LGPD além do
  que os anexos já preveem.
- Sem edição colaborativa, sem rascunho compartilhado, sem assinatura (Fase 2).

## Decisions

### D1 — Modelo preenchido vira **PDF**, não HTML no banco

O texto editado é renderizado em PDF no backend e entregue ao pipeline de anexos
existente:

```
Editor (front)                 backend
   HTML restrito  ──▶  sanitiza  ──▶  render PDF  ──▶  documento.anexar()
   b/i/u, align,       (whitelist       (fpdf2)          │
   listas, p, br        de tags)                          ▼
                                            ┌─────────────┴──────────────┐
                                            ▼      ▼        ▼        ▼   ▼
                                       objeto  hash_    soft-   purga  download
                                       no GCS  sha256   delete
```

Três motivos, em ordem de peso:

1. **Não enfraquece a segurança.** PDF já está na whitelist e passa no
   *sniffing* (`%PDF` na assinatura). Aceitar HTML como documento exigiria
   admitir um formato executável no navegador no acervo — regressão do controle
   anti-spoofing existente.
2. **Prepara a Fase 2.** A assinatura ICP-Brasil assina bytes de arquivo
   (PAdES, sobre PDF). `hash_sha256` já está lá.
3. **Zero encanamento novo.** Download, `Content-Disposition`, retenção, purga e
   soft-delete funcionam sem uma linha de código adicional.

Alternativa rejeitada: coluna `conteudo` em `Documento` com `objeto_chave`
nullable. Criaria duas classes de documento e obrigaria a tratar o caso "sem
arquivo" em download, purga, hash e futura assinatura.

### D2 — `fpdf2` como renderizador

Python puro, sem dependências de sistema. Seu subconjunto de HTML
(`write_html`) cobre **exatamente** o que o cliente pediu — negrito, itálico,
sublinhado, alinhamento, listas — sem inchar a imagem do Cloud Run.

Alternativa rejeitada: WeasyPrint. Fidelidade tipográfica superior, mas exige
cairo/pango/gdk-pixbuf na imagem, aumentando tempo de build e superfície de
vulnerabilidade para um ganho que o caso de uso não pede.

### D3 — Sanitização por whitelist de tags, antes de renderizar

O HTML recebido é filtrado contra uma whitelist estrita — `p`, `br`, `b`,
`strong`, `i`, `em`, `u`, `ul`, `ol`, `li` e o atributo `align` — descartando
qualquer outra tag ou atributo, silenciosamente. Aplicada **no backend**, na
gravação do modelo e na geração do documento; a restrição do editor no front é
conveniência de UI, nunca a fronteira de segurança.

Mesmo com o PDF sendo o artefato final, a sanitização é necessária: o conteúdo do
modelo é devolvido ao editor de outros usuários, e um modelo com script
injetado seria XSS armazenado atingindo todo servidor que o abrisse.

### D4 — Lacunas são convenção visual, não estrutura

O modelo escreve lacunas como texto (`____________`, `[NOME DO SOLICITANTE]`) e
o servidor as substitui digitando. Não há parser, não há campos, não há
validação de preenchimento — decisão do cliente.

Consequência aceita e registrada: o sistema **não** garante que todas as lacunas
foram preenchidas; um documento pode ser gerado com `[NOME DO SOLICITANTE]`
literal. Mitigação de produto: o editor destaca visualmente o padrão de lacuna
enquanto ele existir no texto, como lembrete — sem bloquear.

### D5 — Documento gerado é imutável, como qualquer anexo

Nenhum caminho de edição pós-geração. Corrigir = remover (soft-delete, já
reversível pelo Administrador dentro da retenção) e gerar novamente. Isso evita
introduzir versionamento e mantém a regra "anexo é imutável" uniforme no acervo.

A regra existente de bloqueio de remoção após a saída do processo da unidade
(`gestao-documental`) aplica-se igualmente aos gerados — nenhuma exceção.

### D6 — Proveniência: `documento.modelo_id`

FK nullable para `modelo_documento`: preenchida nos gerados, nula nos enviados
por upload. Permite auditar quais modelos estão em uso e impede a exclusão
física de um modelo já utilizado — modelos são **desativados**, nunca excluídos,
como unidades, setores e tipos de processo.

### D7 — Tipo do modelo como enum de domínio

`tipo_modelo_documento`: `requerimento`, `oficio`, `memorando`, `despacho`,
`parecer`, `nota_tecnica`, `relatorio`, `ata`, `contrato`, `outro` — exatamente
a lista do cliente. Enum, não texto livre, para sustentar filtro e agrupamento no
catálogo. `categoria` permanece **texto livre**, porque o cliente a especificou
como campo aberto de digitação.

### D8 — Migration `0026` (schema antes de endpoint)

Revision única: cria o enum `tipo_modelo_documento`, cria `modelo_documento` e
adiciona `documento.modelo_id` (FK nullable). `down_revision` = a última revision
vigente quando este change for implementado — como ele é independente dos demais,
a numeração é ajustada na implementação conforme a ordem real de merge, mantendo
a cadeia sequencial legível.

### Fluxo principal

```
Servidor                web (/processos/novo)              api
   │ escolhe tipo/assunto     │                             │
   │ marca "usar modelo"      │                             │
   │──────────────────────────▶ GET /modelos?ativo=true     │
   │                          │─────────────────────────────▶
   │ escolhe "Requerimento    │◀───────────────────────────── catálogo
   │  padrão"                 │                             │
   │──────────────────────────▶ GET /modelos/{id}           │
   │                          │◀───────────────────────────── conteúdo sanitizado
   │ editor carrega o texto   │                             │
   │ substitui as lacunas     │  (edição só no cliente)     │
   │ salva o processo         │                             │
   │──────────────────────────▶ POST /processos             │
   │                          │◀───────────────────────────── 201 processo
   │                          │─────────────────────────────▶ POST /processos/{id}
   │                          │    { modelo_id, conteudo }    /documentos/gerar
   │                          │                             │
   │                          │   D3: sanitiza HTML          │
   │                          │   D2: fpdf2 → bytes PDF      │
   │                          │   D1: documento.anexar(bytes)│
   │                          │        → whitelist ok (PDF)  │
   │                          │        → sniffing ok (%PDF)  │
   │                          │        → objeto no bucket    │
   │                          │        → hash_sha256          │
   │                          │   D6: modelo_id gravado      │
   │                          │◀───────────────────────────── 201 documento
   │ vê o PDF na lista de     │                             │
   │  anexos do processo      │                             │
```

## Risks / Trade-offs

- [Documento pode ser gerado com lacunas não preenchidas] → aceito por decisão do
  cliente (D4); o editor destaca visualmente as lacunas remanescentes como
  lembrete, sem bloquear a geração. Registrado como comportamento esperado, não
  como defeito.
- [Fidelidade tipográfica do `fpdf2` é inferior à de um motor HTML completo] →
  aceito: o caso de uso é documento administrativo de texto corrido com
  formatação simples, não diagramação. Se a exigência mudar, a troca do
  renderizador é local a uma função.
- [Conteúdo de modelo é XSS armazenado em potencial] → sanitização por whitelist
  no **backend** (D3), aplicada na gravação e na geração; a restrição do editor
  no front é conveniência, não fronteira.
- [Administrador pode cadastrar dados pessoais reais dentro de um modelo] → o
  modelo é catálogo, não processo: a spec exige que contenha apenas marcações de
  lacuna, e a tela adverte. Não há como impedir tecnicamente digitação de texto,
  mas o risco fica registrado e orientado.
- [Documento imutável frustra quem quer corrigir um erro de digitação] →
  caminho existente e reversível: remover (soft-delete) e gerar de novo, dentro
  da janela de retenção. Preferido a introduzir versionamento por um caso de uso
  que o cliente não pediu.
- [Nova dependência de runtime no backend] → `fpdf2` é Python puro, sem
  bibliotecas de sistema; impacto na imagem do Cloud Run é desprezível e não há
  alteração de infraestrutura.
- [Numeração da migration pode conflitar com os outros changes em paralelo] →
  este change é independente; a revision é numerada na implementação conforme a
  ordem real de merge (D8), preservando a cadeia sequencial.
