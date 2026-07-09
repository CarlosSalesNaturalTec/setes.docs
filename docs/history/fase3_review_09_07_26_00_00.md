# Relatório de Revisão de PRD — Controle de Qualidade

<auditoria_interna>

## Análise Crítica — Chain of Thought

### 1. Critérios de Aceitação (BDD)

**Pontos Positivos:**
- Todas as 38 User Stories possuem formato Dado/Quando/Então bem estruturado.
- Cobertura de caminhos tristes é excepcional: a maioria das US tem cenários de erro, validação e borda (e-mail duplicado, senha incorreta, acesso negado, unidade inexistente, link expirado, devolução, etc.).
- US 1.3 destaca-se por cobrir: login válido, bloqueio após 3 tentativas, tentativa durante bloqueio, recuperação de senha, desbloqueio após timeout, e e-mail não cadastrado na recuperação.
- US 2.1 cobre CPF inválido, CNPJ inválido e tipo de processo sem roteiro — pensamento de borda robusto.
- US 5.1 cobre corretamente a diferença entre notificações lidas vs. não lidas e regras de expurgo — excelente nível de detalhe.
- A premissa de contingência do Épico 4 (Assinatura Digital) demonstra maturidade de produto.

**Vulnerabilidades encontradas:**
1. **US 1.3 — Ausência de cenário "Recuperação de senha durante bloqueio temporário":** O que acontece se o usuário tiver sua conta bloqueada por 30 min e solicitar recuperação de senha nesse período? Ele recebe o link? Pode redefinir? A senha redefinida desbloqueia a conta?
2. **US 3.1 Cenário 4b — Lacuna sobre documentos anexados pós-devolução:** O cenário cobre exclusão de documentos anexados "antes do despacho original", mas não especifica se documentos anexados APÓS a devolução podem ser excluídos e em quais condições.
3. **US 2.6 — Inconsistência de perfil:** A US diz que "Servidor ou Gestor" podem marcar/desmarcar sigilo, mas omite o Administrador. Por RF 6, o Administrador tem "acesso irrestrito a todos os processos". A omissão gera dúvida: o Admin pode ou não gerenciar sigilo? Se pode, por que não está na US?
4. **US 1.7 — Ausência de histórico de senhas:** O sistema impede reuso da senha ATUAL (Cenário 3), mas não impede alternância entre duas senhas (ex.: alternar entre "Senha@123" e "Senha@456"). Para um sistema de governo, histórico de N senhas anteriores é esperado.
5. **US 2.5 Cenário 2 — Redação confusa:** O cenário testa não-retroatividade, mas a redação usa "apenas os processos que completaram 30 dias" quando nenhum dos 10 processos citados no "Dado" (concluídos há 25 dias) atingiu 30 dias — o resultado implícito é que NENHUM é arquivado, mas o texto omite essa conclusão explícita.

### 2. Coesão de Escopo

**Verificação RF ↔ US:** Todos os 38 Requisitos Funcionais mapeiam para ao menos uma User Story. Não foram encontrados RFs órfãos.

**Verificação US ↔ RF:** Todas as US têm lastro nos RFs. A rastreabilidade é bidirecional e completa.

**Ponto de atenção:** O Épico 9 (Auditoria e Relatórios Avançados) e o Épico 10 (Conformidade LGPD) adicionam complexidade significativa ao MVP. Embora LGPD seja inegociável para sistemas de governo, os relatórios de auditoria (US 9.2) com exportação PDF beiram o escopo de "Relatórios avançados com exportação em múltiplos formatos" listado como Fora de Escopo. Há uma tensão: o Fora de Escopo cita "Relatórios avançados com exportação em múltiplos formatos — o MVP terá dashboard visual e consulta em tela", mas a US 9.2 adiciona exportação PDF. Isso é uma inconsistência interna.

### 3. Blindagem Tecnológica

**Avaliação:** O PRD é disciplinado em evitar decisões de arquitetura.

- Nenhuma menção a banco de dados, linguagem de programação, framework ou ORM.
- "Web PKI" na US 4.1 é um padrão de browser, não uma escolha de framework — aceitável.
- "Hash criptográfico" e "HTTPS" nos RNFs de Segurança são requisitos de conformidade, não escolhas de implementação.
- O formato "AAAA/NNNNNN" para número de processo é especificação funcional legítima.

**Única ressalva menor:** A US 5.2 Cenário 1 menciona "link direto para acessá-lo" no e-mail — isso pressupõe URL pública para o sistema, o que é inevitável para um sistema web, mas poderia ser formulado como "acesso ao sistema" em vez de "link direto".

