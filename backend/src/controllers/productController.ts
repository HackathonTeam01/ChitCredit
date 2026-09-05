import { Request, Response } from "express";
import { calculateElasticRepayment, calculateForecast, calculateSmoothingReserve } from "../services/productService.js";

function handleCalculation(res: Response, calculation: () => unknown) {
  try {
    res.status(200).json(calculation());
  } catch (error) {
    res.status(400).json({ error: error instanceof Error ? error.message : "Invalid calculation input" });
  }
}

export function calculateReserve(req: Request, res: Response) {
  handleCalculation(res, () => calculateSmoothingReserve(
    req.body.daily_earnings,
    req.body.amount_due,
    req.body.dates,
    req.body.trailing_window ?? 7,
    req.body.base_pct ?? 0.15,
  ));
}

export function calculateRepayment(req: Request, res: Response) {
  handleCalculation(res, () => calculateElasticRepayment(
    req.body.daily_earnings,
    req.body.loan_balance,
    req.body.deduction_pct ?? 0.1,
    req.body.moving_average_window ?? 7,
  ));
}

export function calculateMemberForecast(req: Request, res: Response) {
  const earnings = req.body?.daily_earnings ?? (typeof req.query.earnings === "string"
    ? req.query.earnings.split(",").map(Number)
    : undefined);
  const window = req.body?.window ?? (typeof req.query.window === "string" ? Number(req.query.window) : 7);
  handleCalculation(res, () => calculateForecast(earnings, window));
}
