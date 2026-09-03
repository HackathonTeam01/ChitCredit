import { supabase } from "../supabase.js";

export async function getMemberHistory(memberId: number) {
  const { data, error } = await supabase
    .from("chit_contributions")
    .select("*")
    .eq("member_id", memberId)
    .order("due_date", { ascending: true });

  if (error) {
    throw new Error(`Failed to fetch member history: ${error.message}`);
  }

  return data;
}