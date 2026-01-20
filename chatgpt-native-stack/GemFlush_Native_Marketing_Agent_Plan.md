# GemFlush Native Marketing Agent Plan

## Purpose

This document is designed to be **read and executed by Cursor AI in agentic mode**. It defines a *native-first, metric-driven marketing stack* for **gemflush.com**, prioritizing cold email (Apollo) while keeping human setup minimal and avoiding custom code unless explicitly required.

---

## Operating Assumptions

* User operates primarily as a **solo founder**
* Preference for **native SaaS tools** over custom infrastructure
* Cursor AI may:

  * Open browser tabs
  * Draft copy
  * Generate assets
  * Prepare automation instructions
* Cursor AI **cannot create accounts or accept ToS** — user will approve manually

---

## Stack Overview (Authoritative)

### 1. Strategy & Messaging (Native)

**Tool:** ChatGPT (built-in)

**Outputs:**

* ICP definitions
* Persona-specific value propositions
* Messaging pillars

**Primary Metrics:**

* Persona-level reply rate
* Persona-level CTR

---

### 2. Cold Email Lead Source (Semi-Native)

**Tool:** Apollo.io

**Role:**

* Prospect discovery
* Contact enrichment
* Email sequencing

**Primary Metrics:**

* Open rate
* Reply rate
* Positive reply rate

**Cursor Tasks:**

* Draft Apollo filters
* Draft Apollo sequence copy
* Draft personalization tokens

---

### 3. Email Copy Generation (Native)

**Tool:** ChatGPT

**Outputs:**

* Cold email sequences (3–5 steps)
* Subject line variants
* Reply handling templates

**Primary Metrics:**

* A/B subject performance
* CTA click-through

---

### 4. Visual + Social Assets (Native)

**Tool:** Canva (ChatGPT App)

**Outputs:**

* Instagram carousels
* Explainer graphics
* Quote cards

**Primary Metrics:**

* Engagement rate
* Saves / shares

---

### 5. Distribution (Human-in-the-Loop)

| Channel    | Tool                      | Notes             |
| ---------- | ------------------------- | ----------------- |
| Cold Email | Apollo.io                 | Primary channel   |
| Instagram  | Manual / Native Scheduler | Secondary channel |
| LinkedIn   | Manual posting            | Optional          |

---

### 6. Metrics & Optimization (Native)

**Tool:** ChatGPT

**Inputs:**

* Exported Apollo stats
* Social engagement metrics

**Outputs:**

* Weekly performance summaries
* Copy improvement recommendations
* Persona pruning suggestions

---

## Cursor Execution Instructions

### Phase 1 — Strategy Generation

1. Ask ChatGPT to generate 3 ICPs for gemflush.com
2. Produce persona-specific pain points and value framing

### Phase 2 — Cold Email Assembly

1. Draft Apollo search filters for each ICP
2. Generate 3-email sequence per ICP
3. Generate 5 subject lines per sequence

### Phase 3 — Asset Creation

1. Generate 10 Instagram captions
2. Generate 5 Canva carousel concepts

### Phase 4 — Metrics Loop

1. Define baseline KPIs
2. Create weekly review prompt
3. Define kill/scale thresholds

---

## KPI Definitions

| Metric               | Target |
| -------------------- | ------ |
| Email Open Rate      | >40%   |
| Email Reply Rate     | >5%    |
| Positive Reply Rate  | >1.5%  |
| Instagram Engagement | >3%    |

---

## Explicit Non-Goals

* No custom backend
* No direct API scripting
* No automatic account creation

---

## Next Optional Upgrade (NOT REQUIRED)

* Zapier bridge Apollo → CRM
* Automated reporting

---

## Instruction to Cursor

> Treat this file as authoritative. Execute sequentially. Ask for human confirmation only where credentials, ToS, or payments are required.

---

**End of File**
