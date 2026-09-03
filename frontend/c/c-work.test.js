import test from 'node:test'
import assert from 'node:assert/strict'
import { calculateSmoothingReserve } from './incomeSmoothing.js'
import { calculateElasticRepayment } from './elasticRepayment.js'
import { createAutoPayNotification, notificationsForSmoothing } from './notificationFeed.js'

test('smoothing builds a capped wallet and records the first target date', () => {
  const result = calculateSmoothingReserve(Array(10).fill(500), { basePct: 0.2, targetAmount: 500, startDate: '2024-08-01' })
  assert.equal(result.targetReachedDate, '2024-08-04')
  assert.equal(result.walletBalances.at(-1).walletBalance, 500)
  assert.equal(result.autoPaidOnDueDate, true)
})

test('smoothing uses a lower reserve percentage on a below-average day', () => {
  const result = calculateSmoothingReserve([800, 800, 100], { basePct: 0.2 })
  assert.equal(result.walletBalances[2].reservePct, 0.15000000000000002)
})

test('repayment never deducts more than the remaining loan balance', () => {
  const result = calculateElasticRepayment([1000, 1000], { loanBalance: 50, deductionPct: 0.1, slowPeriodCheck: false })
  assert.equal(result.schedule[0].deduction, 50)
  assert.equal(result.finalRemainingBalance, 0)
})

test('repayment halves the rate when a slow period is detected', () => {
  const result = calculateElasticRepayment([...Array(7).fill(1000), ...Array(7).fill(700)], { loanBalance: 10000, deductionPct: 0.1 })
  assert.equal(result.slowPeriodPredicted, true)
  assert.equal(result.appliedDeductionPct, 0.05)
})

test('notification is generated only after the wallet reaches its target', () => {
  const noNotification = notificationsForSmoothing({ targetAmount: 500, targetReachedDate: null })
  const notification = notificationsForSmoothing({ targetAmount: 500, targetReachedDate: '2024-08-06' }, { language: 'ta' })
  assert.deepEqual(noNotification, [])
  assert.match(notification[0].message, /சிட்/)
  assert.equal(createAutoPayNotification({ amount: 500, date: '2024-08-06' }).type, 'auto-pay')
})
