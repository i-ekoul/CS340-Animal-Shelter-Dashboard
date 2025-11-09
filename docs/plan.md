# Milestone 1 Plan — CS-340 (animal_shelter.py)

**Branch:** `enhancement/m1-plan` | **Before tag:** `v-before-review`  
**Single file in scope:** `mod7_project2/animal_shelter.py` (DAO & queries)

## 1) Current State (file-level review)
- CRUD and query functions reside in `animal_shelter.py` and interact directly with MongoDB.
- Validation occurs primarily in application code; the database accepts malformed documents.
- “Recent adoptables (optionally by type) sorted by `intake_date`” is a hot path; indexing for that shape is not guaranteed here.
- Error messages are inconsistent and not always structured for consumers.

## 2) Gaps (why enhance)
- No **server-enforced** integrity (DB schema) to backstop app validation.
- The hot query can degrade without a supporting **compound index**; sorts may run in memory.
- Errors and inputs are not normalized in a single place in this file.

## 3) Enhancement Plan (single-file; plan only in M1)
**A. Idempotent index ensure (localized in DAO init)**  
Inside `animal_shelter.py`, on initialization, ensure a single **compound index** that matches the hot query:
- `{ status: 1, animal_type: 1, intake_date: -1 }` (background build, ignore if exists).  
This keeps read performance predictable for “recent adoptables (by type)”.

**B. Structured error returns (no raw driver traces)**  
Wrap write/update/delete operations to return a small dict with:
- `code`: `"VALIDATION_FAILED" | "DB_ERROR" | "NOT_FOUND" | "CONFLICT"`  
- `message`: short, user-safe text  
Public callers can still interpret success via truthy/falsey, but we preserve a reason internally.

**C. Input whitelist/coercion (in-file helpers)**  
Add tiny helpers within this file to:
- Coerce `intake_date` to a `datetime` (or ISO string consistently converted),  
- Enforce `status` enum (e.g., `{"adoptable","fostered","hold","adopted"}`),  
- Strip non-digits for phone-like fields if present (document assumption).

**D. Evidence plan (not implemented in M1)**  
- Capture one `explain()` for the hot query **before** and **after** ensuring the index, showing the winning plan and absence of in-memory sort.  
- Record a short note of observed improvement (qualitative is acceptable if dataset is small).

## 4) Outcomes Mapping (CS-499)
- **CO3 (Design/Engineering):** a single, well-bounded DAO file with localized index ensure and input guards.  
- **CO2 (Algorithms/Reasoning):** the compound index is chosen to match filter + sort order (status/type filter; `intake_date` descending).  
- **CO4 (Assessment):** M2 will include `explain()` evidence to verify plan-shape improvements.  
- **CO5 (Policies/Docs):** structured, non-leaky errors; explicit input whitelisting and date coercion.

## 5) Screencast Talking Points (M1)
1. Open `v-before-review` → show `animal_shelter.py` and the hot query path.   
2. State the CO3/CO2/CO4/CO5 mapping.  
