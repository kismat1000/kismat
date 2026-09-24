/*
 * COMP2004 Assessment — Log4Shell CVSS analysis and SIEM proposal.
 * Generates report/AStudent_COMP2004_Assignment2_2026.docx with docx-js.
 *
 * Figures are rendered separately (src/figures/render.js). Run order:
 *   node src/figures/render.js && NODE_PATH=$(npm root -g) node src/build_report.js
 */
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType, BorderStyle, ShadingType,
  ImageRun, PageBreak, Header, Footer, PageNumber, ExternalHyperlink,
  TableOfContents, LevelFormat, convertInchesToTwip,
} = require("docx");

const FIG = path.join(__dirname, "figures");
const OUT = path.join(__dirname, "..", "report", "KAcharya_COMP2004_Assignment2_2026.docx");

// ---- palette ----------------------------------------------------------
const INK = "1A1A19", ACCENT = "1C5CAB", ACCENT2 = "184F95", LIGHT = "EAF2FC",
      RULE = "C9C8C3", HEADSHADE = "1C5CAB", ZEBRA = "F2F6FC", CRIT = "B22222";

// ---- helpers ----------------------------------------------------------
const FONT = "Calibri"; // maps to Carlito/DejaVu at render time
function run(text, o = {}) { return new TextRun({ text, font: FONT, ...o }); }
function body(children, o = {}) {
  return new Paragraph({ spacing: { after: 140, line: 276 }, alignment: AlignmentType.JUSTIFIED, children, ...o });
}
function p(text, o = {}) { return body([run(text)], o); }
function bullet(text, level = 0, runs) {
  return new Paragraph({ numbering: { reference: "bullets", level }, spacing: { after: 70, line: 268 },
    children: runs || [run(text)] });
}
function num(text, runs) {
  return new Paragraph({ numbering: { reference: "steps", level: 0 }, spacing: { after: 80, line: 268 },
    children: runs || [run(text)] });
}
function h1(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { before: 300, after: 140 },
    children: [run(text, { bold: true, size: 30, color: ACCENT2 })] });
}
function h2(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 220, after: 100 },
    children: [run(text, { bold: true, size: 25, color: ACCENT })] });
}
function h3(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_3, spacing: { before: 170, after: 80 },
    children: [run(text, { bold: true, size: 22, color: INK })] });
}
function mono(text, o = {}) { return new TextRun({ text, font: "Consolas", size: 18, ...o }); }
function figure(file, w, h, caption) {
  const img = new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120, after: 40 },
    children: [ new ImageRun({ type: "png", data: fs.readFileSync(path.join(FIG, file)), transformation: { width: w, height: h } }) ] });
  const cap = new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 },
    children: [run(caption, { italics: true, size: 18, color: "52514E" })] });
  return [img, cap];
}
// simple bordered box (quote / callout)
function callout(children) {
  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE }, columnWidths: [9360],
    borders: { top: {style:BorderStyle.SINGLE,size:2,color:ACCENT}, bottom:{style:BorderStyle.SINGLE,size:2,color:ACCENT},
               left:{style:BorderStyle.SINGLE,size:18,color:ACCENT}, right:{style:BorderStyle.SINGLE,size:2,color:ACCENT},
               insideHorizontal:{style:BorderStyle.NONE}, insideVertical:{style:BorderStyle.NONE} },
    rows: [ new TableRow({ children: [ new TableCell({
      width:{size:9360,type:WidthType.DXA}, shading:{type:ShadingType.CLEAR,fill:LIGHT,color:"auto"},
      margins:{top:120,bottom:120,left:180,right:180}, children }) ] }) ],
  });
}

// ---- generic table builder -------------------------------------------
const TW = 9360;
function cell(children, { w, head=false, fill, bold=false, align } = {}) {
  const kids = Array.isArray(children) ? children : [ new Paragraph({
    alignment: align, spacing:{after:0,line:250}, children:[run(String(children), { bold: head||bold, color: head?"FFFFFF":INK, size: head?19:19 })] }) ];
  return new TableCell({ width:{size:w,type:WidthType.DXA},
    shading: head?{type:ShadingType.CLEAR,fill:HEADSHADE,color:"auto"}:(fill?{type:ShadingType.CLEAR,fill,color:"auto"}:undefined),
    margins:{top:70,bottom:70,left:110,right:110}, children: kids });
}
function table(colW, rows, { zebra=true } = {}) {
  const trs = rows.map((r, ri) => new TableRow({ tableHeader: ri===0,
    children: r.map((c, ci) => {
      if (c && c.__cell) return cell(c.children, { w: colW[ci], head: ri===0, fill: c.fill, bold:c.bold, align:c.align });
      return cell(c, { w: colW[ci], head: ri===0, fill: (ri>0 && zebra && ri%2===0)?ZEBRA:undefined,
        align: (ci>0? undefined : undefined) });
    }) }));
  return new Table({ width:{size:100,type:WidthType.PERCENTAGE}, columnWidths: colW,
    borders:{ top:{style:BorderStyle.SINGLE,size:2,color:RULE},bottom:{style:BorderStyle.SINGLE,size:2,color:RULE},
      left:{style:BorderStyle.SINGLE,size:2,color:RULE},right:{style:BorderStyle.SINGLE,size:2,color:RULE},
      insideHorizontal:{style:BorderStyle.SINGLE,size:2,color:RULE},insideVertical:{style:BorderStyle.SINGLE,size:2,color:RULE}},
    rows: trs });
}
// rich cell (custom paragraphs)
function rc(children, opt={}) { return { __cell:true, children: (Array.isArray(children)?children:[children]), ...opt }; }
function tp(runs, o={}) { return new Paragraph({ spacing:{after:0,line:250}, children: runs, ...o }); }

