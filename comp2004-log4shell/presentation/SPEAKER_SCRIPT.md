# Speaker script — Log4Shell CVSS & SIEM (COMP2004)

Recording checklist: Zoom (or privately-listed YouTube). Camera **on** at the introduction; show your **student ID**. Introduce yourself, then present. Est. 10–12 min.

## Slide 1: The Log4ShellVulnerability

Good morning. I'm presenting a SOC analyst's view of Log4Shell — CVE-2021-44228 — the Apache Log4j flaw disclosed in December 2021. The brief has two parts: first I score the vulnerability using CVSS to show exactly how dangerous it is and where to prioritise; then I propose a SIEM deployment and demonstrate how it detects an exploitation attempt end to end. Aim for about ten to twelve minutes.

## Slide 2: What this brief covers

Two parts. Task one is the CVSS analysis: I'll explain the flaw, derive its base score of ten out of ten, then layer on temporal and environmental context and compare the three CVSS versions. Task two is the SIEM proposal: why a SIEM is the right tool here, the architecture and the log sources it needs, four layered detection use cases, and a walkthrough of the recorded demo.

## Slide 3: A logging library that runs code hidden inside the data it logs

Here is the flaw in one sentence: Log4j is a logging library that could run code hidden inside the very data it was asked to log. Log4j 2 supported "lookups" — the dollar-brace-jndi syntax on screen. In vulnerable versions it expanded that expression even when it arrived as untrusted input. So an attacker just had to get this string logged — in an HTTP header, a form field, a username — and the server would reach out to an attacker-controlled server, download a Java class and execute it. That's unauthenticated remote code execution. It's catalogued as CVE-2021-44228, weakness class CWE-917 expression injection, and it maps to ATT&CK technique T1190, exploiting a public-facing application.

## Slide 4: Five steps &#8212; and the server does most of them itself

The attack has five steps, and the important thing is who performs them. In red, the attacker only controls two: crafting the input, and standing up the malicious directory server. Everything in blue — logging the string, making the outbound lookup, and executing the code — the victim's own server does. That's what makes it so dangerous: the server attacks itself. But notice the flip side, at the bottom: steps two, three and five all happen inside your infrastructure, which means your logs can see them. Hold that thought for Task two.

## Slide 5: One of the most serious vulnerabilities in history

Why did this matter so much? Three numbers. Over thirty-five thousand Java packages were affected — more than eight percent of the entire Maven Central repository — and most were affected indirectly, through dependencies teams didn't even know they had. Weaponised exploit code and mass scanning appeared within a day of disclosure. And the US Cyber Safety Review Board later called it an "endemic" vulnerability, expected to be exploited into the 2030s. The CISA director called it one of the most serious vulnerabilities of her career. So the scale was enormous and patching alone was never going to be enough — which is the case for investing in detection.

## Slide 6: A power company running Java deep in its control systems

Here's our specific scenario, and it's what makes this analysis more than a textbook exercise. We're a power company, and four of our assets use Java or embed Log4j. The SIMATIC IT Report Manager, a Java reporting product that sits on the IT-OT boundary and is network-reachable. The OPC UA Java Stack, buried deep in the SCADA and EMS core that talks to our controllers. And the Siemens Connect X200 and X300 telecontrol gateways out at our substations. The critical point is at the bottom: a compromise of these isn't a data breach, it's loss of view and control over physical grid equipment. Integrity and availability here have safety consequences. That reasoning drives every CVSS environmental score and every SIEM choice I'm about to make.

## Slide 7: It is not one CVE &#8212; it is a family, and patches created new ones

Before scoring, the rubric asks me to comprehensively identify the vulnerabilities — and the important insight is that Log4Shell isn't one CVE, it's a family, and the rushed patches actually created new ones. I scored all four myself. 44228, the original, is my ten out of ten. But 45046 — the first fix, 2.15.0, turned out to be incomplete, and it's still remote code execution, which I scored 9.0, Critical, the higher complexity pulling it just below ten. 45105 is a denial-of-service through recursive lookups, 5.9 Medium. And 44832 is another RCE but it needs the attacker to control configuration, so 6.6 Medium. The practical lesson, at the bottom: for our Siemens assets, the finish line is 2.17.1, not 2.15.0 — and each product has to be checked against Siemens ProductCERT advisories.

## Slide 8: Scoring it with CVSS

On to Task one. CVSS — the Common Vulnerability Scoring System, maintained by FIRST — is the industry standard for expressing how severe a vulnerability is, on a scale of zero to ten. It has three metric groups. Base captures the intrinsic qualities of the flaw and is the same for everyone. Temporal adjusts for how the threat evolves over time — is there working exploit code, is there a patch. And Environmental tailors the score to your specific deployment. I'll work through all three for Log4Shell.