### 4. Cálculo do Score

**Pontos fortes (puxam a nota para cima):**
- Estrutura BDD impecável com cobertura de caminhos tristes (+2.0)
- Rastreabilidade completa RF ↔ US (+1.5)
- Blindagem tecnológica exemplar (+1.5)
- Premissa de contingência do Épico 4 (+0.5)
- Escopo de MVP bem delimitado (+1.0)
- Cobertura LGPD abrangente (+0.5)

**Pontos fracos (puxam a nota para baixo):**
- Inconsistência US 2.6 vs. RF 6 (Admin e sigilo) (-0.5)
- Lacuna de cenário "recuperação de senha durante bloqueio" (-0.3)
- Inconsistência entre Fora de Escopo e US 9.2 (exportação PDF) (-0.3)
- Ausência de histórico de senhas na US 1.7 (-0.2)
- Redação confusa na US 2.5 Cenário 2 (-0.1)
- Lacuna sobre documentos pós-devolução na US 3.1 (-0.1)

**Base inicial: 9.0**
**Penalidades: -0.5 -0.3 -0.3 -0.2 -0.1 -0.1 = -1.5**
**Score Final: 7.5**

Arredondando para escala de 0.5: **7.5**

O score abaixo de 8 se deve principalmente a três fatores: (1) a inconsistência entre o perfil Admin e a gestão de sigilo (US 2.6) pode gerar bugs de autorização em produção; (2) a contradição entre o Fora de Escopo (sem exportação) e a US 9.2 (exportação PDF) cria ambiguidade de escopo que a engenharia não consegue resolver sozinha; (3) a omissão de histórico de senhas para um sistema de governo é uma lacuna de segurança que deveria ser capturada na fase de produto.

</auditoria_interna>

---

## 1. Veredito e Score de Prontidão

* **Score de Prontidão:** 7.5/10
* **Status:** REQUER REFATORAÇÃO (Score < 8)
* **Resumo:** O PRD demonstra excelente estrutura BDD, cobertura abrangente de caminhos tristes e rastreabilidade completa entre RFs e US. A blindagem tecnológica é exemplar — zero vazamentos de arquitetura. No entanto, três problemas impedem a aprovação imediata: (1) inconsistência de autorização entre a US 2.6 (sigilo restrito a Servidor/Gestor) e o RF 6 (Admin com acesso irrestrito), que pode gerar bugs de autorização; (2) contradição de escopo entre o item "Fora de Escopo" (sem exportação de relatórios) e a US 9.2 (exportação PDF); (3) ausência de política de histórico de senhas para um sistema de governo. Estas correções são pontuais e de baixo esforço — estima-se que o documento possa atingir score 8.5+ após uma rodada de ajustes.

---

## 2. Pontos Críticos Identificados

* **Crítica 1 — Inconsistência de autorização (US 2.6 × RF 6):** A US 2.6 especifica que apenas "Servidor ou Gestor da unidade atual" podem marcar/desmarcar sigilo. O RF 6 estabelece que "Administradores têm acesso irrestrito a todos os processos, unidades e configurações do sistema". A engenharia não saberá se o Administrador pode ou não gerenciar sigilo de processos. Se implementar conforme a US (sem Admin), o RF 6 é violado. Se implementar conforme o RF 6 (com Admin), a US fica incompleta.

* **Crítica 2 — Contradição de escopo (Fora de Escopo × US 9.2):** O item "Fora de Escopo" lista "Relatórios avançados com exportação em múltiplos formatos — o MVP terá dashboard visual e consulta em tela". Porém, a US 9.2 Cenário 1 especifica "opção de exportação em formato PDF ao clicar no botão 'Exportar PDF'". A engenharia não consegue resolver sozinha se exportação PDF está dentro ou fora do MVP. Se exportação PDF estiver fora, a US 9.2 inteira pode ser postergada — mas a US 9.1 (visualização de processos pelo Auditor) parece essencial e independente.

* **Crítica 3 — Ausência de política de histórico de senhas (US 1.7):** A US 1.7 Cenário 3 impede reuso da senha ATUAL, mas não impede que o usuário alterne entre duas senhas (ex.: "Senha@123" → "Senha@456" → "Senha@123"). Para um sistema de governo com exigências de segurança, é esperado um histórico de N senhas anteriores (tipicamente 6 a 12). Esta lacuna será apontada em auditoria de segurança e gerará retrabalho.

