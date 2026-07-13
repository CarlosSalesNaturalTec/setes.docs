import { chromium } from "playwright-core";

const browser = await chromium.launch({
  executablePath: "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
});
const page = await browser.newPage();
page.on("console", (msg) => {
  if (msg.type() === "error") console.log("[console:error]", msg.text());
});
page.on("pageerror", (err) => console.log("[pageerror]", err.message));

// 1) Setup
await page.goto("http://127.0.0.1:3000/setup");
await page.waitForSelector("h1");
await page.fill("#nome", "Admin Root");
await page.fill("#email", "admin@setes.docs");
await page.fill("#senha", "SenhaForte1");
await page.fill("#confirmar-senha", "SenhaForte1");
await page.fill("#unidade-nome", "Coordenação Financeira");
await page.fill("#unidade-sigla", "COFIN");
await page.click('button[type="submit"]');
await page.waitForURL("**/login**", { timeout: 30000 });
await page.screenshot({ path: "manual-shot-01-login-apos-setup.png" });

// 2) Login
await page.fill("#email", "admin@setes.docs");
await page.fill("#senha", "SenhaForte1");
await page.click('button[type="submit"]');
await page.waitForURL("**/perfil**", { timeout: 30000 });
await page.waitForTimeout(500);
await page.screenshot({ path: "manual-shot-02-perfil.png", fullPage: true });

// 3) Admin > Unidades
await page.click('a[href="/admin/unidades"]');
await page.waitForURL("**/admin/unidades**");
await page.waitForSelector("td:has-text('COFIN')", { timeout: 10000 });
await page.screenshot({ path: "manual-shot-03-admin-unidades.png", fullPage: true });

// 4) Cadastrar segunda unidade
await page.fill("#nome", "Assessoria Jurídica");
await page.fill("#sigla", "AJUR");
await page.click('button:has-text("Cadastrar unidade")');
await page.waitForSelector("td:has-text('AJUR')", { timeout: 10000 });
await page.screenshot({ path: "manual-shot-04-unidades-duas.png", fullPage: true });

// 5) Admin > Tipos de processo
await page.click('a[href="/admin/tipos-processo"]');
await page.waitForURL("**/admin/tipos-processo**");
await page.waitForSelector("#unidade-etapa");
await page.waitForFunction(() => document.querySelectorAll("#unidade-etapa option").length > 2);
await page.fill("#nome-tipo", "Licitação");
await page.selectOption("#unidade-etapa", { label: "Coordenação Financeira" });
await page.click('button:has-text("Adicionar etapa")');
await page.selectOption("#unidade-etapa", { label: "Assessoria Jurídica" });
await page.click('button:has-text("Adicionar etapa")');
await page.screenshot({ path: "manual-shot-05-roteiro-antes-salvar.png", fullPage: true });
await page.click('button:has-text("Cadastrar tipo de processo")');
await page.waitForSelector("li h2:has-text('Licitação')", { timeout: 10000 });
await page.screenshot({ path: "manual-shot-06-tipos-processo.png", fullPage: true });

// 6) Admin > Usuários — cadastra um servidor
await page.click('a[href="/admin/usuarios"]');
await page.waitForURL("**/admin/usuarios**");
await page.waitForFunction(() => document.querySelectorAll("#unidade option").length > 1);
await page.fill("#nome", "Servidor Teste");
await page.fill("#email", "servidor@setes.docs");
await page.selectOption("#unidade", { label: "Coordenação Financeira" });
await page.click('button:has-text("Cadastrar usuário")');
await page.waitForSelector("text=e-mail de primeiro acesso foi enviado", { timeout: 30000 });
await page.waitForSelector("td:has-text('Servidor Teste')", { timeout: 10000 });
await page.screenshot({ path: "manual-shot-07-usuarios.png", fullPage: true });

await browser.close();
console.log("ok");