## Slide 9: Every metric, justified from how it works

Now the core of Task one — and I want to stress this is my own determination, justified metric by metric, not a copied number. Attack Vector is Network: the payload arrives over the network. Attack Complexity is Low: one request works, reliably. Privileges Required, None — no login. User Interaction, None — logging is automatic. Scope is Changed, and this is the key one: the flaw breaks out of the logging library to compromise the whole host, so it crosses a security boundary. And Confidentiality, Integrity and Availability are all High because arbitrary code execution means total loss on all three. Put together, both halves of the equation max out, and the base score is a perfect ten out of ten — Critical. There's the vector string.

## Slide 10: How the threat looked in December 2021

Temporal metrics adjust for how the threat evolved, and I set three. Exploit Code Maturity: High — weaponised exploits and mass scanning appeared within a day. Remediation Level: Official Fix — Apache shipped a patch, and this is the only factor pulling the score down at all. Report Confidence: Confirmed — vendor-confirmed and reproduced everywhere. That gives 9.5, still Critical. And the key point in the string at the bottom: in the first days, before any patch existed, Remediation Level would be Unavailable, and the temporal score would sit at the full ten. The most dangerous window is always before the fix.

## Slide 11: Same flaw, three of our assets, three priorities

This is where context earns its keep. Environmental scoring lets me re-score the same flaw for each of our assets, and I made a deliberate choice: for all three I set Integrity Requirement and Availability Requirement to High, because corrupted control data or lost availability threatens the grid itself. What differs is reachability. The SIMATIC Report Manager is exposed at the IT-OT boundary with no mitigation — it stays 9.5, Critical, so it's fixed first. The Connect gateways are remotely reachable but hardened, so I set Modified Attack Complexity High — 8.7. The OPC UA stack is deep in segmented OT, only adjacent-reachable, so Modified Attack Vector Adjacent plus complexity High — 8.0. And the lesson at the bottom is the whole point of doing this in an OT context: you cannot deprioritise an OT asset the way you might a low-value IT box, because the high integrity and availability requirements keep everything at least High.

## Slide 12: One flaw, every version and metric group

Here's the whole analysis on one chart, and it also shows why the CVSS version matters. Under the old version two, the same flaw scores 9.3 — because version two had no Scope metric, it couldn't capture the break-out, so it can't reach ten. Version 3.1, which I based my analysis on, adds Scope and gives the full ten. Version 4.0 restructures impact into vulnerable-system and subsequent-system metrics and still lands at ten. In the middle you can see our three environmental scores spreading from 9.5 down to 8.0. The takeaway on the right: always cite which version a score came from, because the same flaw reads anywhere from 9.3 to 10 depending on it.

## Slide 13: Why a SIEM &#8212; and which one for us

On to Task two, the SIEM. First, why a SIEM at all? Because no single log proves Log4Shell. The web log shows the payload string, the firewall shows the strange outbound LDAP connection, the OT sensor shows a gateway behaving oddly — individually easy to dismiss. The SIEM is the one place those weak signals line up, on one asset, within seconds. And which SIEM in our context? I'm proposing Splunk Enterprise Security — it has risk-based alerting, published Log4Shell detections and ATT&CK mapping, and an OT add-on — and I'll note the demo reproduces it for free with Wazuh or Elastic. Crucially, I pair it with a passive OT monitoring sensor like Nozomi or Claroty, because you cannot install endpoint agents on controllers or the Siemens gateways — the sensor watches the network and feeds the SIEM.

## Slide 14: From IT and OT log sources to SOC action

Here's the reference architecture. Four stages, left to right. Diverse log sources — and note these span both IT and OT: the DMZ web logs from the SIMATIC Report Manager, the IT-OT boundary firewall, DNS, and the OT side — Connect gateway syslog, OPC UA, the historian. Those feed lightweight collectors, which forward over encrypted transport to the SIEM. The SIEM parses and normalises everything, correlates it against Log4Shell use cases, and enriches it with threat intel and asset context — including which Purdue zone an asset sits in. The outputs drive the SOC: triage, automated response, dashboards, incident response and compliance. The next three slides drill into exactly what this pipeline needs — its inputs, its insights, and its actions.

## Slide 15: What must we ingest &#8212; and why

