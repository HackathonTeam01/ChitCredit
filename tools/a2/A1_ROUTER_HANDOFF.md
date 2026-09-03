# A2 Router Integration & Handoff Specification

This document defines the integration interface for Person A1 to mount the A2 Credit Scoring and Credit Offer API routes into the root backend application.

---

## 1. Module Path and Export

- **Module Path:** `backend.a2.api.routes` (or `backend.a2.api`)
- **Exported Router Name:** `router` (FastAPI `APIRouter` instance)

```python
from backend.a2.api.routes import router as a2_router
```

---

## 2. Routes Provided

| Method | Path | Description | Query Parameters |
|---|---|---|---|
| `GET` | `/member/{member_id}/score` | Returns canonical Chit Credit Score, tier, and explainable breakdown | `include_breakdown: bool = True` |
| `GET` | `/member/{member_id}/credit-offer` | Returns pre-approved NBFC credit offer based on member score tier | `unlock_date: Optional[str] = None` |

---

## 3. Server Registration Example for Person A1

When Person A1 creates/configures the root application entrypoint (`backend/main.py` or root server), simply mount `a2_router` as follows:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.a2.api.routes import router as a2_router
# from backend.a1.api.routes import router as a1_router (Person A1 router)

app = FastAPI(
    title="Chit Credit Unified API",
    description="Decentralized credit signals and circle intelligence platform",
    version="1.0.0"
)

# Optional CORS for frontend (Person B)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Person A2 routes
app.include_router(a2_router)

# Register Person A1 routes
# app.include_router(a1_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
```

---

## 4. Canonical Response Shapes

### 4.1 Score Response (`contracts/credit/chit_credit_score.schema.json`)
```json
{
  "member_id": "1",
  "on_time_pct": 98.0,
  "streak_count": 10,
  "tenure_cycles": 8,
  "score_value": 85,
  "score_band": "Gold",
  "breakdown": {
    "on_time_component": 98.0,
    "streak_component": 100.0,
    "tenure_component": 80.0,
    "missed_payment_penalty": 0.0,
    "raw_score": 85.0,
    "clamped_score": 85,
    "weights": {
      "w1_on_time": 0.5,
      "w2_streak": 0.2,
      "w3_tenure": 0.2,
      "w4_missed_penalty": 0.1
    },
    "normalization_convention": "Streak & tenure capped at 10 cycles mapped to 0-100; missed penalty at 10 pts per missed payment; clamped to [0, 100]"
  }
}
```

### 4.2 Credit Offer Response (`contracts/credit/credit_offer.schema.json`)
```json
{
  "member_id": "1",
  "eligible_amount": 30000.0,
  "interest_rate": 11.0,
  "unlock_date": "2024-08-25",
  "partner_nbfc": "ChitCredit Demo NBFC Partner (Simulated)",
  "is_eligible": true,
  "score_band": "Gold",
  "term_months": 36,
  "disclaimer": "This pre-approved credit offer is a simulated mock calculation for demonstration purposes and does not represent a legally binding credit agreement."
}
```

---

## 5. Tier Mapping Reference

| Tier Band | Score Range | Pre-approved Working Capital | APR (%) | Recommended Term |
|---|---|---|---|---|
| **Gold** | 85 – 100 | ₹30,000 | 11.0% | 36 months |
| **Silver** | 70 – 84 | ₹15,000 | 14.0% | 24 months |
| **Bronze** | 50 – 69 | ₹5,000 | 18.0% | 12 months |
| **Not Yet Eligible** | 0 – 49 | ₹0 | 0.0% | N/A (Ineligible) |

---

## 6. Architecture & DataProvider Extensibility

The A2 architecture uses an abstract `DataProvider` interface (`backend/a2/integration/data_provider.py`).
- **Currently:** Uses `MockDataProvider` (contains 18 demo personas + edge cases).
- **Future A1 Integration:** A1 can pass a database-backed `A1DataProvider` to `ScoreService(data_provider=a1_provider)` and `OfferService(data_provider=a1_provider)` without modifying the underlying scoring formulas or offer logic.

---

## 7. Merge Safety Assurance

- **Zero Root Modifications:** Person A2 has **NOT** modified or created any root entrypoint, shared README, `.gitignore`, or package config files.
- **Strict Path Isolation:** All A2 implementation resides strictly in `backend/a2/**`, `contracts/credit/**`, `tests/a2/**`, `scripts/credit/**`, and `tools/a2/**`.
- **Zero File Copying:** Person A1 should import `a2_router` directly and does not need to duplicate or copy any A2 files.