* **Crítica 4 — Lacuna: recuperação de senha durante bloqueio (US 1.3):** A US 1.3 define o fluxo de bloqueio (Cenário 2 e 2b) e o fluxo de recuperação de senha (Cenário 3), mas não especifica a interação entre eles. Perguntas não respondidas: um usuário com conta bloqueada pode solicitar recuperação de senha? Se receber o link e redefinir a senha, a conta é desbloqueada antes dos 30 minutos? Ou o bloqueio permanece independente da redefinição?

* **Crítica 5 — Redação confusa em cenário de não-retroatividade (US 2.5 Cenário 2):** O "Dado" estabelece 10 processos concluídos há 25 dias. O "Então" diz "apenas os processos que completaram 30 dias [...] são arquivados". Como nenhum dos 10 processos completou 30 dias (estão em 25), o resultado real é "nenhum processo é arquivado", mas o texto não declara isso explicitamente, deixando margem para interpretação ambígua.

* **Crítica 6 — Lacuna sobre exclusão de documentos pós-devolução (US 3.1 Cenário 4b):** O cenário cobre exclusão de documentos anexados "antes do despacho original". Não especifica se documentos anexados APÓS a devolução do processo (durante a correção) podem ser excluídos e em quais condições.

---

## 3. Propostas de Correção Direta

### Correção 1: Inconsistência de autorização Admin × Sigilo (US 2.6)

* **Como está no PRD original:** 
  > * **US 2.6:** Como Servidor ou Gestor, eu quero marcar um processo como sigiloso para restringir sua visibilidade na consulta pública.
  >   * *Cenário 1: Marcação de processo como sigiloso*
  >     * **Dado** que estou autenticado como Servidor ou Gestor da unidade atual do processo

* **Como deve ficar (Sugestão de Reescrita):**
  > * **US 2.6:** Como Servidor, Gestor ou Administrador, eu quero marcar um processo como sigiloso para restringir sua visibilidade na consulta pública.
  >   * *Cenário 1: Marcação de processo como sigiloso*
  >     * **Dado** que estou autenticado como Servidor ou Gestor da unidade atual do processo, ou como Administrador do sistema
  >   
  >   * **(ADICIONAR) Cenário 1b: Marcação de sigilo por Administrador em processo de qualquer unidade**
  >     * **Dado** que estou autenticado como Administrador
  >     * **Quando** acesso um processo de qualquer unidade e aciono "Marcar como Sigiloso" ou "Remover Sigilo"
  >     * **Então** a operação é concluída com sucesso, independentemente da unidade em que o processo se encontra, e a ação é registrada no histórico de tramitação

### Correção 2: Contradição de escopo — Exportação de relatórios (Fora de Escopo e US 9.2)

* **Como está no PRD original (Fora de Escopo):** 
  > * Relatórios avançados com exportação em múltiplos formatos — o MVP terá dashboard visual e consulta em tela

* **Como deve ficar (Sugestão de Reescrita) — OPÇÃO A (manter exportação PDF no MVP):**
  > * Relatórios avançados com exportação em múltiplos formatos (Excel, CSV) — o MVP terá dashboard visual, consulta em tela e exportação em PDF para relatórios de auditoria

* **OU OPÇÃO B (postergar exportação PDF):**
  > Na US 9.2 Cenário 1, substituir o "Então" por:
  > * **Então** o sistema exibe em tela um relatório consolidado contendo: total de processos no período, tempo médio de tramitação, lista de processos com status atual e unidade atual. O relatório é visualizado na própria interface. A exportação em PDF estará disponível em versão futura.

* **Recomendação do Revisor:** OPÇÃO A. Relatório PDF de auditoria é requisito básico para órgãos públicos e a complexidade de implementação é baixa. Ajustar o Fora de Escopo para explicitar que "múltiplos formatos" refere-se a Excel, CSV e outros, não a PDF.

### Correção 3: Histórico de senhas (US 1.7)

* **Como está no PRD original (apenas Cenário 3):** 
  > * *Cenário 3: Nova senha igual à anterior*
  >   * **Dado** que estou autenticado no sistema
  >   * **Quando** informo uma nova senha idêntica à senha atual
  >   * **Então** o sistema rejeita a operação e exibe "A nova senha não pode ser igual à senha atual"

