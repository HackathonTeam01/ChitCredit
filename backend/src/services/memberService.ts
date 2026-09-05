import { supabase } from "../supabase.js";

export async function getAllMembers() {
  const { data, error } = await supabase
    .from("members")
    .select("*")
    .order("member_id", { ascending: true });

  if (error) {
    throw new Error(`Failed to fetch members: ${error.message}`);
  }

  return data;
}

export async function getMemberById(memberId: number) {
  const { data, error } = await supabase
    .from("members")
    .select("*")
    .eq("member_id", memberId)
    .maybeSingle();

  if (error) {
    throw new Error(`Failed to fetch member: ${error.message}`);
  }

  return data;
}