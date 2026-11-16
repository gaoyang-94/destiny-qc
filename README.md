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

## What Kane caught (real findings, not a staged demo)

Both findings below came from actual runs on a production Next.js app; each has a sealed
evidence pack and a code commit behind it.

1. **Report info bar silently dropped 四柱.** The generator emitted four of the five
   required birth-info items. Kane's preview flow caught it on the rendered page
   (`The report header does not show all five required pieces of birth information`),
   the fix agent read that verdict, rewrote the report, and the re-run exposed a second
   issue (body under the 2000-character floor) before going green on round 3.
2. **The web chart's centre cell was missing 四柱 / 命主 / 身主** even though the PNG
   renderer already showed them. Kane's 7-step journey test failed only at the
   centre-cell assertion (`The chart rendered its 12-palace layout, but the center cell
   did not provide all of the required chart details`). We fixed the component, rebuilt,
   and the same test then passed 7/7.
3. The suite also caught **its own ambiguity**: Kane's bug verdict classified one failure
   as `automation_bug / agent_misstep` because the step text let 命宫/身宫 stand in for
   命主/身主. The step was rewritten to assert the two rows separately — a nice example
   of the verification layer auditing the spec, not just the app.

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

Video (3:15): `demo/destiny-qc-demo.mp4` — one planted defect, two Kane failures with root
causes, agent fixes, one green run, then the same rig finding a real bug in the product.

Launch posts:
- https://x.com/chuchouji/status/2122208447928336846
- https://x.com/chuchouji/status/2122209668256977379