// ---- references -------------------------------------------------------
const REFS = [
 ['MITRE, "CVE-2021-44228," Common Vulnerabilities and Exposures. [Online]. Available: https://www.cve.org/CVERecord?id=CVE-2021-44228'],
 ['National Institute of Standards and Technology, "CVE-2021-44228 Detail," National Vulnerability Database, Dec. 10, 2021. [Online]. Available: https://nvd.nist.gov/vuln/detail/CVE-2021-44228'],
 ['Apache Software Foundation, "Apache Log4j Security Vulnerabilities." [Online]. Available: https://logging.apache.org/log4j/2.x/security.html'],
 ['FIRST, "Common Vulnerability Scoring System version 3.1: Specification Document." [Online]. Available: https://www.first.org/cvss/v3.1/specification-document'],
 ['P. Mell, K. Scarfone, and S. Romanosky, "A Complete Guide to the Common Vulnerability Scoring System Version 2.0," FIRST, Jun. 2007. [Online]. Available: https://www.first.org/cvss/v2/guide'],
 ['FIRST, "Common Vulnerability Scoring System version 4.0: Specification Document." [Online]. Available: https://www.first.org/cvss/v4.0/specification-document'],
 ['Cybersecurity and Infrastructure Security Agency, "Apache Log4j Vulnerability Guidance." [Online]. Available: https://www.cisa.gov/news-events/news/apache-log4j-vulnerability-guidance'],
 ['Cybersecurity and Infrastructure Security Agency, "Emergency Directive 22-02: Mitigate Apache Log4j Vulnerability," Dec. 17, 2021. [Online]. Available: https://www.cisa.gov/news-events/directives/ed-22-02-mitigate-apache-log4j-vulnerability-closed'],
 ['Cyber Safety Review Board, "Review of the December 2021 Log4j Event," CISA, Jul. 11, 2022. [Online]. Available: https://www.cisa.gov/resources-tools/resources/review-december-2021-log4j-event'],
 ['Australian Cyber Security Centre, "2021-007: Log4j vulnerability – advice and mitigations." [Online]. Available: https://www.cyber.gov.au/about-us/advisories/2021-007-log4j-vulnerability-advice-and-mitigations'],
 ['J. Wetter and N. Ringland, "Understanding the Impact of Apache Log4j Vulnerability," Google Open Source Insights, Dec. 17, 2021. [Online]. Available: https://security.googleblog.com/2021/12/understanding-impact-of-apache-log4j.html'],
 ['Microsoft, "Guidance for preventing, detecting, and hunting for CVE-2021-44228 Log4j 2 exploitation," Microsoft Security Blog, Dec. 11, 2021. [Online]. Available: https://www.microsoft.com/en-us/security/blog/2021/12/11/guidance-for-preventing-detecting-and-hunting-for-cve-2021-44228-log4j-2-exploitation/'],
 ['FIRST, "Exploit Prediction Scoring System (EPSS)." [Online]. Available: https://www.first.org/epss/'],
 ['Cybersecurity and Infrastructure Security Agency, "Stakeholder-Specific Vulnerability Categorization (SSVC)." [Online]. Available: https://www.cisa.gov/stakeholder-specific-vulnerability-categorization-ssvc'],
 ['A. Nelson, S. Rekhi, K. Scarfone, and M. Souppaya, "Incident Response Recommendations and Considerations for Cybersecurity Risk Management: A CSF 2.0 Community Profile," NIST SP 800-61r3, Apr. 2025. [Online]. Available: https://doi.org/10.6028/NIST.SP.800-61r3'],
 ['Australian Signals Directorate, "Essential Eight Maturity Model," Australian Cyber Security Centre, Nov. 2023. [Online]. Available: https://www.cyber.gov.au/resources-business-and-government/essential-cyber-security/essential-eight/essential-eight-maturity-model'],
 ['Splunk Threat Research Team, "Log4Shell - Detecting Log4j 2 RCE Using Splunk," Splunk, Dec. 2021. [Online]. Available: https://www.splunk.com/en_us/blog/security/log-jammin-log4j-2-rce.html'],
 ['Wazuh, "Detecting Log4Shell with Wazuh." [Online]. Available: https://wazuh.com/blog/detecting-log4shell-with-wazuh/'],
 ['F. Roth, "Log4j RCE CVE-2021-44228 Generic (Sigma rule)," SigmaHQ. [Online]. Available: https://github.com/SigmaHQ/sigma'],
 ['MITRE, "Exploit Public-Facing Application (T1190)," MITRE ATT&CK. [Online]. Available: https://attack.mitre.org/techniques/T1190/'],
 ['Siemens ProductCERT, "Security Advisories" (Apache Log4j impact on Siemens products). [Online]. Available: https://www.siemens.com/global/en/products/services/cert.html'],
];
function refPara(i, text) {
  return new Paragraph({ spacing:{after:90,line:264}, indent:{left:520,hanging:520},
    children:[ run(`[${i+1}] `, { bold:true }), run(text, { size:19 }) ] });
}
function cite(...ns) { return run("[" + ns.join("], [") + "]"); }

// ---- document ---------------------------------------------------------
const children = [];

// Title page
children.push(
  new Paragraph({ spacing:{before:1600,after:0}, alignment:AlignmentType.CENTER, children:[run("COMP2004", { bold:true, size:30, color:ACCENT })] }),
  new Paragraph({ alignment:AlignmentType.CENTER, spacing:{after:600}, children:[run("Cyber Security Fundamentals", { size:24, color:"52514E" })] }),
  new Paragraph({ alignment:AlignmentType.CENTER, spacing:{after:60}, children:[run("Assessment 2", { size:22, color:"52514E" })] }),
  new Paragraph({ alignment:AlignmentType.CENTER, spacing:{after:40}, children:[run("The Log4Shell Vulnerability:", { bold:true, size:44, color:INK })] }),
  new Paragraph({ alignment:AlignmentType.CENTER, spacing:{after:500}, children:[run("A CVSS Analysis and SIEM Demonstration Proposal", { bold:true, size:30, color:ACCENT2 })] }),
);
children.push(...figure("fig1_attack_chain.png", 560, 236, "The Log4Shell (CVE-2021-44228) exploitation chain and the points at which a SIEM can observe it."));
children.push(
  new Paragraph({ alignment:AlignmentType.CENTER, spacing:{before:400, after:40}, children:[run("Prepared by: Kismat Acharya  (Student ID: 24823456)", { size:22 })] }),
  new Paragraph({ alignment:AlignmentType.CENTER, spacing:{after:40}, children:[run("Role: Security Operations Centre (SOC) Analyst", { size:22 })] }),
  new Paragraph({ alignment:AlignmentType.CENTER, spacing:{after:40}, children:[run("Date: 24 September 2026", { size:22 })] }),
  new Paragraph({ alignment:AlignmentType.CENTER, spacing:{after:40}, children:[run("Referencing style: IEEE", { size:22 })] }),
  new Paragraph({ children:[new PageBreak()] }),
);

// TOC
children.push(
  new Paragraph({ spacing:{after:120}, children:[run("Contents", { bold:true, size:28, color:ACCENT2 })] }),
  new TableOfContents("Contents", { hyperlink:true, headingStyleRange:"1-3" }),
  new Paragraph({ children:[new PageBreak()] }),
);

