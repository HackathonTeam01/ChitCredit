import { describe, it, expect } from "vitest";
import request from "supertest";
import app from "../../src/app.js";

describe("A2 Credit Scoring & Offer Express API", () => {
  it("GET /member/1/score should return canonical Gold score response", async () => {
    const res = await request(app).get("/member/1/score");

    expect(res.status).toBe(200);
    expect(res.body.member_id).toBe("1");
    expect(res.body.on_time_pct).toBe(98.0);
    expect(res.body.streak_count).toBe(10);
    expect(res.body.tenure_cycles).toBe(8);
    expect(res.body.score_value).toBe(85);
    expect(res.body.score_band).toBe("Gold");
    expect(res.body.breakdown).toBeDefined();
    expect(res.body.breakdown.clamped_score).toBe(85);
    expect(res.body.breakdown.weights.w1_on_time).toBe(0.5);
  });

  it("GET /member/1/score with include_breakdown=false should omit breakdown", async () => {
    const res = await request(app).get("/member/1/score?include_breakdown=false");

    expect(res.status).toBe(200);
    expect(res.body.member_id).toBe("1");
    expect(res.body.score_value).toBe(85);
    expect(res.body.breakdown).toBeUndefined();
  });

  it("GET /member/1/credit-offer should return canonical Gold offer response", async () => {
    const res = await request(app).get("/member/1/credit-offer");

    expect(res.status).toBe(200);
    expect(res.body.member_id).toBe("1");
    expect(res.body.eligible_amount).toBe(30000.0);
    expect(res.body.interest_rate).toBe(11.0);
    expect(res.body.is_eligible).toBe(true);
    expect(res.body.score_band).toBe("Gold");
    expect(res.body.term_months).toBe(36);
    expect(res.body.partner_nbfc).toBe("ChitCredit Demo NBFC Partner (Simulated)");
    expect(res.body.unlock_date).toBeDefined();
    expect(res.body.disclaimer).toBeDefined();
  });

  it("GET /member/1/credit-offer with custom unlock_date", async () => {
    const res = await request(app).get("/member/1/credit-offer?unlock_date=2024-08-25");

    expect(res.status).toBe(200);
    expect(res.body.unlock_date).toBe("2024-08-25");
  });

  it("GET /member/CHT-010/score & offer should yield Silver tier", async () => {
    const scoreRes = await request(app).get("/member/CHT-010/score");
    expect(scoreRes.status).toBe(200);
    expect(scoreRes.body.score_band).toBe("Silver");

    const offerRes = await request(app).get("/member/CHT-010/credit-offer");
    expect(offerRes.status).toBe(200);
    expect(offerRes.body.eligible_amount).toBe(15000.0);
    expect(offerRes.body.interest_rate).toBe(14.0);
    expect(offerRes.body.is_eligible).toBe(true);
    expect(offerRes.body.term_months).toBe(24);
  });

  it("GET /member/CHT-013/score & offer should yield Bronze tier", async () => {
    const scoreRes = await request(app).get("/member/CHT-013/score");
    expect(scoreRes.status).toBe(200);
    expect(scoreRes.body.score_band).toBe("Bronze");

    const offerRes = await request(app).get("/member/CHT-013/credit-offer");
    expect(offerRes.status).toBe(200);
    expect(offerRes.body.eligible_amount).toBe(5000.0);
    expect(offerRes.body.interest_rate).toBe(18.0);
    expect(offerRes.body.is_eligible).toBe(true);
    expect(offerRes.body.term_months).toBe(12);
  });

  it("GET /member/CHT-EMPTY/score & offer should handle empty history gracefully", async () => {
    const scoreRes = await request(app).get("/member/CHT-EMPTY/score");
    expect(scoreRes.status).toBe(200);
    expect(scoreRes.body.score_value).toBe(0);
    expect(scoreRes.body.score_band).toBe("Not Yet Eligible");

    const offerRes = await request(app).get("/member/CHT-EMPTY/credit-offer");
    expect(offerRes.status).toBe(200);
    expect(offerRes.body.eligible_amount).toBe(0.0);
    expect(offerRes.body.interest_rate).toBe(0.0);
    expect(offerRes.body.is_eligible).toBe(false);
  });

  it("GET /member/CHT-INELIGIBLE/score & offer should return Not Yet Eligible", async () => {
    const scoreRes = await request(app).get("/member/CHT-INELIGIBLE/score");
    expect(scoreRes.status).toBe(200);
    expect(scoreRes.body.score_band).toBe("Not Yet Eligible");

    const offerRes = await request(app).get("/member/CHT-INELIGIBLE/credit-offer");
    expect(offerRes.status).toBe(200);
    expect(offerRes.body.eligible_amount).toBe(0.0);
    expect(offerRes.body.is_eligible).toBe(false);
  });

  it("GET /member/NONEXISTENT-999 should return 404 for nonexistent member", async () => {
    const scoreRes = await request(app).get("/member/NONEXISTENT-999/score");
    expect(scoreRes.status).toBe(404);

    const offerRes = await request(app).get("/member/NONEXISTENT-999/credit-offer");
    expect(offerRes.status).toBe(404);
  });

  it("GET /member/%20%20 should return 400 for empty or whitespace-only member ID", async () => {
    const scoreRes = await request(app).get("/member/%20%20/score");
    expect(scoreRes.status).toBe(400);

    const offerRes = await request(app).get("/member/%20%20/credit-offer");
    expect(offerRes.status).toBe(400);
  });

  it("should conform to credit contract required schema fields", async () => {
    const scoreRes = await request(app).get("/member/1/score");
    expect(scoreRes.status).toBe(200);
    const scoreData = scoreRes.body;
    expect(typeof scoreData.member_id).toBe("string");
    expect(typeof scoreData.on_time_pct).toBe("number");
    expect(typeof scoreData.streak_count).toBe("number");
    expect(typeof scoreData.tenure_cycles).toBe("number");
    expect(typeof scoreData.score_value).toBe("number");
    expect(["Not Yet Eligible", "Bronze", "Silver", "Gold"]).toContain(scoreData.score_band);

    const offerRes = await request(app).get("/member/1/credit-offer");
    expect(offerRes.status).toBe(200);
    const offerData = offerRes.body;
    expect(typeof offerData.member_id).toBe("string");
    expect(typeof offerData.eligible_amount).toBe("number");
    expect(typeof offerData.interest_rate).toBe("number");
    expect(typeof offerData.unlock_date).toBe("string");
    expect(typeof offerData.partner_nbfc).toBe("string");
  });
});
