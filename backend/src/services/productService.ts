export interface SmoothingDay {
  date: string;
  daily_earning: number;
  trailing_average: number;
  reserve_pct: number;
  reserve_amount: number;
  wallet_balance: number;
}

export interface SmoothingResult {
  amount_due: number;
  trailing_window: number;
  base_pct: number;
  days: SmoothingDay[];
  target_reached_date: string | null;
  auto_payment: {
    status: "ready";
    date: string;
    amount: number;
    source: "savings_wallet";
  } | null;
}

function assertEarnings(earnings: unknown): number[] {
  if (!Array.isArray(earnings) || earnings.some(value => typeof value !== "number" || !Number.isFinite(value) || value < 0)) {
    throw new Error("daily_earnings must be an array of non-negative numbers");
  }
  return earnings;
}

export function calculateSmoothingReserve(
  dailyEarningsInput: unknown,
  amountDue: number,
  datesInput?: unknown,
  trailingWindow = 7,
  basePct = 0.15,
): SmoothingResult {
  const dailyEarnings = assertEarnings(dailyEarningsInput);
  if (!Number.isFinite(amountDue) || amountDue <= 0) throw new Error("amount_due must be greater than 0");
  if (!Number.isInteger(trailingWindow) || trailingWindow < 1) throw new Error("trailing_window must be at least 1");
  if (!Number.isFinite(basePct) || basePct <= 0 || basePct >= 1) throw new Error("base_pct must be between 0 and 1");

  const dates = datesInput === undefined
    ? dailyEarnings.map((_, index) => String(index + 1))
    : datesInput;
  if (!Array.isArray(dates) || dates.length !== dailyEarnings.length || dates.some(date => typeof date !== "string")) {
    throw new Error("dates must be an array of strings matching daily_earnings");
  }

  let wallet = 0;
  let targetReachedDate: string | null = null;
  const days = dailyEarnings.map((earning, index) => {
    const window = dailyEarnings.slice(Math.max(0, index - trailingWindow + 1), index + 1);
    const trailingAverage = window.reduce((sum, value) => sum + value, 0) / window.length;
    const reservePct = index === 0 ? basePct : earning > trailingAverage ? basePct * 1.25 : basePct * 0.75;
    const reserveAmount = earning * reservePct;
    wallet = Math.min(amountDue, wallet + reserveAmount);
    if (targetReachedDate === null && wallet >= amountDue) targetReachedDate = dates[index];
    return {
      date: dates[index],
      daily_earning: Number(earning.toFixed(2)),
      trailing_average: Number(trailingAverage.toFixed(2)),
      reserve_pct: Number(reservePct.toFixed(4)),
      reserve_amount: Number(reserveAmount.toFixed(2)),
      wallet_balance: Number(wallet.toFixed(2)),
    };
  });

  return {
    amount_due: amountDue,
    trailing_window: trailingWindow,
    base_pct: basePct,
    days,
    target_reached_date: targetReachedDate,
    auto_payment: targetReachedDate ? { status: "ready", date: targetReachedDate, amount: amountDue, source: "savings_wallet" } : null,
  };
}

export interface RepaymentDay {
  day: number;
  daily_earning: number;
  deduction_pct: number;
  deduction_amount: number;
  remaining_balance: number;
  slow_period_predicted: boolean;
}

export function calculateElasticRepayment(
  dailyEarningsInput: unknown,
  loanBalance: number,
  deductionPct = 0.1,
  movingAverageWindow = 7,
) {
  const dailyEarnings = assertEarnings(dailyEarningsInput);
  if (!Number.isFinite(loanBalance) || loanBalance < 0) throw new Error("loan_balance cannot be negative");
  if (!Number.isFinite(deductionPct) || deductionPct <= 0 || deductionPct > 1) throw new Error("deduction_pct must be between 0 and 1");
  if (!Number.isInteger(movingAverageWindow) || movingAverageWindow < 1) throw new Error("moving_average_window must be at least 1");

  let remaining = loanBalance;
  const schedule: RepaymentDay[] = dailyEarnings.map((earning, index) => {
    const previous = dailyEarnings.slice(Math.max(0, index - movingAverageWindow), index);
    const slowPeriodPredicted = previous.length === movingAverageWindow && earning < previous.reduce((sum, value) => sum + value, 0) / previous.length;
    const effectivePct = slowPeriodPredicted ? deductionPct / 2 : deductionPct;
    const deduction = Math.min(earning * effectivePct, remaining);
    remaining = Math.max(0, remaining - deduction);
    return {
      day: index + 1,
      daily_earning: Number(earning.toFixed(2)),
      deduction_pct: Number(effectivePct.toFixed(4)),
      deduction_amount: Number(deduction.toFixed(2)),
      remaining_balance: Number(remaining.toFixed(2)),
      slow_period_predicted: slowPeriodPredicted,
    };
  });
  return { loan_balance: loanBalance, deduction_pct: deductionPct, remaining_balance: Number(remaining.toFixed(2)), paid_off: remaining === 0, schedule };
}

export function calculateForecast(dailyEarningsInput: unknown, window = 7) {
  const dailyEarnings = assertEarnings(dailyEarningsInput);
  if (!Number.isInteger(window) || window < 1) throw new Error("window must be at least 1");
  const movingAverages = dailyEarnings.slice(window - 1).map((_, index) => {
    const values = dailyEarnings.slice(index, index + window);
    return Number((values.reduce((sum, value) => sum + value, 0) / window).toFixed(2));
  });
  const decliningWindows = movingAverages.slice(1).filter((value, index) => value < movingAverages[index]).length;
  return { window, moving_averages: movingAverages, slow_period_predicted: decliningWindows >= 3, declining_windows: decliningWindows };
}