// ---------------------------------------------------------------- Exec summary
children.push(h1("Executive summary"));
children.push(p("In December 2021 a remote code execution flaw in Apache Log4j 2, a Java logging library embedded in an enormous share of enterprise software, was disclosed as CVE-2021-44228 and nicknamed “Log4Shell.” Because Log4j records data that an attacker can control, and because a vulnerable version would interpret a short “lookup” expression inside that data, an unauthenticated attacker could make a target server fetch and run code of the attacker’s choosing simply by getting a crafted string logged — for example, in an HTTP header. This report is written from the perspective of a SOC analyst at an electricity utility (a “power company”) that runs Java deep in its operational technology (OT): its SCADA and Energy Management Systems, a SIMATIC IT Report Manager V6.7 reporting product, the OPC UA Java Stack, and Siemens Connect X200/X300 telecontrol gateways. That context — where a compromise threatens physical grid equipment, not just data — shapes every score and recommendation. All CVSS metrics, scores and vector strings below were determined and justified independently; published vendor scores are cited only for corroboration."));
children.push(bullet("", 0, [run("Task 1 — CVSS analysis. ", {bold:true}), run("The Log4j vulnerability family (CVE-2021-44228/45046/45105/44832) is identified and scored, then CVE-2021-44228 is dissected in full. Each Base metric is justified from the vulnerability’s mechanics, giving the maximum Base score of 10.0 (Critical). Temporal and Environmental metrics are then applied to three of the utility’s real assets (9.5 → 8.7 → 8.0) to show how the same flaw carries different residual risk in different OT contexts, and the result is contrasted across CVSS v2.0, v3.1 and v4.0.")]));
children.push(bullet("", 0, [run("Task 2 — SIEM proposal. ", {bold:true}), run("A Splunk Enterprise Security SIEM (paired with a passive OT sensor) is proposed for the utility, with the log inputs, correlation insights, response actions and a scripted demonstration that detects a Log4Shell attempt end to end, mapped to the MITRE ATT&CK framework and to published Splunk, Sigma and Wazuh detections.")]));
children.push(callout([
  new Paragraph({ spacing:{after:60}, children:[run("Bottom line for management", { bold:true, color:ACCENT2, size:21 })] }),
  new Paragraph({ spacing:{after:0, line:268}, alignment:AlignmentType.JUSTIFIED, children:[run("Log4Shell scores the maximum 10.0 (Critical): trivial to exploit, remotely, without credentials, for full system takeover. In a power company the danger is amplified — corrupted control data or lost availability carries safety and grid-stability consequences — and patching alone was never enough because the library is buried deep in the software supply chain and in OT firmware. Detection therefore matters as much as remediation. A SIEM turns the scattered evidence of an attempt — web logs, IT/OT firewall egress, DNS, OT sensor and endpoint telemetry — into a single, alertable picture, and is the control this report recommends investing in.", { size:20 })] }),
]));

// ============================================================== TASK 1
children.push(new Paragraph({ children:[new PageBreak()] }));
children.push(h1("Task 1 — CVSS analysis of CVE-2021-44228 (Log4Shell)"));

children.push(h2("1.1  The vulnerability in brief"));
children.push(body([
  run("Apache Log4j 2 supports a feature called "), run("message lookups", {italics:true}),
  run(": special tokens of the form "), mono("${...}"),
  run(" inside a logged message are expanded at logging time. One supported lookup, "),
  mono("jndi"),
  run(", resolves names through the Java Naming and Directory Interface (JNDI), which can reach out over LDAP, RMI or DNS. In vulnerable versions (2.0-beta9 through 2.15.0) this expansion happened even when the "),
  mono("${jndi:...}"),
  run(" string arrived as untrusted data. An attacker who could get such a string logged — by placing it in an HTTP "),
  mono("User-Agent"),
  run(" header, a form field, a username, or any other logged input — could force the server to contact an attacker-controlled directory server, retrieve a reference to a remote Java class, load it and execute it. The result is unauthenticated remote code execution (RCE). "),
  cite(1,2,3),
]));
children.push(body([
  run("The flaw is classified under "), run("CWE-917", {bold:true}),
  run(" (Improper Neutralization of Special Elements used in an Expression Language Statement), with related weaknesses CWE-502 (deserialization of untrusted data), CWE-400 (uncontrolled resource consumption) and CWE-20 (improper input validation). "),
  cite(2),
  run(" It maps to the MITRE ATT&CK technique "), run("T1190 — Exploit Public-Facing Application", {bold:true}), run(". "), cite(20),
]));
children.push(...figure("fig1_attack_chain.png", 600, 253, "Figure 1. The five stages of a Log4Shell attack. Attacker-controlled steps are orange; the victim server performs the shaded steps itself, which is what makes the flaw so dangerous."));

children.push(h2("1.2  Vulnerabilities in scope — the Log4j family"));
children.push(body([
  run("Log4Shell is not a single CVE. The rushed remediation itself introduced further flaws, so a comprehensive analysis must consider the whole family. The scores below are the author’s own determinations (method as in §1.4); they are consistent with, but not copied from, the published values. "),
  cite(3),
]));
children.push(table([1650, 900, 3260, 1250, 2300], [
  ["CVE","My score","Nature of the flaw","Fixed in","Relevance to our scenario"],
  [ rc(tp([run("CVE-2021-44228",{bold:true}), new TextRun({break:1}), run("(Log4Shell)",{size:17,color:"52514E"})])), rc(tp([run("10.0",{bold:true,color:CRIT}), run(" Crit",{size:16})],{alignment:AlignmentType.CENTER})), "Unauthenticated RCE via JNDI message lookup", "2.15.0", "Primary risk to all four Java assets" ],
  [ rc(tp([run("CVE-2021-45046",{bold:true})])), rc(tp([run("9.0",{bold:true,color:CRIT}), run(" Crit",{size:16})],{alignment:AlignmentType.CENTER})), "RCE — the 2.15.0 fix proved incomplete", "2.16.0", "Assets patched only to 2.15.0 remain exposed" ],
  [ rc(tp([run("CVE-2021-45105",{bold:true})])), rc(tp([run("5.9",{bold:true,color:"C87000"}), run(" Med",{size:16})],{alignment:AlignmentType.CENTER})), "Denial of service via recursive self-referential lookups", "2.17.0", "DoS of an EMS/SCADA node is an availability event" ],
  [ rc(tp([run("CVE-2021-44832",{bold:true})])), rc(tp([run("6.6",{bold:true,color:"C87000"}), run(" Med",{size:16})],{alignment:AlignmentType.CENTER})), "RCE via JDBC Appender; needs attacker control of config", "2.17.1", "Lower likelihood; still requires the final patch" ],
]));
children.push(body([
  run("The practical consequence for the utility is that patching to 2.15.0 is not the finish line — 2.17.1 is. Each affected product (SIMATIC IT Report Manager, the OPC UA Java Stack, and the firmware of the Connect X200/X300 gateways) must be triaged against the vendor’s Siemens ProductCERT advisories, because in embedded OT products the fix depends on a firmware release, not a library the operator can swap. "),
  cite(21),
]));
children.push(p("The remainder of Task 1 focuses on CVE-2021-44228, the highest-severity member and the one directly relevant to every asset in scope.", ));

