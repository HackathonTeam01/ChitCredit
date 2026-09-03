const assertValidEarnings = earnings => {
  if (!Array.isArray(earnings) || earnings.length === 0) throw new TypeError('dailyEarnings must be a non-empty array')
  if (earnings.some(value => typeof value !== 'number' || !Number.isFinite(value) || value < 0)) throw new TypeError('dailyEarnings must contain non-negative numbers')
}

export function calculateSmoothingReserve(dailyEarnings, { trailingWindow = 7, basePct = 0.15, targetAmount = 500, startDate = '2024-08-01' } = {}) {
  assertValidEarnings(dailyEarnings)
  if (!Number.isInteger(trailingWindow) || trailingWindow < 1) throw new RangeError('trailingWindow must be a positive integer')
  if (basePct <= 0 || basePct >= 1) throw new RangeError('basePct must be between 0 and 1')
  if (targetAmount <= 0) throw new RangeError('targetAmount must be positive')

  let walletBalance = 0
  let targetReachedDate = null
  const walletBalances = dailyEarnings.map((earning, index) => {
    const previousEarnings = dailyEarnings.slice(Math.max(0, index - trailingWindow), index)
    const trailingAverage = previousEarnings.length === 0
      ? earning
      : previousEarnings.reduce((sum, value) => sum + value, 0) / previousEarnings.length
    const reservePct = index === 0 || earning >= trailingAverage ? basePct * 1.25 : basePct * 0.75
    const reservedAmount = Math.min(earning * reservePct, Math.max(0, targetAmount - walletBalance))
    walletBalance = Math.min(targetAmount, walletBalance + reservedAmount)
    const date = new Date(`${startDate}T00:00:00Z`)
    date.setUTCDate(date.getUTCDate() + index)
    const dateString = date.toISOString().slice(0, 10)
    if (walletBalance >= targetAmount && targetReachedDate === null) targetReachedDate = dateString
    return { date: dateString, earning, trailingAverage: Math.round(trailingAverage * 100) / 100, reservePct, reservedAmount: Math.round(reservedAmount * 100) / 100, walletBalance: Math.round(walletBalance * 100) / 100 }
  })

  return { targetAmount, walletBalances, targetReachedDate, autoPaidOnDueDate: targetReachedDate !== null }
}
