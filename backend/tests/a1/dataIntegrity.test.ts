import { describe, it, expect } from "vitest";
import { supabase } from "../../src/supabase.js";

describe("A1 Database + Seed Data Integrity", () => {
  it("should contain exactly 18 members", async () => {
    const { data, error } = await supabase
      .from("members")
      .select("member_id");

    expect(error).toBeNull();
    expect(data).toHaveLength(18);
  });

  it("should contain exactly 126 daily earning records", async () => {
    const { data, error } = await supabase
      .from("daily_earnings")
      .select("id");

    expect(error).toBeNull();
    expect(data).toHaveLength(126);
  });

  it("should contain exactly 18 smoothing wallets", async () => {
    const { data, error } = await supabase
      .from("smoothing_wallet")
      .select("member_id");

    expect(error).toBeNull();
    expect(data).toHaveLength(18);
  });

  it("should have exactly 3 chit groups with 6 members each", async () => {
    const { data, error } = await supabase
      .from("members")
      .select("chit_group_id");

    expect(error).toBeNull();
    expect(data).toBeDefined();

    const groupCounts = new Map<number, number>();

    for (const member of data ?? []) {
      const groupId = Number(member.chit_group_id);

      groupCounts.set(
        groupId,
        (groupCounts.get(groupId) ?? 0) + 1
      );
    }

    expect(groupCounts.size).toBe(3);
    expect(groupCounts.get(101)).toBe(6);
    expect(groupCounts.get(102)).toBe(6);
    expect(groupCounts.get(103)).toBe(6);
  });

  it("should have no contribution with amount_paid greater than amount_due", async () => {
    const { data, error } = await supabase
      .from("chit_contributions")
      .select("id, amount_due, amount_paid");

    expect(error).toBeNull();

    for (const contribution of data ?? []) {
      expect(
        Number(contribution.amount_paid)
      ).toBeLessThanOrEqual(
        Number(contribution.amount_due)
      );
    }
  });

  it("should have no daily earning with a negative amount", async () => {
    const { data, error } = await supabase
      .from("daily_earnings")
      .select("id, amount");

    expect(error).toBeNull();

    for (const earning of data ?? []) {
      expect(Number(earning.amount)).toBeGreaterThanOrEqual(0);
    }
  });

  it("should have every daily earning linked to a valid member", async () => {
    const { data: members, error: memberError } = await supabase
      .from("members")
      .select("member_id");

    expect(memberError).toBeNull();

    const memberIds = new Set(
      (members ?? []).map((member) => Number(member.member_id))
    );

    const { data: earnings, error: earningError } = await supabase
      .from("daily_earnings")
      .select("member_id");

    expect(earningError).toBeNull();

    for (const earning of earnings ?? []) {
      expect(
        memberIds.has(Number(earning.member_id))
      ).toBe(true);
    }
  });

  it("should have every contribution linked to a valid member", async () => {
    const { data: members, error: memberError } = await supabase
      .from("members")
      .select("member_id");

    expect(memberError).toBeNull();

    const memberIds = new Set(
      (members ?? []).map((member) => Number(member.member_id))
    );

    const { data: contributions, error: contributionError } =
      await supabase
        .from("chit_contributions")
        .select("member_id");

    expect(contributionError).toBeNull();

    for (const contribution of contributions ?? []) {
      expect(
        memberIds.has(Number(contribution.member_id))
      ).toBe(true);
    }
  });

  it("should have exactly 7 contribution records for each seeded member", async () => {
    const { data, error } = await supabase
      .from("chit_contributions")
      .select("member_id");

    expect(error).toBeNull();

    const counts = new Map<number, number>();

    for (const contribution of data ?? []) {
      const memberId = Number(contribution.member_id);

      counts.set(
        memberId,
        (counts.get(memberId) ?? 0) + 1
      );
    }

    expect(counts.size).toBe(18);

    for (let memberId = 1; memberId <= 18; memberId++) {
      expect(counts.get(memberId)).toBe(6);
    }
  });
});