# Member C Work Area

This folder contains the Member C deliverables that can be built before Member A's API is ready. It does not modify the existing React frontend.

## Deliverables

- `incomeSmoothing.js`: reserves a variable percentage of daily earnings and returns the wallet timeline.
- `elasticRepayment.js`: calculates repayment as a percentage of earnings and protects low-income days with an optional slow-period adjustment.
- `notificationFeed.js`: converts a successful smoothing target event into an English or Tamil auto-pay notification.
- `pitch-deck.md`: seven-slide pitch content and speaker notes.
- `demo-script.md`: timed live demonstration script and rehearsal checklist.

## Shared contract for Member A and B

`calculateSmoothingReserve` returns:

```json
{
  "targetAmount": 500,
  "walletBalances": [
    {
      "date": "2024-08-01",
      "earning": 850,
      "trailingAverage": 850,
      "reservePct": 0.1875,
      "reservedAmount": 159.38,
      "walletBalance": 159.38
    }
  ],
  "targetReachedDate": "2024-08-06",
  "autoPaidOnDueDate": true
}
```

The frontend chart can plot `earning` and `walletBalance`; the notification layer should fire only when `targetReachedDate` is present. Member A can wrap this same output in an API response without renaming these fields.

## Run tests

From this folder:

```bash
npm test
```
