// Sanitização de HTML do modelo de documento — mesma whitelist do backend
// (change modelos-de-documento, design.md D3: `services/modelo_documento.py::
// sanitizar_html`). A fronteira de segurança real é o backend, que sanitiza
// de novo na gravação e na geração; esta cópia no cliente é conveniência de
// UI (garante que a barra do editor nunca produza tag fora da whitelist),
// nunca a garantia final.
const TAGS_PERMITIDAS = new Set(["P", "BR", "B", "STRONG", "I", "EM", "U", "UL", "OL", "LI"]);
const TAGS_CONTEUDO_PERIGOSO = new Set(["SCRIPT", "STYLE", "IFRAME", "OBJECT", "EMBED"]);
const ALINHAMENTOS_PERMITIDOS = new Set(["left", "center", "right", "justify"]);

function escaparTexto(texto: string): string {
  return texto.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function serializarNo(no: Node): string {
  if (no.nodeType === Node.TEXT_NODE) {
    return escaparTexto(no.textContent ?? "");
  }
  if (no.nodeType !== Node.ELEMENT_NODE) return "";

  const elemento = no as Element;
  const tag = elemento.tagName;
  const filhos = Array.from(elemento.childNodes).map(serializarNo).join("");

  if (TAGS_CONTEUDO_PERIGOSO.has(tag)) return "";
  if (!TAGS_PERMITIDAS.has(tag)) return filhos; // tag desconhecida: descarta só a marcação

  if (tag === "BR") return "<br>";

  const tagMinuscula = tag.toLowerCase();
  let atributos = "";
  if (tagMinuscula === "p") {
    const align = elemento.getAttribute("align");
    if (align && ALINHAMENTOS_PERMITIDOS.has(align)) atributos = ` align="${align}"`;
  }
  return `<${tagMinuscula}${atributos}>${filhos}</${tagMinuscula}>`;
}

export function sanitizarHtmlModelo(html: string): string {
  const documento = new DOMParser().parseFromString(`<body>${html}</body>`, "text/html");
  return Array.from(documento.body.childNodes).map(serializarNo).join("");
}

// Convenção visual de lacuna (D4): `[TEXTO ENTRE COLCHETES]` ou uma sequência
// de 3+ sublinhados — nunca bloqueia a geração, só sinaliza como lembrete.
const PADRAO_LACUNA = /\[[^[\]\n]{1,80}\]|_{3,}/g;

export function contarLacunas(html: string): number {
  const texto = html.replace(/<[^>]+>/g, " ");
  return (texto.match(PADRAO_LACUNA) ?? []).length;
}
