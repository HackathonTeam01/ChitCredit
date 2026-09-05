import { supabase } from "../supabase.js";

export interface CreateContributionInput {
  member_id: number;
  chit_group_id: number;
  due_date: string;
  amount_due: number;
  amount_paid: number;
  paid_on_time: boolean;
}

export async function createContribution(
  input: CreateContributionInput
) {
  const { data, error } = await supabase
    .from("chit_contributions")
    .insert({
      member_id: input.member_id,
      chit_group_id: input.chit_group_id,
      due_date: input.due_date,
      amount_due: input.amount_due,
      amount_paid: input.amount_paid,
      paid_on_time: input.paid_on_time,
    })
    .select("*")
    .single();

  if (error) {
    throw new Error(`Failed to create contribution: ${error.message}`);
  }

  return data;
}