children.push(h2("1.3  Why CVSS, and which version"));
children.push(body([
  run("The Common Vulnerability Scoring System (CVSS), maintained by FIRST, is the industry-standard open framework for expressing the severity of a vulnerability as a number from 0.0 to 10.0 and as a compact vector string. It is organised into three metric groups: the "),
  run("Base", {bold:true}), run(" group captures the intrinsic, constant qualities of the flaw; the "),
  run("Temporal", {bold:true}), run(" group (renamed "), run("Threat", {italics:true}),
  run(" in v4.0) adjusts for how the real-world threat evolves; and the "),
  run("Environmental", {bold:true}),
  run(" group tailors the score to a specific organisation’s deployment. "), cite(4,5,6),
]));
children.push(p("The National Vulnerability Database (NVD) published a CVSS v3.1 Base score for this CVE. This analysis derives that Base score from first principles, then layers Temporal and Environmental metrics on top, and finally contrasts the result with the older v2.0 and the newer v4.0 systems so the differences between the versions are visible on one vulnerability.", ));

children.push(h2("1.4  Base metric analysis (CVSS v3.1)"));
children.push(p("Each Base metric below is justified from the way Log4Shell actually works. The resulting vector is CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H."));
children.push(table([1700, 1150, 6510], [
  ["Metric","Value","Justification"],
  ["Attack Vector (AV)","Network (N)","The attacker needs only to reach a service that logs their input over a network; the malicious string can be delivered from anywhere on the internet. This is the highest-exposure value."],
  ["Attack Complexity (AC)","Low (L)","No special conditions, race, or configuration are required. A single request containing the payload is enough; public proof-of-concept exploits worked reliably."],
  ["Privileges Required (PR)","None (N)","The attacker needs no account or prior authentication — any input path that ends up in a log will do."],
  ["User Interaction (UI)","None (N)","No victim (e.g. an administrator) needs to click or do anything; logging happens automatically."],
  ["Scope (S)","Changed (C)","The vulnerable component (the Log4j library / the JVM) can affect resources beyond its own security authority — code executes on the host and can pivot into the wider system. A changed scope raises the score."],
  ["Confidentiality (C)","High (H)","Arbitrary code runs with the application’s privileges, exposing any data the process can read — secrets, tokens, customer records."],
  ["Integrity (I)","High (H)","The attacker can create, modify or delete data and install persistent backdoors."],
  ["Availability (A)","High (H)","The attacker can crash, ransom or fully commandeer the service."],
]));
children.push(callout([
  new Paragraph({ spacing:{after:0, line:270}, children:[
    run("CVSS v3.1 Base score = ", {size:21}), run("10.0", {bold:true, size:24, color:CRIT}),
    run("  —  Severity: ", {size:21}), run("CRITICAL", {bold:true, size:21, color:CRIT}),
    run("      Vector: ", {size:20}), mono("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H"),
  ]}),
]));
children.push(body([
  run("This is the maximum possible score. It is reached because the two “halves” of the Base equation are both maximal: the "),
  run("Exploitability", {italics:true}),
  run(" sub-score is driven to its ceiling by AV:N, AC:L, PR:N and UI:N (nothing stands between an attacker and the flaw), while the "),
  run("Impact", {italics:true}),
  run(" sub-score is maximal because confidentiality, integrity and availability are all fully compromised and Scope is Changed, which increases the weight of that impact. A perfect 10.0 is uncommon and, by itself, tells a SOC to treat the finding as an emergency. "),
  cite(4),
]));

children.push(h2("1.5  Temporal metrics — how the threat evolved"));
children.push(p("Temporal metrics describe factors that change over time but are the same for every organisation. Their values shifted dramatically during December 2021:"));
children.push(table([2450, 1500, 5410], [
  ["Temporal metric","Value","Rationale (as of mid-to-late December 2021)"],
  ["Exploit Code Maturity (E)","High (H)","Weaponised, reliable exploit code and mass-scanning were public within a day of disclosure; automated exploitation was widespread."],
  ["Remediation Level (RL)","Official Fix (O)","Apache released fixed versions (2.15.0, then 2.16.0/2.17.0 as follow-up issues emerged). An official fix lowers the temporal score slightly."],
  ["Report Confidence (RC)","Confirmed (C)","The vulnerability was confirmed by the vendor and independently reproduced worldwide."],
]));
children.push(callout([ new Paragraph({ spacing:{after:0}, children:[
  run("CVSS v3.1 Temporal score = ", {size:21}), run("9.5", {bold:true, size:24, color:CRIT}),
  run("  (still Critical).   Vector adds ", {size:20}), mono("/E:H/RL:O/RC:C"), run(".", {size:20}) ]}) ]));
children.push(body([
  run("The score barely moves from 10.0. The only downward pull is the availability of an official fix; the maturity of exploit code and confirmed status keep the number pinned near the top. In the first days after disclosure, before any patch existed, Remediation Level would have been "),
  mono("U"), run(" (Unavailable) and the temporal score would have equalled the Base 10.0 — a useful reminder that the window of maximum danger is the window before a fix ships. This is also why complementary signals such as the "),
  run("Exploit Prediction Scoring System (EPSS)", {bold:true}),
  run(", which estimates the probability of exploitation in the next 30 days, rate Log4Shell in the topmost percentile. "), cite(4,13),
]));

children.push(h2("1.6  Environmental metrics — the power company’s assets"));
children.push(body([
  run("Environmental metrics let a SOC re-score the same CVE for its own deployment, adjusting the security requirements (CR/IR/AR) and, where justified, overriding Base metrics with Modified equivalents (e.g. Modified Attack Vector). A crucial, scenario-wide decision comes first: because this is a power company, I set "),
  run("Integrity Requirement and Availability Requirement to High", {bold:true}),
  run(" for every OT asset — corrupted control data or lost availability threatens grid stability and physical safety — and Confidentiality Requirement to Medium (operational data matters, but the physical impacts dominate). What then differs between assets is how reachable each one is. The three real assets below show the spread."),
]));
children.push(h3("Asset A — SIMATIC IT Report Manager V6.7 (IT/OT boundary, exposed)"));
children.push(body([
  run("A Java reporting product at the IT/OT boundary, network-reachable and with no compensating control that reduces exposure. The Base metrics are unchanged; only the security requirements are applied. Environmental vector adds "),
  mono("/CR:M/IR:H/AR:H"), run(" over the temporal vector."),
]));
children.push(callout([ new Paragraph({ spacing:{after:0}, children:[
  run("Asset A environmental score = ", {size:21}), run("9.5", {bold:true, size:23, color:CRIT}), run("  (Critical) — remediate first.", {size:21}) ]}) ]));
