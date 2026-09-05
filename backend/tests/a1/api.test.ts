import { describe, it, expect } from "vitest";
import request from "supertest";
import app from "../../src/app.js";
import { supabase } from "../../src/supabase.js";

describe("A1 Data + Ledger API", () => {
  it("GET /health should return backend health status", async () => {
    const response = await request(app)
      .get("/health");

    expect(response.status).toBe(200);
    expect(response.body.status).toBe("ok");
    expect(response.body.service).toBe("chit-credit-backend");
  });

  it("GET /members should return all 18 seeded members", async () => {
    const response = await request(app)
      .get("/members");

    expect(response.status).toBe(200);
    expect(response.body.count).toBe(18);
    expect(response.body.members).toHaveLength(18);
  });

  it("GET /member/:id should return a valid member", async () => {
    const response = await request(app)
      .get("/member/1");

    expect(response.status).toBe(200);
    expect(response.body.member).toBeDefined();
    expect(response.body.member.member_id).toBe(1);
    expect(response.body.member.name).toBe("Arun Kumar");
  });

  it("GET /member/:id should return 404 for unknown member", async () => {
    const response = await request(app)
      .get("/member/999");

    expect(response.status).toBe(404);
    expect(response.body.error).toBe("Member not found");
  });

  it("GET /member/:id should reject invalid member ID", async () => {
    const response = await request(app)
      .get("/member/abc");

    expect(response.status).toBe(400);
    expect(response.body.error).toBe("Invalid member ID");
  });

  it("GET /group/:id/members should return 6 members for group 101", async () => {
    const response = await request(app)
      .get("/group/101/members");

    expect(response.status).toBe(200);
    expect(response.body.chit_group_id).toBe(101);
    expect(response.body.count).toBe(6);
    expect(response.body.members).toHaveLength(6);
  });

  it("GET /group/:id/members should return 6 members for group 102", async () => {
    const response = await request(app)
      .get("/group/102/members");

    expect(response.status).toBe(200);
    expect(response.body.chit_group_id).toBe(102);
    expect(response.body.count).toBe(6);
    expect(response.body.members).toHaveLength(6);
  });

  it("GET /group/:id/members should return 6 members for group 103", async () => {
    const response = await request(app)
      .get("/group/103/members");

    expect(response.status).toBe(200);
    expect(response.body.chit_group_id).toBe(103);
    expect(response.body.count).toBe(6);
    expect(response.body.members).toHaveLength(6);
  });

  it("GET /group/:id/members should reject invalid group ID", async () => {
    const response = await request(app)
      .get("/group/abc/members");

    expect(response.status).toBe(400);
    expect(response.body.error).toBe("Invalid group ID");
  });

  it("GET /member/:id/history should return contribution history", async () => {
    const response = await request(app)
      .get("/member/1/history");

    expect(response.status).toBe(200);
    expect(response.body.member_id).toBe(1);
    expect(response.body.count).toBeGreaterThan(0);
    expect(response.body.history).toBeInstanceOf(Array);
  });

  it("GET /member/:id/history should return empty history for unknown member", async () => {
    const response = await request(app)
      .get("/member/999/history");

    expect(response.status).toBe(200);
    expect(response.body.member_id).toBe(999);
    expect(response.body.count).toBe(0);
    expect(response.body.history).toEqual([]);
  });
  it("should create a valid contribution", async () => {
    const response = await request(app)
      .post("/contribution")
      .send({
        member_id: 1,
        chit_group_id: 101,
        due_date: "2026-09-05",
        amount_due: 1500,
        amount_paid: 1500,
        paid_on_time: true,
      });

    expect(response.status).toBe(201);
    expect(response.body.contribution).toBeDefined();
    expect(response.body.contribution.member_id).toBe(1);
    expect(response.body.contribution.chit_group_id).toBe(101);
    expect(response.body.contribution.amount_due).toBe(1500);
    expect(response.body.contribution.amount_paid).toBe(1500);
    expect(response.body.contribution.paid_on_time).toBe(true);

    const createdId = response.body.contribution.id;

    const { error } = await supabase
      .from("chit_contributions")
      .delete()
      .eq("id", createdId);

    expect(error).toBeNull();
  });





  it("POST /contribution should reject negative amount_due", async () => {
    const response = await request(app)
      .post("/contribution")
      .send({
        member_id: 1,
        chit_group_id: 101,
        due_date: "2026-09-05",
        amount_due: -100,
        amount_paid: 0,
        paid_on_time: false,
      });

    expect(response.status).toBe(400);
    expect(response.body.error).toBe(
      "amount_due must be greater than 0"
    );
  });

  it("POST /contribution should reject amount_paid greater than amount_due", async () => {
    const response = await request(app)
      .post("/contribution")
      .send({
        member_id: 1,
        chit_group_id: 101,
        due_date: "2026-09-05",
        amount_due: 1000,
        amount_paid: 1500,
        paid_on_time: false,
      });

    expect(response.status).toBe(400);
    expect(response.body.error).toBe(
      "amount_paid cannot exceed amount_due"
    );
  });

  it("POST /contribution should reject invalid date format", async () => {
    const response = await request(app)
      .post("/contribution")
      .send({
        member_id: 1,
        chit_group_id: 101,
        due_date: "05-09-2026",
        amount_due: 1000,
        amount_paid: 1000,
        paid_on_time: true,
      });

    expect(response.status).toBe(400);
    expect(response.body.error).toBe(
      "Invalid due_date. Use YYYY-MM-DD"
    );
  });

  it("POST /contribution should reject invalid paid_on_time value", async () => {
    const response = await request(app)
      .post("/contribution")
      .send({
        member_id: 1,
        chit_group_id: 101,
        due_date: "2026-09-05",
        amount_due: 1000,
        amount_paid: 1000,
        paid_on_time: "yes",
      });

    expect(response.status).toBe(400);
    expect(response.body.error).toBe(
      "paid_on_time must be boolean"
    );
  });
});