# Chit Credit C-Part Demo Pack

## One-line pitch

Chit Credit turns daily income volatility into a visible, explainable path to reliable chit payments and fair formal credit.

## Seven-slide outline

1. **The income is real. The credit file is missing.** Informal workers earn daily but lenders see an incomplete story. Chit payments are a trusted behavioral signal.
2. **The insight: consistency beats a snapshot.** A jagged income curve can still fund a steady contribution when reserve behavior adapts to the day.
3. **Three layers, one loop.** Ledger and score create the signal; income smoothing protects the contribution; elastic repayment protects the borrower.
4. **Watch the loop live.** Move from the member dashboard to the reserve chart, then confirm a contribution and show the event notification.
5. **Built for the real ecosystem.** The product is designed around chit operators, QR/UPI collection, and the everyday cash flow of gig and informal workers.
6. **A healthier circle compounds.** On-time contributions improve visibility, liquidity planning, and access to responsibly sized offers.
7. **Close: make the work visible.** Chit Credit does not ask workers to become less volatile; it gives their real behavior a usable financial record.

## Four-minute demo script

- **0:00-0:40, hook:** Show the member dashboard. Say: "A delivery worker can earn ₹200 one day and ₹1,200 the next. The volatility is visible in their life, but invisible in a conventional credit file."
- **0:40-1:30, Layer 1:** Open the score and history. Explain that the score is derived from on-time percentage, streak, tenure, and missed payments, with a visible breakdown rather than a black box.
- **1:30-2:30, Layer 2:** Show the smoothing chart and reserve panel. Move through the earnings curve and point to the wallet target. Explain that good days reserve more and low days reserve less; the target produces an explicit auto-payment-ready event.
- **2:30-3:15, Layer 3:** Move the repayment slider. Show the deduction change with today's earnings and explain that a detected slow period halves the deduction rate instead of forcing a fixed installment.
- **3:15-3:45, anchor:** Switch to the operator view. Show group liquidity, members needing attention, and the contribution event. Connect the product to existing chit collection behavior rather than replacing it.
- **3:45-4:00, close:** "Chit Credit makes daily work legible: a fairer credit signal for the member and a clearer risk picture for the circle."

## Cold-start rehearsal checklist

- Start backend with the real Supabase variables and confirm `GET /health`.
- Start frontend with `VITE_API_BASE_URL` pointing at that backend.
- Open the app in a fresh browser window and verify member login, operator login, and language toggle.
- Confirm reserve and repayment panels show API-backed values, not loading forever.
- Submit one contribution and verify the API response contains `auto_payment_event` and the notification bubble updates.
- Visit `GET /member/1/forecast?earnings=420,280,650,190,780,340,520,610` and confirm the forecast response renders without breaking the chart.
- Rehearse once without pausing. Record any issue, fix only demo-breaking problems, and repeat the cold start.
