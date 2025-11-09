# CS-499 Milestone One — Code Review (CS-340)

**Artifact:** `mod7_project2/animal_shelter.py`  
**Scope:** Single file only (no other files changed in M1)  
**Baseline tag:** `v-before-review`  
**Plan branch:** `enhancement/m1-plan`

---

## Quick links
- Before tag: https://github.com/i-ekoul/CS340-Animal-Shelter-Dashboard/releases/tag/v-before-review
- Enhancement branch: https://github.com/i-ekoul/CS340-Animal-Shelter-Dashboard/tree/enhancement/m1-plan
- Plan (docs/plan.md): https://github.com/i-ekoul/CS340-Animal-Shelter-Dashboard/blob/enhancement/m1-plan/docs/plan.md
- Checklist (docs/checklist.md): https://github.com/i-ekoul/CS340-Animal-Shelter-Dashboard/blob/enhancement/m1-plan/docs/checklist.md

---

## What this video will show (M1)
1. Open the **before tag** and show `animal_shelter.py` (hot query highlighted).
2. Summarize the enhancement:
   - Ensure a single compound index for the hot path.
   - Return structured errors (`code`, `message`) without leaking driver traces.
   - Add tiny in-file input helpers (status enum, date coercion).
3. Open `docs/checklist.md` to show what will be verified in M2 (`explain()` capture).
4. Close with outcomes (CO3, CO2, CO4, CO5).

---

## Outcomes mapping
- **CO3 (Design/Engineering):** localized index ensure and input guards in one DAO file.
- **CO2 (Algorithms/Reasoning):** index selection tied to filter + sort shape.
- **CO4 (Assessment):** planned `explain()` comparison of plan stages.
- **CO5 (Policies/Docs):** structured, user-safe errors; explicit input constraints.

---

## Submission checklist
- [ ] `v-before-review` exists and opens to `animal_shelter.py`.
- [ ] Branch `enhancement/m1-plan` has `docs/plan.md` and `docs/checklist.md`.
- [ ] `README_M1.md` committed on `enhancement/m1-plan`.
- [ ] MP4 recorded following “What this video will show.”
