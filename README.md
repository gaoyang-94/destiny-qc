# Destiny QC — AI writes the horoscope. Kane grades it.

**Kane CLI Online Hackathon entry (Nov 12–19, 2026).**

A closed-loop quality gate for AI-generated Chinese astrology (Zi Wei Dou Shu) reports.
A content agent writes a report; Kane CLI walks the real product in a real browser and
grades the output against acceptance criteria; on failure the verdict JSON is fed back to
the agent, which fixes the report and resubmits — up to three rounds, then it escalates
to a human.

```
 generate report (agent)
        │
        ▼
 Kane CLI: browser flows + report preview checks ──pass──► ship
        │ fail
        ▼
 verdict JSON (root cause, culprit step, confidence)
        │
        ▼
 agent reads verdict → regenerates the report ──► verify again (≤3 rounds)
```

## Why this exists

LLM content pipelines are open-loop: the model writes, nobody checks. Our astrology
report pipeline (Next.js charting app + report generator) had exactly one quality
standard — a human glancing at the PDF. This project closes the loop: every acceptance
criterion from `prd/report-acceptance.md` is now a browser-verifiable Kane test, and a
failed run produces a machine-readable verdict that the writing agent consumes directly.

## Kane CLI is used three ways

1. **Build partner** — the report generator and the preview page were iterated with
   Kane runs checking each change in a real browser.
2. **Tester** — `tests/` holds authored `*_test.md` flows: the full user journey
   (birth data in → chart renders → 12 palaces visible) plus report acceptance checks
   (info bar fields, section coverage, banned scaffold phrases, length floor).
3. **Runtime gate** — `qc_loop.py` is the shipping gate: no report leaves the pipeline
   without a sealed Kane evidence pack showing green.

## Repo layout

| Path | What it is |
|---|---|
| `prd/report-acceptance.md` | The requirements (source of truth for Kane context) |
| `tests/chart_flow_test.md` | End-to-end user journey on the charting web app |
| `tests/report_preview_test.md` | Report acceptance checks on the rendered report |
| `qc_loop.py` | The closed loop: generate → verify → fix → re-verify |
| `report_gen.py` | The content agent (report generator), DeepSeek-backed |
| `sample_chart.json` | Real chart engine output used as fixture |
| `evidence/` | Sealed Kane evidence packs from the demo runs |

## Quick start

```bash
npm install -g @testmuai/kane-cli
kane-cli login --username "$LT_USERNAME" --access-key "$LT_ACCESS_KEY"
python3 qc_loop.py --demo-seed-defect   # watch Kane catch a planted bug, then watch the fix go green
```

## Demo

Video: (link) — 3 minutes: one planted defect, one Kane failure with root cause, one
agent fix, one green run.