children.push(h3("Asset B — OPC UA Java Stack in the SCADA/EMS core (deep, segmented)"));
children.push(body([
  run("The same vulnerable class of component, but deep inside the segmented OT network (a low Purdue level), reachable only from an adjacent control-network segment and behind egress filtering that impedes the outbound JNDI callback. I therefore set Modified Attack Vector to "),
  mono("MAV:A"), run(" (Adjacent) and Modified Attack Complexity to "), mono("MAC:H"),
  run(", keeping the High OT security requirements. Environmental vector: "),
  mono("/CR:M/IR:H/AR:H/MAV:A/MAC:H"), run("."),
]));
children.push(callout([ new Paragraph({ spacing:{after:0}, children:[
  run("Asset B environmental score = ", {size:21}), run("8.0", {bold:true, size:23, color:"C87000"}), run("  (High).", {size:21}) ]}) ]));
children.push(h3("Asset C — Siemens Connect X200/X300 gateway (substation edge, hardened remote)"));
children.push(body([
  run("A telecontrol gateway at the substation edge: remotely reachable for legitimate telecontrol (so Attack Vector stays Network) but hardened, which raises exploitation complexity. I set "),
  mono("MAC:H"), run(" with the High OT security requirements. Environmental vector: "),
  mono("/CR:M/IR:H/AR:H/MAC:H"), run("."),
]));
children.push(callout([ new Paragraph({ spacing:{after:0}, children:[
  run("Asset C environmental score = ", {size:21}), run("8.7", {bold:true, size:23, color:"C87000"}), run("  (High).", {size:21}) ]}) ]));
children.push(body([
  run("The same 10.0 flaw resolves to 9.5, 8.7 and 8.0 across the three assets, giving the SOC a defensible remediation order: the exposed SIMATIC boundary server first, then the gateways, then the deeply segmented OPC UA component. The critical OT lesson is that none of them drops below High: in an IT estate a segmented, low-value host might fall to Medium, but here the High integrity and availability requirements keep every grid-connected asset serious. Note also that the very controls that lowered B and C — segmentation and egress filtering — are exactly what the SIEM in Task 2 monitors, so scoring and detection reinforce each other. "),
  cite(4),
]));

children.push(h2("1.7  Cross-version comparison: v2.0, v3.1 and v4.0"));
children.push(p("Running the same vulnerability through three generations of CVSS shows how the standard has matured. The comparison also explains why a SOC should always note which version a score came from."));
children.push(table([1550, 1150, 6660], [
  ["Version","Base","What it captures, and the key difference"],
  [ rc(tp([run("CVSS v2.0", {bold:true})])), rc(tp([run("9.3", {bold:true, size:22})], {alignment:AlignmentType.CENTER})),
    rc(tp([run("Vector "), mono("AV:N/AC:M/Au:N/C:C/I:C/A:C"), run(". v2 has no Scope metric and rates Access Complexity as Medium for this class, so it cannot express the “break-out” nature of the flaw and lands below 10. Its impact metrics are all “Complete.”")])) ],
  [ rc(tp([run("CVSS v3.1", {bold:true})])), rc(tp([run("10.0", {bold:true, size:22, color:CRIT})], {alignment:AlignmentType.CENTER})),
    rc(tp([run("Vector "), mono("AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H"), run(". Introduces "), run("Scope", {italics:true}), run(" and separates Privileges Required from User Interaction, so it correctly rewards the fact that the exploit crosses a security boundary — reaching the maximum 10.0. This is the score NVD publishes. "), cite(2,4)])) ],
  [ rc(tp([run("CVSS v4.0", {bold:true})])), rc(tp([run("10.0", {bold:true, size:22, color:CRIT})], {alignment:AlignmentType.CENTER})),
    rc(tp([run("Vector "), mono("CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:H/SC:H/SI:H/SA:H"), run(". Adds "), run("Attack Requirements (AT)", {italics:true}), run(" and splits impact into Vulnerable-system (VC/VI/VA) and Subsequent-system (SC/SI/SA) metrics, replacing Scope with a clearer model. Log4Shell is High on both, so it remains 10.0. "), cite(6)])) ],
]));
children.push(...figure("fig2_cvss_scores.png", 600, 210, "Figure 2. CVE-2021-44228 scored across CVSS versions and metric groups for the power company. The Base score is maximal under v3.1 and v4.0; the environmental scores (9.5\u20138.0) are how the SOC sequences remediation across OT assets."));

children.push(h2("1.8  What the score means for a SOC"));
children.push(p("A CVSS score is an input to risk-based prioritisation, not the whole decision. For Log4Shell the numbers align with how the response actually unfolded worldwide, and translate into concrete SOC actions:"));
children.push(bullet("", 0, [run("Treat it as an emergency, but prioritise by environment. ", {bold:true}), run("The 10.0 Base score justified out-of-band patching; the Environmental re-scoring (9.5 \u2192 8.0 above) is how a SOC sequences that work across a large estate. Frameworks such as CISA’s SSVC (Act / Attend / Track) and EPSS complement CVSS by folding in exploitation status. "), cite(13,14)]));
children.push(bullet("", 0, [run("Assume patching is incomplete. ", {bold:true}), run("Google’s Open Source Insights team found more than 35,000 Java packages (over 8% of Maven Central) depended on a vulnerable Log4j, most of them transitively — many organisations did not know they were affected. The Cyber Safety Review Board later called Log4j an “endemic vulnerability” expected to persist for a decade. Detection therefore has to run alongside remediation. "), cite(9,11)]));
children.push(bullet("", 0, [run("Regulators mandated urgency. ", {bold:true}), run("CISA issued Emergency Directive 22-02 requiring U.S. federal agencies to remediate within days, and Australia’s ACSC issued advisory 2021-007. Under the ASD Essential Eight, a working exploit for an internet-facing service compels patching within 48 hours. "), cite(8,10,16)]));
children.push(callout([ new Paragraph({ spacing:{after:0, line:268}, alignment:AlignmentType.JUSTIFIED, children:[
  run("Link to Task 2: ", {bold:true, color:ACCENT2}),
  run("CVSS tells us how bad Log4Shell is and where to fix it first. It does not tell us whether someone is trying it against us right now. That question — detection — is what the SIEM in Task 2 answers, and the environmental mitigations that lowered Asset B’s score (egress filtering, segmentation) are precisely the controls the SIEM monitors.", {size:20}) ]}) ]));

