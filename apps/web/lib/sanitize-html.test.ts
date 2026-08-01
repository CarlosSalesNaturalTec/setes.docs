import { describe, expect, it } from "vitest";

import { contarLacunas, sanitizarHtmlModelo } from "./sanitize-html";

describe("sanitizarHtmlModelo", () => {
  it("preserva as tags da whitelist", () => {
    const html =
      '<p align="center"><b>Requerimento</b></p>' +
      "<p>Prezado <i>Fulano</i>, <u>bom dia</u>.</p>" +
      "<ul><li>Item um</li></ul><ol><li>Passo um</li></ol>" +
      "Texto solto<br>com quebra";

    const saida = sanitizarHtmlModelo(html);

    expect(saida).toContain('<p align="center"><b>Requerimento</b></p>');
    expect(saida).toContain("<i>Fulano</i>");
    expect(saida).toContain("<u>bom dia</u>");
    expect(saida).toContain("<ul><li>Item um</li></ul>");
    expect(saida).toContain("<ol><li>Passo um</li></ol>");
    expect(saida).toContain("<br>");
  });

  it("descarta script e seu conteúdo", () => {
    const saida = sanitizarHtmlModelo("<p>Antes</p><script>alert(1)</script><p>Depois</p>");

    expect(saida).not.toContain("<script");
    expect(saida).not.toContain("alert");
    expect(saida).toContain("<p>Antes</p>");
    expect(saida).toContain("<p>Depois</p>");
  });

  it("descarta atributos de evento e style", () => {
    const saida = sanitizarHtmlModelo('<p onclick="x()" style="color:red">Texto</p>');

    expect(saida).not.toContain("onclick");
    expect(saida).not.toContain("style");
    expect(saida).toBe("<p>Texto</p>");
  });

  it("desembrulha tags fora da whitelist mantendo o texto", () => {
    const saida = sanitizarHtmlModelo('<div class="x"><span>Texto dentro</span></div>');

    expect(saida).not.toContain("<div");
    expect(saida).not.toContain("<span");
    expect(saida).toContain("Texto dentro");
  });

  it("só aceita align com valor reconhecido", () => {
    const saida = sanitizarHtmlModelo('<p align="center">A</p><p align="javascript:x">B</p>');

    expect(saida).toContain('<p align="center">A</p>');
    expect(saida).not.toContain("javascript");
    expect(saida).toContain("<p>B</p>");
  });

  it("qualquer controle de formatação simulado nunca produz tag fora da whitelist", () => {
    const combinacoes = [
      '<div style="text-align:center"><b>x</b></div>',
      '<span style="font-weight:bold">x</span>',
      '<p class="ql-align-center">x</p>',
      '<b onmouseover="x()">x</b>',
    ];
    for (const html of combinacoes) {
      const saida = sanitizarHtmlModelo(html);
      const tagsEncontradas = [...saida.matchAll(/<([a-zA-Z0-9]+)/g)].map((m) => m[1].toLowerCase());
      const permitidas = new Set(["p", "br", "b", "strong", "i", "em", "u", "ul", "ol", "li"]);
      for (const tag of tagsEncontradas) {
        expect(permitidas.has(tag)).toBe(true);
      }
      expect(saida).not.toContain("style");
      expect(saida).not.toContain("onmouseover");
      expect(saida).not.toContain("class");
    }
  });
});

describe("contarLacunas", () => {
  it("conta marcações de lacuna sem bloquear nada", () => {
    expect(contarLacunas("<p>Nome: [NOME DO SOLICITANTE]</p>")).toBe(1);
    expect(contarLacunas("<p>Nome: ___________</p>")).toBe(1);
    expect(contarLacunas("<p>Nome: [A] CPF: [B]</p>")).toBe(2);
    expect(contarLacunas("<p>Sem lacunas aqui</p>")).toBe(0);
  });
});
