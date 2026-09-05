# Chit Credit

React + Tailwind frontend for Chit Credit, an alternative credit signal for gig and informal workers.

## Run

```bash
npm install
npm run dev
```

Set `VITE_API_BASE_URL` from `.env.example` when Member A's backend is available. The frontend calls:

- `GET /member/:id/score`
- `GET /member/:id/history`
- `GET /member/:id/credit-offer`
- `GET /group/:id/members`

The smoothing chart expects Member C's fixed output contract as a prop: a running wallet balance array plus the date the target was reached. The frontend does not calculate or rename that contract. The repayment simulator applies `min(dailyEarning * deductionPct, remainingBalance)`.

## Wireframe

### Member dashboard

1. Navy navigation with member/operator switching and language toggle.
2. Greeting and member identifier.
3. Score hero with tier badge, wallet balance, next contribution, and consistency summary.
4. Smoothing chart with raw earnings, wallet balance, and dashed contribution target.
5. Notification feed and contribution history.
6. Elastic repayment simulator.

### Operator dashboard

1. Navy navigation.
2. Group health summary: active members, collection rate, and attention flags.
3. Member table with score, tier, and missed-payment flags.
4. Group pulse chart.

## Contract note

The C product endpoints are:

- `POST /smoothing/reserve` for the variable reserve wallet contract.
- `POST /repayment/simulate` for elastic repayment schedules.
- `GET /member/:id/forecast?earnings=420,280,...` for the optional slow-period forecast.

Payment confirmation posts to `/contribution`; the API response's `auto_payment_event` drives the notification feed. Set `VITE_API_BASE_URL` to the running backend URL for the integrated demo.
