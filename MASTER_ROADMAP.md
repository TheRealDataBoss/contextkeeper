# ContextKeeper Master Build Roadmap

**Author:** Steven Wazlavek | Originami
**AI Collaboration:** Claude (Anthropic)
**Version:** 1.0 | April 2026
**Full Document:** ContextKeeper_Master_Roadmap.docx (in this repo)

---

## Current Sprint: Sprint 1 -- Stability and Critical Bug Fixes

### Active Tasks
- [ ] S1-01: Fix Analytics charts (Flame Timeline, Cost Waterfall, Token Sankey, Radar, Gauge, Latency, Leaderboard, Run Comparison, Trace Tree, AI Insight Cards)
- [ ] S1-02: Fix Data Canvas dragged nodes rendering blank (node data shape mismatch)
- [ ] S1-03: Verify right panel all tabs on both canvases
- [ ] S1-04: Verify auto-expand sections post-run

---

## Sprint Order

| Sprint | Focus | Key Deliverable |
|--------|-------|----------------|
| 1 | Stability | All bugs fixed, platform verified |
| 2 | KaTeX + Streamdown | Math rendering, formatted output |
| 3 | First-Run Experience | Guided demo, code splitting |
| 4 | Connectors 1-20 | Live data in pipelines |
| 5 | Evaluation Features | Model tournament, Pareto frontier |
| 6 | Notebook Port | 15,403 lines ported |
| 7 | Fine-Tuning Pipeline | Unsloth QLoRA on RTX 4070 |
| 8 | Novel Features | 15 features no competitor has |
| 9 | Observability | Production monitoring |
| 10 | IDE + Terminal | Full dev environment |
| 11 | Node Expansion | DSPy, advanced RAG, safety nodes |
| 12 | Connectors 21-50 | Full connector library |
| 13 | Polish + Performance | Release preparation |

---

## Build Protocol
- PowerShell only (Windows) -- never bash
- TypeScript strict -- zero errors before every commit
- Observatory design system on every surface
- Full builds only -- no minimal implementations
- Every session: read STATE_VECTOR.json first, update it last

## Backend Start Command
```powershell
cd C:\Users\Steven\contextkeeper-platform\backend
python -m uvicorn app.main:app --reload --port 8000
```
