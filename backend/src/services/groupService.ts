import { supabase } from "../supabase.js";

export async function getGroupMembers(groupId: number) {
  const { data, error } = await supabase
    .from("members")
    .select("*")
    .eq("chit_group_id", groupId)
    .order("member_id", { ascending: true });

  if (error) {
    throw new Error(`Failed to fetch group members: ${error.message}`);
  }

  return data;
}