* **Como deve ficar (Sugestão de Reescrita):**
  > * *Cenário 3: Nova senha igual à anterior (histórico)*
  >   * **Dado** que estou autenticado no sistema
  >   * **Quando** informo uma nova senha idêntica à senha atual **ou a qualquer uma das últimas 6 senhas utilizadas**
  >   * **Então** o sistema rejeita a operação e exibe "A nova senha não pode ser igual à senha atual ou às 6 senhas anteriores"

### Correção 4: Recuperação de senha durante bloqueio (US 1.3)

* **Como está no PRD original:** Nenhum cenário cobre a interseção entre bloqueio e recuperação de senha.

* **Como deve ficar (Sugestão de Adição de Cenário):**
  > * **(ADICIONAR) Cenário 2c: Recuperação de senha durante bloqueio temporário**
  >   * **Dado** que minha conta está bloqueada temporariamente após 3 tentativas incorretas
  >   * **Quando** solicito recuperação de senha informando meu e-mail cadastrado
  >   * **Então** recebo o link de redefinição normalmente. Ao redefinir a senha com sucesso (seguindo os mesmos critérios do Cenário 3), a conta é automaticamente desbloqueada, o contador de tentativas é resetado para zero, e sou redirecionado à tela de login. Caso o link expire (2 horas) sem ser utilizado, a conta permanece bloqueada até o fim do período de 30 minutos.

### Correção 5: Clareza na US 2.5 Cenário 2 (não-retroatividade)

* **Como está no PRD original:** 
  > * **Então** apenas os processos que completaram 30 dias (prazo vigente no momento da conclusão de cada um) são arquivados; a alteração do prazo não se aplica retroativamente

* **Como deve ficar (Sugestão de Reescrita):**
  > * **Então** nenhum dos 10 processos é arquivado nesta execução, pois todos ainda estão dentro do prazo de 30 dias vigente no momento de suas conclusões. A alteração para 15 dias aplica-se apenas a processos concluídos a partir desta data, e não retroativamente aos processos já concluídos. Os 10 processos serão arquivados somente quando completarem 30 dias cada um.

### Correção 6: Lacuna de documentos pós-devolução (US 3.1)

* **Como está no PRD original (apenas Cenário 4b cobre pré-devolução):** 
  > * *Cenário 4b: Exclusão de documento após devolução do processo*
  >   * **Dado** que um processo da minha unidade foi despachado, devolvido pela unidade seguinte [...]
  >   * **Quando** aciono a opção "Remover" sobre um documento que havia sido anexado antes do despacho original

* **Como deve ficar (Sugestão de Reescrita — substituir Cenário 4b):**
  > * *Cenário 4b: Exclusão de documento após devolução do processo*
  >   * **Dado** que um processo da minha unidade foi despachado, devolvido pela unidade seguinte (US 2.2b) e agora está novamente na minha unidade
  >   * **Quando** aciono a opção "Remover" sobre um documento (independentemente de ter sido anexado antes do despacho original ou após a devolução)
  >   * **Então** o sistema exibe confirmação "Tem certeza que deseja remover este documento?" e, ao confirmar, o documento é removido da lista de anexos, o arquivo físico é excluído do armazenamento, e a exclusão é registrada no histórico do processo. Esta regra aplica-se a QUALQUER documento, tenha ele sido anexado antes do despacho original ou durante o período de correção pós-devolução. O processo permanece na unidade atual com o mesmo status ("Em Tramitação").
  >   * **(ADICIONAR) Cenário 4c: Tentativa de exclusão de documento após o processo ser despachado novamente pós-correção**
  >     * **Dado** que um processo foi devolvido para minha unidade, corrigi a pendência e despachei novamente para a unidade seguinte
  >     * **Quando** tento remover qualquer documento do processo
  >     * **Então** o sistema exibe "Não é possível remover documentos de um processo que já foi despachado" (mesma regra do Cenário 4)

---

## 4. Próximos Passos

1. **Aplicar as 6 correções listadas na Seção 3** — são ajustes pontuais, sem mudança de escopo ou arquitetura. Estima-se 30 minutos de edição.
2. **Rodar novamente a validação (Fase 3)** após as correções para reavaliar o Score de Prontidão. Espera-se que o documento atinja score ≥ 8.5.
3. **Esclarecer com o Product Owner** a decisão sobre exportação PDF (Correção 2) — se será mantida no MVP (Opção A recomendada) ou postergada (Opção B).
4. Após aprovação na reavaliação (Score 8+), o PRD estará apto para ser encaminhado à **Fase 4 (Patcher)** para refinamento final ou diretamente para o time de engenharia e ferramentas de SDD (OpenSpec).