// ============================================================== TASK 2
children.push(new Paragraph({ children:[new PageBreak()] }));
children.push(h1("Task 2 — SIEM proposal and demonstration"));

children.push(h2("2.1  Purpose and scope"));
children.push(body([
  run("Following the Log4Shell incident the power company is reviewing all SOC processes and technology. This part proposes a Security Information and Event Management (SIEM) capability, justified specifically against this incident and the utility’s environment rather than in the abstract. A SIEM collects log and event data from across both the IT and OT estates, normalises it into a common format, and correlates it in near-real time to raise alerts an analyst can act on. The proposal is organised around the three questions the audit asks — the "),
  run("inputs", {bold:true}), run(" the SIEM must ingest (§2.4), the "),
  run("insights", {bold:true}), run(" it must produce (§2.5), and the "),
  run("actions", {bold:true}),
  run(" it must drive (§2.6) — followed by a demonstration and an honest appraisal. Free and open-source components are used in the demonstration so it can be reproduced at no cost."),
]));
children.push(callout([
  new Paragraph({ spacing:{after:50}, children:[run("Why a SIEM was the right control for Log4Shell", {bold:true, color:ACCENT2, size:21})]}),
  new Paragraph({ spacing:{after:0, line:268}, alignment:AlignmentType.JUSTIFIED, children:[run("No single log tells the whole story. A web log shows a suspicious ${jndi:...} string; a boundary-firewall log shows an odd outbound LDAP connection; an OT sensor shows a gateway behaving abnormally. Individually each is easy to miss. A SIEM is the one place those events line up, on one asset, within seconds — turning three weak signals into one high-confidence alert.", {size:20})]}),
]));

children.push(h2("2.2  Which SIEM, and why in this context"));
children.push(body([
  run("The proposal is "), run("Splunk Enterprise Security", {bold:true}),
  run(" as the primary platform: it offers risk-based alerting, ready-made and community Log4Shell detections mapped to MITRE ATT&CK, and an OT security add-on. It is paired with a "),
  run("passive OT network-monitoring sensor", {bold:true}),
  run(" (for example Nozomi or Claroty) feeding the SIEM, because endpoint agents cannot be installed on controllers or the Siemens Connect gateways — the sensor observes the OT network and forwards events instead. The demonstration reproduces the same detections at no cost with Wazuh or the Elastic Stack, so the design is not tied to one vendor. "),
  cite(17,18),
]));

children.push(h2("2.3  Reference architecture"));
children.push(p("The proposed pipeline has four stages: diverse IT and OT log sources feed lightweight collectors (and, for OT, a passive sensor), which forward over encrypted transport to the SIEM for parsing, correlation and enrichment; the SIEM’s outputs then drive the SOC’s triage, automated response, dashboards and reporting."));
children.push(...figure("fig3_siem_architecture.png", 610, 261, "Figure 3. Proposed SIEM reference architecture for the utility. Enrichment with OT asset criticality, Purdue zone and threat intelligence is what lets the platform prioritise the exposed SIMATIC boundary server (Asset A in Task 1) over the deeply segmented OPC UA component."));

children.push(h2("2.4  SIEM inputs — what we must ingest, and why"));
children.push(p("A detection is only as good as the telemetry behind it. Each input below is chosen for the specific part of the Log4Shell chain (Figure 1) it reveals in this environment."));
children.push(table([2550, 3350, 3460], [
  ["Data input","What it provides","Why it is critical for this incident"],
  ["IT / DMZ web & app / WAF logs (SIMATIC Report Mgr, Java apps)","HTTP request lines, headers, User-Agent, URIs, WAF verdicts","Stage 1–2: the inbound ${jndi:...} payload lands here first, including obfuscated variants"],
  ["IT–OT boundary firewall & proxy","Outbound connection and allow/deny records, destination ports","Stage 3: server-initiated egress to LDAP (389/636) or RMI (1099) — a tell an OT host should never make"],
  ["DNS resolver logs","Queries made by servers and gateways","Stage 3: callback / “canary” lookups — visible even when the inbound payload is encrypted"],
  ["OT telemetry (Connect X200/X300 syslog, OPC UA, historian)","Passive-sensor events where no agent can run","Abnormal gateway behaviour and new connections on assets that cannot be instrumented directly"],
  ["Endpoint (EDR) / Sysmon / auditd","Process creation, parent-child lineage, network connections","Stage 5: java/java.exe spawning a shell, curl or a miner — proof an attempt succeeded"],
  ["Vulnerability scan / SBOM inventory","Which assets run vulnerable Log4j and at what version","Turns a raw alert into a prioritised one and confirms 2.17.1 remediation status"],
]));

children.push(h2("2.5  SIEM insights — what we must detect, and why"));
children.push(p("The SIEM produces four layered insights. Layering matters: signature matching on the payload catches the noisy mass-scanning, while the behavioural insights catch a quieter attacker who evades the string match but still has to make the server call out or spawn a process."));

children.push(h3("Insight 1 — Inbound JNDI payload in web traffic (signature)"));
children.push(body([ run("Search web/WAF logs for the lookup pattern and its common evasions ("),
  mono("${jndi:ldap://"), run(", "), mono("${${lower:j}ndi:"), run(", URL-/Base64-encoded forms). This mirrors the published SigmaHQ rule "),
  run("“Log4j RCE CVE-2021-44228 Generic”", {italics:true}), run(" and Splunk’s ESCU analytic. Example Splunk SPL (Nginx access logs):"), cite(17,19) ]));
children.push(codeBlock([
  'index=web sourcetype=nginx:plus:kv',
  '| rex field=_raw "(?<jndi>(?i)\\$(\\{|%7[bB])[^\\n]*?jndi(:|%3[aA]))"',
  '| where isnotnull(jndi)',
  '| stats count values(http_user_agent) as user_agent by src_ip, uri_path, status',
  '| sort - count',
]));
children.push(body([ run("MITRE ATT&CK: T1190 (Exploit Public-Facing Application). Known false positive: authorised vulnerability scanners — tuned out by an allow-list of scanner source IPs. "), cite(20) ]));

