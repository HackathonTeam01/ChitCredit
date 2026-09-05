import { describe, expect, it } from "vitest";
import request from "supertest";
import app from "../../src/app.js";

describe("C product and integration APIs", () => {
  it("calculates a reserve and returns the auto-payment contract", async () => {
    const response = await request(app).post("/smoothing/reserve").send({
      daily_earnings: [1000, 800, 1200],
      amount_due: 400,
      dates: ["2026-09-01", "2026-09-02", "2026-09-03"],
    });

    expect(response.status).toBe(200);
    expect(response.body.days).toHaveLength(3);
    expect(response.body.target_reached_date).toBe("2026-09-03");
    expect(response.body.auto_payment.source).toBe("savings_wallet");
  });

  it("shrinks repayment during a slow period and never over-collects", async () => {
    const response = await request(app).post("/repayment/simulate").send({
      daily_earnings: [1000, 1000, 1000, 1000, 1000, 1000, 1000, 100],
      loan_balance: 1000,
      deduction_pct: 0.1,
    });

    expect(response.status).toBe(200);
    expect(response.body.schedule[7].deduction_pct).toBe(0.05);
    expect(response.body.remaining_balance).toBeGreaterThanOrEqual(0);
  });

  it("rejects negative earnings instead of returning unsafe financial values", async () => {
    const response = await request(app).post("/repayment/simulate").send({
      daily_earnings: [-1],
      loan_balance: 1000,
    });

    expect(response.status).toBe(400);
    expect(response.body.error).toContain("non-negative");
  });

  it("supports the documented GET forecast contract", async () => {
    const response = await request(app).get("/member/1/forecast").query({
      earnings: "100,90,80,70,60,50,40,30",
      window: 3,
    });

    expect(response.status).toBe(200);
    expect(response.body.slow_period_predicted).toBe(true);
    expect(response.body.declining_windows).toBeGreaterThanOrEqual(3);
  });
});
