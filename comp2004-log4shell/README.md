# COMP2004 Assessment 2 — Log4Shell CVSS analysis & SIEM presentation

SOC-analyst deliverables for the Log4Shell (CVE-2021-44228) assessment, set in the
given **power-company / OT scenario** (SCADA & EMS, SIMATIC IT Report Manager V6.7,
OPC UA Java Stack, Siemens Connect X200/X300 gateways).

> All CVSS metrics, scores and vector strings were **determined and justified
> independently** (computed with the `cvss` library, corroborated against public
> sources) — not copied — per the academic-integrity note in the task sheet.

## What's here

| Path | What it is |
|------|------------|
| `report/KAcharya_COMP2004_Assignment2_2026.docx` | The written report (Task 1 CVSS + Task 2 SIEM), IEEE references, 3 figures.Named for Kismat Acharya. Paste your recording link into §2.10 before submitting. |
| `presentation/KAcharya_COMP2004_Assignment2_Slides_2026.pptx` | **Native, editable PowerPoint** of the 21-slide deck, with speaker notes. Named for Kismat Acharya. Safe Office fonts (Calibri/Consolas). |
| `presentation/` | The slide deck (21 slides) is also published as a Claude Artifact — see the link in the chat. `SPEAKER_SCRIPT.md` compiles every slide's speaker notes for recording. `deck/` holds the artifact slide source. |
| `src/build_report.js`, `src/build_pptx.js` | Node scripts that generate the report (`docx-js`) and the PowerPoint (`pptxgenjs`). |
| `src/figures/` | Figure sources (HTML) + a Playwright renderer (`render.js`) that outputs the PNGs. |

## Task 1 — CVSS (my determinations)

| Scoring | Score | Vector |
|---------|-------|--------|
| CVE-2021-44228 Base (v3.1) | **10.0 Critical** | `AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H` |
| Temporal | 9.5 | `…/E:H/RL:O/RC:C` |
| Env — SIMATIC Report Mgr (exposed) | 9.5 | `…/CR:M/IR:H/AR:H` |
| Env — Connect X200/X300 (hardened remote) | 8.7 | `…/MAC:H` |
| Env — OPC UA stack (deep, segmented) | 8.0 | `…/MAV:A/MAC:H` |
| CVE-2021-45046 / 45105 / 44832 | 9.0 / 5.9 / 6.6 | see report §1.2 |

Cross-version: v2.0 → 9.3, v3.1 → 10.0, v4.0 → 10.0.

## Task 2 — SIEM (Inputs → Insights → Actions)

Splunk Enterprise Security + a passive OT sensor (Nozomi/Claroty), reproducible free
with Wazuh/Elastic. Structured around the three audit questions: the **inputs** to
ingest, the **insights** to detect (four layered, ATT&CK-mapped, correlation-driven),
and the safety-gated **actions** to drive.

## Regenerating

```bash
cd src
NODE_PATH=$(npm root -g) node figures/render.js        # render figure PNGs
NODE_PATH="<docx-install>:$(npm root -g)" node build_report.js   # build the .docx
```

Requires Node with the `docx` and `playwright` packages available on `NODE_PATH`.
CVSS scores were checked with Python's `cvss` package.