children.push(h3("Insight 2 — Server-initiated outbound LDAP/RMI (behaviour)"));
children.push(p("Correlate firewall/proxy egress: a web or application server making an outbound connection to ports 389, 636, 1099 or 1389 is almost never legitimate. This catches exploitation even when the inbound payload was missed or encrypted. Raise a high-severity alert when the destination is external and the source is a server in the DMZ."));
children.push(h3("Insight 3 — Correlated inbound payload + outbound callback (high confidence)"));
children.push(body([ run("The flagship rule: within a short window (e.g. 5 minutes), a host that "),
  run("received", {italics:true}), run(" a JNDI payload (insight 1) and then "),
  run("made", {italics:true}),
  run(" an outbound LDAP/RMI/DNS connection (insight 2) to the same or attacker-named host. Two independent weak signals combine into one strong one, dramatically reducing false positives. Splunk publishes an equivalent “JNDI Payload Injection with Outbound Connection” analytic. "), cite(17) ]));
children.push(h3("Insight 4 — Suspicious child process of Java (post-exploitation)"));
children.push(body([ run("From EDR/Sysmon (Event ID 1) or Linux auditd: a Java process ("),
  mono("java"), run("/"), mono("java.exe"),
  run(") spawning a shell, "), mono("curl"), run(", "), mono("wget"), run(", "), mono("powershell"),
  run(" or an unknown binary. This is the clearest evidence that an attempt succeeded and is the trigger for immediate host isolation. Wazuh provides file-integrity and command-execution rules for this stage. "), cite(18) ]));

children.push(h2("2.6  SIEM actions — what we must do, and why"));
children.push(body([
  run("In an OT environment automation must be "), run("safety-gated", {bold:true}),
  run(": the SIEM/SOAR may act freely at the IT/OT boundary, but it must never automatically isolate a live controller or gateway, because taking a device offline can itself cause an outage. A human confirms before anything touches the grid. The actions below follow from the insights above."),
]));
children.push(h3("Contain"));
children.push(bullet("SOAR blocks the attacking source IP and denies the outbound LDAP/RMI callback at the boundary firewall — stopping the chain at Stage 3."));
children.push(bullet("Isolate affected IT hosts automatically; quarantine any OT asset only with operator sign-off, to avoid causing the very outage we are protecting against."));
children.push(h3("Enrich and prioritise"));
children.push(bullet("Cross-reference the SBOM/scan feed to confirm the alerting asset actually runs a vulnerable Log4j version, and attach its CVSS environmental score and Purdue zone so triage is instant."));
children.push(bullet("Auto-raise severity for the exposed SIMATIC boundary server (Asset A, 9.5) ahead of the deeply segmented OPC UA component (Asset B, 8.0)."));
children.push(h3("Respond and report"));
children.push(bullet("", 0, [run("Open an incident ticket, page on-call and OT engineers, and retrospectively hunt stored logs for earlier attempts — then preserve an evidence trail aligned to "), run("NIST SP 800-61r3", {bold:true}), run(" for the audit that prompted this review. "), cite(15)]));

children.push(h2("2.7  Demonstration walkthrough"));
children.push(p("The live demonstration (to be recorded and linked with the submission — see §2.10) runs a safe, self-contained lab: a deliberately vulnerable Log4j application container, an attacker container on an isolated network, and a free SIEM (Splunk Free, Wazuh, or the Elastic Stack) ingesting the logs. No real or third-party systems are touched. The recorded sequence is:"));
children.push(num("", [run("Baseline. ", {bold:true}), run("Show the SIEM dashboards quiet — normal web traffic flowing in, no alerts. Establish what “good” looks like.")]));
children.push(num("", [run("Reconnaissance & attempt. ", {bold:true}), run("From the attacker container, send an HTTP request whose header carries a ${jndi:ldap://...} lookup pointing at the attacker’s own listener on the isolated network.")]));
children.push(num("", [run("Detection — signature. ", {bold:true}), run("Insight 1 fires within seconds; open the alert and show the offending request, source IP and User-Agent.")]));
children.push(num("", [run("Detection — behaviour & correlation. ", {bold:true}), run("Show the vulnerable server’s outbound LDAP callback in the boundary-firewall logs (insight 2), then the correlated high-confidence alert (insight 3) tying inbound payload to outbound callback on the same host.")]));
children.push(num("", [run("Post-exploitation. ", {bold:true}), run("Trigger the follow-on stage so the server spawns a shell; show insight 4 firing from endpoint telemetry and the ATT&CK technique tags on the alert.")]));
children.push(num("", [run("Response. ", {bold:true}), run("Walk through the analyst triage: pivot from alert to raw events, confirm the asset is vulnerable via the scanner/SBOM feed, and show the SOAR playbook that blocks the source IP and isolates the host.")]));
children.push(callout([ new Paragraph({ spacing:{after:0, line:268}, alignment:AlignmentType.JUSTIFIED, children:[
  run("Safety note. ", {bold:true, color:ACCENT2}),
  run("The demonstration is performed only in an isolated lab, against a system the presenter owns, using documentation IP ranges and reserved domains. It is an authorised, educational proof of detection — not an attack on any live or third-party system.", {size:20}) ]}) ]));

children.push(h2("2.8  Mapping detections to MITRE ATT&CK"));
children.push(table([3100, 2550, 3710], [
  ["Attack stage","ATT&CK technique","SIEM insight / data source"],
  ["Initial access via crafted input","T1190 Exploit Public-Facing Application","Insight 1 — IT/DMZ web & WAF logs"],
  ["Command & control callback","T1071 Application Layer Protocol / T1105 Ingress Tool Transfer","Insights 2 & 3 — boundary firewall, proxy, DNS"],
  ["Execution of retrieved code","T1059 Command and Scripting Interpreter","Insight 4 — EDR / Sysmon / OT sensor"],
  ["Persistence & escalation","T1136 Create Account / T1068 Exploitation for Privilege Escalation","Identity, cloud & OT historian logs"],
]));

