// Dados compartilhados entre os fluxos críticos (task 12.x) — os 4 arquivos
// rodam em série (playwright.config.ts: fullyParallel=false, workers=1) e
// constroem estado uns sobre os outros: 01 inicializa o sistema com este
// Administrador; 02/03 criam e reaproveitam o mesmo Servidor; 04 reaproveita
// o Administrador para cadastrar unidade/tipo de processo e uma Gestora.

export const ADMIN_ROOT = {
  nome: "Admin Root",
  email: "admin.root@example.com",
  senha: "SenhaForte1",
};

export const UNIDADE_INICIAL = {
  nome: "Secretaria Geral",
  sigla: "SEGE",
};

export const NOVO_SERVIDOR = {
  nome: "Servidor Novo",
  email: "servidor.novo@example.com",
  senha: "SenhaServidor1",
};
