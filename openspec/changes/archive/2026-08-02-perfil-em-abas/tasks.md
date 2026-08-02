## 1. Frontend — componente de abas (design D4)

- [x] 1.1 Componente de abas reutilizável em `components/`, com `role="tablist"`, `role="tab"` (`aria-selected`, `aria-controls`) e `role="tabpanel"` (`aria-labelledby`); navegação por setas esquerda/direita e ativação por Enter/Espaço; cada aba é um `<button>`, não um link. Aceite: navegável inteiramente por teclado, sem armadilha de foco.
- [x] 1.2 Estilizar o componente com os tokens visuais já em uso no projeto, incluindo estado de foco visível. Aceite: consistente com o restante da interface.

## 2. Frontend — tela Meu Perfil (design D1, D2, D3)

- [x] 2.1 `app/perfil/page.tsx`: reorganizar o conteúdo existente em quatro abas — "Meu perfil", "Trocar senha", "Processos em que atuei" e "Documentos assinados" — preservando integralmente o que já é renderizado hoje. Aceite: nenhum conteúdo existente é perdido nem alterado em comportamento.
- [x] 2.2 Aba "Meu perfil": exibir nome, e-mail, perfil, unidade, setor, cargo, telefone e chefia direta, mantendo a edição do próprio nome sem alteração de regra; omitir campos vazios em vez de exibir valores nulos. Aceite: edição do nome continua funcionando exatamente como antes.
- [x] 2.3 Aba "Trocar senha": montar o `TrocarSenhaForm` existente sem refatoração. Aceite: fluxo de troca de senha inalterado.
- [x] 2.4 Aba "Documentos assinados": placeholder com mensagem informando que a assinatura digital será disponibilizada em fase futura; **nenhum** botão "Assinar", campo de certificado ou elemento que sugira funcionalidade disponível (D3). Aceite: nada na aba sugere que a assinatura já existe.
- [x] 2.5 Aba ativa refletida na query string (`?aba=perfil|senha|processos|assinados`), restaurada na recarga e endereçável por link; valor ausente ou inválido cai no padrão `perfil` (D1). Aceite: recarregar mantém a aba; link direto abre a aba correta.
- [x] 2.6 Confirmar que a troca de aba **não** dispara nova chamada à API (D2). Aceite: uma única requisição ao endpoint de "Meu Perfil" por carga de página.
- [x] 2.7 Testes Vitest: renderização das quatro abas; troca de aba atualiza a query string; recarga com `?aba=processos` abre a aba correta; valor inválido cai no padrão; navegação por teclado entre abas; ausência de chamada extra à API ao trocar de aba; aba de assinados exibe o placeholder e nenhum controle de assinatura.

## 3. Documentação mestre

- [x] 3.1 `docs/PRD.md` US 1.5: registrar a organização da tela "Meu Perfil" em quatro abas, mantendo explícito que "Documentos assinados" é placeholder da Fase 2 (Épico 4). Aceite: PRD sem contradição com as specs deste change nem com `openspec/config.yaml`.
- [x] 3.2 `docs/manual-usuario.md`: seção de "Meu Perfil" atualizada com a navegação por abas. Aceite: descrições coerentes com a UI final.
