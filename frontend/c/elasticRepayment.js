const validateEarnings = earnings => {
  if (!Array.isArray(earnings) || earnings.some(value => typeof value !== 'number' || !Number.isFinite(value) || value < 0)) throw new TypeError('dailyEarnings must contain non-negative numbers')
}

export function calculateElasticRepayment(dailyEarnings, { loanBalance, deductionPct = 0.10, slowPeriodCheck = true } = {}) {
  validateEarnings(dailyEarnings)
  if (!Number.isFinite(loanBalance) || loanBalance < 0) throw new RangeError('loanBalance must be non-negative')
  if (deductionPct <= 0 || deductionPct > 1) throw new RangeError('deductionPct must be between 0 and 1')

  const recent = dailyEarnings.slice(-7)
  const prior = dailyEarnings.slice(-14, -7)
  const recentAverage = recent.length ? recent.reduce((sum, value) => sum + value, 0) / recent.length : 0
  const priorAverage = prior.length ? prior.reduce((sum, value) => sum + value, 0) / prior.length : recentAverage
  const slowPeriodPredicted = slowPeriodCheck && prior.length >= 3 && recentAverage < priorAverage * 0.85
  const appliedDeductionPct = slowPeriodPredicted ? deductionPct / 2 : deductionPct
  let remainingBalance = loanBalance
  const schedule = dailyEarnings.map((earning, index) => {
    const deduction = Math.min(earning * appliedDeductionPct, remainingBalance)
    remainingBalance = Math.max(0, remainingBalance - deduction)
    return { day: index + 1, earning, deductionPct: appliedDeductionPct, deduction: Math.round(deduction * 100) / 100, remainingBalance: Math.round(remainingBalance * 100) / 100 }
  })
  return { loanBalance, requestedDeductionPct: deductionPct, appliedDeductionPct, slowPeriodPredicted, schedule, finalRemainingBalance: remainingBalance }
}