The rubric asks me to individually identify the SIEM inputs and justify each in the context of this incident. Six. Web and application logs from the SIMATIC Report Manager and our Java apps — because the JNDI payload lands here first, in URLs, headers, form fields. The IT-OT boundary firewall and proxy — because a server, especially an OT box, making an outbound LDAP or RMI connection is the exploitation tell; it should never do that. DNS logs — because the JNDI callback resolves an attacker or canary domain, and that's visible even if the inbound request was encrypted. OT telemetry — the Connect gateway syslog, OPC UA and the historian, fed by a passive sensor where no agent can run. Endpoint telemetry — Java spawning a shell is proof an attempt worked. And the vulnerability-scan and SBOM inventory — because knowing which assets actually run vulnerable Log4j is what turns a noisy alert into a prioritised one.

## Slide 16: What must it detect &#8212; and why

Second, the insights — what the SIEM must detect, and these are layered on purpose. Signatures catch the noisy scanning; behavioural rules catch the quiet attacker who evades the string but still has to call out or execute. Insight one: the inbound JNDI payload and its encodings in web traffic — that catches the mass exploitation, ATT&CK T1190. Insight two, behavioural: a Java server or an OT gateway making an outbound LDAP or RMI connection to those ports — almost never legitimate, especially in OT. Insight three is the flagship and it's why we need a SIEM specifically: correlating the two — the same host receives a payload and then calls out within minutes — two weak signals combine into one high-confidence alert with very few false positives. And insight four: post-exploitation — Java spawning a shell or a downloader, which is the trigger to isolate. Each is mapped to an ATT&CK technique so analysts get consistent context.

## Slide 17: What must it do &#8212; and why

Third, the actions — and the OT context changes these more than anything. In OT, automation has to be safety-gated: you block at the IT-OT boundary, but you never automatically isolate a live controller, because pulling a device offline could itself cause an outage. A human confirms before anything touches the grid. So: Contain — SOAR blocks the source IP at the boundary and denies the outbound callback, and it isolates IT hosts automatically but only quarantines OT with operator sign-off. Enrich and prioritise — cross-check the SBOM to confirm the asset is actually vulnerable, attach the CVSS environmental score and Purdue zone, and auto-raise severity for that exposed SIMATIC box. And Respond and report — open an incident ticket, notify both on-call and OT engineers, retrospectively hunt stored logs for earlier attempts, and keep the evidence trail for NIST 800-61 and the audit that prompted this review.

## Slide 18: Detecting an attempt, end to end

Now the demonstration itself, which I'll walk through in the recording. It runs entirely in an isolated lab — a deliberately vulnerable Java service, an attacker host, and a free SIEM, using documentation IP ranges and reserved domains, so nothing live is ever touched. Five steps. One: establish a quiet baseline. Two: send the JNDI payload in an HTTP header. Three: the signature detection, insight one, fires within seconds — I open it and show the offending request. Four: the vulnerable server makes its outbound callback, and the correlated alert, insight three, ties payload to callback on the same host. Five: I walk the analyst response — triage, confirm the asset is vulnerable via the SBOM, and run the SOAR playbook. As required, the recording will be on Zoom with my camera on and my student ID shown, and the link goes in with the submission.

## Slide 19: What the SIEM gives us &#8212; and its limits

An honest appraisal, because the argument for the SIEM has to acknowledge its limits. The benefits: cross-source correlation that no single tool can do; lower mean time to detect and respond, plus the ability to hunt stored logs retrospectively; threat-intel enrichment from feeds like CISA KEV and Siemens ProductCERT; and an audit trail — which matters, since this whole exercise came out of a security audit. The limits, each with our mitigation: a SIEM only sees what it ingests, so we need an onboarding checklist tied to the asset inventory; signature rules are noisy, so we lean on risk-based and correlated alerting; encryption can hide the payload, so we rely on behavioural detections; and we can't put agents on OT devices, so we feed the SIEM from a passive network sensor. None of these is a reason not to deploy — they're design requirements.

## Slide 20: Three things to take away

To close, three takeaways. First, Log4Shell is a maximal ten out of ten — but not everywhere equally, and the environmental scoring, from 9.5 down to 8.0, is exactly how we sequence remediation across our OT estate. Second, patching alone was never enough: it's a family of CVEs, buried in the software supply chain and in OT firmware, so detection has to run alongside remediation. And third, the SIEM is what makes that detection real — with the right inputs, correlated insights and safety-gated actions, it turns three weak signals into one high-confidence alert, and lets us see an attempt before it becomes a grid incident. Thank you — I'll take any questions.

## Slide 21: Selected sources

Finally, my references, in IEEE style — the CVSS specifications from FIRST, the NVD and CVE records, CISA and the Cyber Safety Review Board, the Australian ACSC advisory, Siemens ProductCERT, and the Splunk and Wazuh detection guidance I drew the use cases from. The full list with URLs is in the accompanying report. Thank you.
