# Gate de conformidade manual — verificação de assinatura

> **Status: ⚠️ PENDENTE.** Tarefa 8.1 de `tasks.md`; estudo técnico §8, camada 3.
> Não automatizável: exige PDFs reais (com dados pessoais de terceiros, que **não**
> são commitados) e o Verificador de Conformidade do ITI, operado por uma pessoa.
> A implementação foi validada só contra a PKI descartável de
> `apps/api/scripts/pki_teste.py`, o que **prova o fluxo, não a conformidade
> ICP-Brasil**. Fazer este gate antes de divulgar a funcionalidade aos usuários.

## Procedimento

1. Reunir ao menos três PDFs reais:
   - **A** — assinado com e-CPF ICP-Brasil (A1 ou A3, qualquer AC credenciada);
   - **B** — assinado via gov.br (assinatura avançada);
   - **C** — ICP-Brasil **com carimbo de tempo** (PAdES-T ou superior), se disponível.
2. Anexar cada um a um processo de teste num ambiente com rede de saída liberada
   para as LCR/OCSP das ACs (local ou validação) e acionar "Verificar Assinatura".
   Anotar o veredito e o tempo até o resultado aparecer.
3. Enviar o mesmo arquivo a <https://validar.iti.gov.br> e anotar o veredito
   (Aprovado / Reprovado / Indeterminado).
4. Preencher a tabela. **Critério de aceite:** nenhum caso em que o Despapelize diga
   `valida` e o ITI diga Reprovado; toda divergência tem justificativa (ex.: o ITI
   reprova por política de assinatura, que a conferência local não avalia — D7).
5. Arquivar fora do repositório os comprovantes do ITI (PDF do relatório) — contêm
   dados pessoais.

## Resultado

| Arquivo | Veredito Despapelize | Veredito ITI | Tempo observado | Divergência / justificativa |
|---|---|---|---|---|
| A — e-CPF ICP-Brasil | ⬜ | ⬜ | ⬜ | ⬜ |
| B — gov.br | ⬜ (esperado: `fora_icp_brasil`) | ⬜ | ⬜ | ⬜ |
| C — ICP-Brasil + carimbo | ⬜ | ⬜ | ⬜ | ⬜ |

Executado por: ⬜ · Data: ⬜ · Ambiente: ⬜
