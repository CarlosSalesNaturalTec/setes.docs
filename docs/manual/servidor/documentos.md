# Anexar, consultar e remover documentos

Na aba **Documentos** do processo:

- **Anexar:** o botão **"Anexar Documento"** aceita **PDF, DOC, DOCX, JPG ou
  PNG**, com até **20 MB** por arquivo. Arquivos vazios, em outros formatos ou
  com conteúdo incompatível com a extensão são recusados. Se você anexar um
  arquivo com nome repetido, o sistema o renomeia automaticamente (ex.:
  "parecer (1).pdf") — nada é sobrescrito.
- **Visualizar:** clicar no nome do documento abre **PDF e imagens** em uma
  janela dentro do sistema. **DOC e DOCX** não têm visualização embutida: o
  sistema avisa e inicia o download automaticamente.
- **Baixar:** o botão **"Baixar"** salva o arquivo no seu computador.
- **Remover:** um documento pode ser removido **apenas enquanto o processo
  ainda está com a sua unidade e não foi enviado** (processo recém-criado ou
  recém-devolvido). Depois do envio, o botão de remoção não aparece. A remoção
  pede confirmação, fica registrada no histórico do processo (com autor e
  data/hora) e o arquivo é preservado por **30 dias** — nesse período, o
  Administrador consegue [restaurá-lo](../administrador/documentos-removidos.md)
  se a remoção tiver sido um engano.
- **Documentos gerados a partir de modelo:** o PDF gerado ao
  [abrir um processo com um modelo](modelo-documento.md) aparece na mesma
  lista dos anexos enviados por upload, com os mesmos controles de
  visualização, download, remoção, retenção e restauração — não há distinção
  nenhuma no tratamento.

## Verificar a assinatura digital de um PDF

Quando um documento chega **já assinado digitalmente** — por exemplo, um
contrato que o fornecedor assinou e enviou —, você pode conferir a assinatura
dentro do próprio processo, sem sair do sistema.

1. Na aba **Documentos**, localize o PDF e clique em **"Verificar Assinatura"**.
   O botão aparece **só em arquivos PDF**; DOC, DOCX, JPG e PNG não têm
   assinatura verificável aqui.
2. Aguarde a mensagem "Verificando assinatura…". A conferência consulta a
   situação do certificado junto à autoridade certificadora e pode levar alguns
   segundos.
3. O resultado aparece logo abaixo do documento, uma linha por assinatura, com
   **nome do signatário, CPF, autoridade certificadora e data/hora**. Clique em
   **"Fechar"** para recolher — nada fica guardado.

Qualquer pessoa que consiga abrir o documento no processo consegue verificá-lo
(incluindo quem tem permissão de auditoria). A consulta pública **não** mostra
documentos nem assinaturas.

### O que cada resultado significa

| Resultado | O que quer dizer |
|---|---|
| ✔ **Assinatura válida — documento íntegro** | O arquivo não mudou desde a assinatura, o certificado é da **ICP-Brasil** e não está revogado. |
| ✔ **… Certificado expirado em [data], mas válido na data da assinatura** | O certificado já venceu, mas um **carimbo de tempo** comprova que a assinatura foi feita antes do vencimento. |
| ✖ **Assinatura INVÁLIDA** | O arquivo foi **alterado depois de assinado**, ou o certificado foi **revogado**. Não confie no conteúdo sem confirmar com quem enviou. |
| ? **Verificação inconclusiva** | O sistema **não conseguiu confirmar** a situação do certificado agora (o serviço da autoridade certificadora não respondeu), ou o certificado venceu e o documento **não tem carimbo de tempo** que prove quando foi assinado. Não é o mesmo que inválida: tente de novo mais tarde ou use o verificador oficial. |
| ⚠ **Assinatura íntegra, mas o certificado não pertence à ICP-Brasil** | O arquivo não foi alterado, mas o certificado é de outra cadeia — o caso mais comum é a **assinatura gov.br**, que é uma assinatura eletrônica *avançada*, não *qualificada*. |
| ⚠ **Assinatura válida, mas o documento recebeu alterações depois de assinado** | A assinatura confere, mas alguém acrescentou algo ao PDF depois dela (uma anotação, um campo, uma página). O que veio depois **não** está coberto pela assinatura. |
| **Este documento não contém assinatura digital.** | O PDF não tem nenhuma assinatura. |
| **Não foi possível ler as assinaturas deste documento.** | O arquivo está corrompido ou protegido por senha. |

Quando o PDF tem **mais de uma assinatura**, cada uma aparece com seu próprio
resultado, e o topo mostra o **resumo do documento** — o resultado mais grave
entre elas.

A data/hora vem marcada como **"comprovada por carimbo de tempo"** quando o
documento tem carimbo de uma Autoridade de Carimbo do Tempo, ou como
**"declarada pelo signatário"** quando não tem — nesse caso é a data que o
próprio computador de quem assinou informou, sem prova independente.

### Veredito oficial

A conferência do Despapelize verifica a integridade do arquivo, a cadeia do
certificado e a revogação, mas **não substitui o verificador oficial** do
Instituto Nacional de Tecnologia da Informação (ITI). Para um parecer formal,
baixe o PDF com **"Baixar"** e envie-o ao
[Verificador de Conformidade do ITI](https://validar.iti.gov.br) — o link
também aparece em todo resultado. O Despapelize nunca envia o seu documento ao
ITI: quem envia é você.
