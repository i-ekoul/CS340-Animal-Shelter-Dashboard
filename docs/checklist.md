# Code Review Checklist (CS-340, animal_shelter.py)

> Scope: **one file** — `mod7_project2/animal_shelter.py`  
> Baseline: `v-before-review` tag

---

## A) Structure & Boundaries
- [ ] DAO functions live here; no scattered ad-hoc DB calls
- [ ] Input normalization/validation occurs **before** DB writes/queries

**Before (notes):** Validation mixed with DB ops; some normalization absent.

---

## B) Integrity & Inputs
- [ ] `status` limited to a small enum (documented)
- [ ] `intake_date` coerced to a consistent date type
- [ ] Optional phone-like fields normalized (digits only), if used

**Before (notes):** Types/enums not consistently enforced here.

---

## C) Hot Query Performance
- [ ] Compound index ensured: `{ status:1, animal_type:1, intake_date:-1 }`
- [ ] Query code sorts by `intake_date:-1` to match index order

**Before (notes):** Sort may be in memory without index; order not guaranteed.

---

## D) Error Semantics
- [ ] Returns small dicts with `code` and short `message` (no raw stack traces)
- [ ] Distinguish `VALIDATION_FAILED`, `NOT_FOUND`, `CONFLICT`, `DB_ERROR`

**Before (notes):** Errors not consistently structured.

---

## E) Evidence Plan (M2)
- [ ] Save one `explain()` JSON (or screenshot) for the hot query **before/after** index ensure
- [ ] Brief note on whether a sort stage remains and what plan is chosen
## Rubric Mapping
- **CO3** bounded DAO & validation · **CO2** index matches query shape · **CO4** planned `explain()` check · **CO5** structured, user-safe error model