children.push(h2("2.9  Operational considerations, benefits and limitations"));
children.push(h3("Benefits"));
children.push(bullet("Central visibility across otherwise siloed logs, enabling the cross-source correlation that single tools cannot achieve."));
children.push(bullet("Faster detection and response — measurable as reduced Mean Time to Detect/Respond (MTTD/MTTR) — and an auditable record for incident response and compliance."));
children.push(bullet("Threat-intelligence enrichment (CISA KEV, ACSC advisories, IOC feeds) so new Log4Shell-style indicators can be searched retrospectively across stored logs."));
children.push(bullet("", 0, [run("Supports incident response aligned to "), run("NIST SP 800-61r3", {bold:true}), run(" and detection obligations under the ASD Essential Eight. "), cite(15,16)]));
children.push(h3("Limitations and how the proposal addresses them"));
children.push(bullet("", 0, [run("Coverage gaps. ", {bold:true}), run("A SIEM only sees what it ingests; if the SIMATIC or OT logs are not onboarded, nothing fires. Mitigation: an onboarding checklist tied to the asset inventory, validated with atomic tests.")]));
children.push(bullet("", 0, [run("Alert fatigue. ", {bold:true}), run("Signature rules on ${jndi:...} are noisy under mass scanning. Mitigation: risk-based alerting and the correlated insight 3, which only fires on payload plus callback.")]));
children.push(bullet("", 0, [run("Encryption and evasion. ", {bold:true}), run("TLS or novel obfuscation can hide the inbound string. Mitigation: the behavioural insights (2 and 4) that watch the server’s own outbound and process activity, which the attacker cannot avoid.")]));
children.push(bullet("", 0, [run("No agents on OT devices. ", {bold:true}), run("Endpoint agents cannot run on controllers or the Connect gateways. Mitigation: a passive OT network sensor (Nozomi/Claroty) feeds the SIEM, and safety-gated response keeps automation off live OT assets.")]));
children.push(bullet("", 0, [run("Cost and skills. ", {bold:true}), run("Commercial SIEM licensing scales with data volume and needs skilled analysts. Mitigation: start with an open-source stack (Wazuh/Elastic) and disciplined log selection; grow into a managed or commercial tier as volume justifies it.")]));

children.push(h2("2.10  Recording and submission"));
children.push(p("The presentation and demonstration are to be recorded (Zoom recommended, or privately listed on YouTube). Per the assessment requirements the presenter must appear on camera at the introduction and show their student ID card, then deliver the CVSS analysis and the SIEM demonstration. Insert the recording URL here before submitting:"));
children.push(new Paragraph({ spacing:{after:160}, shading:{type:ShadingType.CLEAR,fill:LIGHT,color:"auto"}, border:{top:{style:BorderStyle.SINGLE,size:2,color:ACCENT},bottom:{style:BorderStyle.SINGLE,size:2,color:ACCENT},left:{style:BorderStyle.SINGLE,size:2,color:ACCENT},right:{style:BorderStyle.SINGLE,size:2,color:ACCENT}}, children:[ run("Presentation recording: ", {bold:true}), run("[ paste your Zoom / YouTube / VoiceThread link here ]", {italics:true, color:"52514E"}) ]}));

children.push(h2("2.11  Conclusion"));
children.push(body([
  run("Log4Shell earns the maximum CVSS Base score of 10.0 because it is a remotely reachable, unauthenticated, low-complexity path to full system compromise, and Temporal and Environmental scoring show why it demanded immediate, prioritised action while remaining an endemic risk. Yet scoring only describes the danger. The SIEM proposed here is the operational answer: by unifying web, network, DNS and endpoint telemetry and correlating it against Log4Shell-specific, ATT&CK-mapped insights, a SOC can see an exploitation attempt as it happens, prioritise the exposed assets the CVSS environmental analysis flagged, and respond before an attempt becomes a breach. Scoring and detection are two halves of the same discipline — know how bad it is, and know when it is happening."),
]));

// References
children.push(new Paragraph({ children:[new PageBreak()] }));
children.push(h1("References"));
children.push(new Paragraph({ spacing:{after:120}, children:[run("IEEE style. In-text citations appear as bracketed numbers, e.g. [2].", {italics:true, size:19, color:"52514E"})] }));
REFS.forEach((r, i) => children.push(refPara(i, r[0])));

// helper defined after use is fine (hoisted function)
function codeBlock(lines) {
  return new Paragraph({ shading:{type:ShadingType.CLEAR,fill:"F4F4F2",color:"auto"},
    spacing:{before:40, after:120, line:240}, indent:{left:160},
    border:{ left:{style:BorderStyle.SINGLE,size:20,color:ACCENT}, top:{style:BorderStyle.SINGLE,size:2,color:RULE}, bottom:{style:BorderStyle.SINGLE,size:2,color:RULE}, right:{style:BorderStyle.SINGLE,size:2,color:RULE} },
    children: lines.flatMap((l, i) => i===0 ? [mono(l)] : [ new TextRun({ break:1 }), mono(l) ]) });
}

// ---- assemble ---------------------------------------------------------
const doc = new Document({
  creator: "Kismat Acharya",
  title: "Log4Shell CVSS analysis and SIEM proposal",
  description: "COMP2004 Assessment 2",
  styles: { default: {
    document: { run: { font: FONT, size: 22, color: INK } },
  }, paragraphStyles: [
    { id:"Heading1", name:"Heading 1", basedOn:"Normal", next:"Normal", quickFormat:true, run:{ font:FONT } },
    { id:"Heading2", name:"Heading 2", basedOn:"Normal", next:"Normal", quickFormat:true, run:{ font:FONT } },
    { id:"Heading3", name:"Heading 3", basedOn:"Normal", next:"Normal", quickFormat:true, run:{ font:FONT } },
  ] },
  numbering: { config: [
    { reference:"bullets", levels:[
      { level:0, format:LevelFormat.BULLET, text:"•", alignment:AlignmentType.LEFT, style:{ paragraph:{ indent:{ left:360, hanging:220 } } } },
      { level:1, format:LevelFormat.BULLET, text:"◦", alignment:AlignmentType.LEFT, style:{ paragraph:{ indent:{ left:720, hanging:220 } } } },
    ]},
    { reference:"steps", levels:[
      { level:0, format:LevelFormat.DECIMAL, text:"%1.", alignment:AlignmentType.LEFT, style:{ paragraph:{ indent:{ left:400, hanging:260 } } } },
    ]},
  ] },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top:1440, bottom:1440, left:1440, right:1440 } } },
    headers: { default: new Header({ children: [ new Paragraph({ alignment:AlignmentType.RIGHT, border:{bottom:{style:BorderStyle.SINGLE,size:4,color:RULE,space:4}}, children:[ run("COMP2004 — Log4Shell CVSS & SIEM", { size:16, color:"8A8984" }) ] }) ] }) },
    footers: { default: new Footer({ children: [ new Paragraph({ alignment:AlignmentType.CENTER, children:[ run("Page ", {size:16,color:"8A8984"}), new TextRun({ children:[PageNumber.CURRENT], size:16, color:"8A8984", font:FONT }), run(" of ", {size:16,color:"8A8984"}), new TextRun({ children:[PageNumber.TOTAL_PAGES], size:16, color:"8A8984", font:FONT }) ] }) ] }) },
    children,
  }],
});

Packer.toBuffer(doc).then(buf => { fs.writeFileSync(OUT, buf); console.log("wrote", OUT, buf.length, "bytes"); });
