import { createClient } from "@supabase/supabase-js";
import dotenv from "dotenv";

dotenv.config();

const supabaseUrl = process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_KEY;

if (!supabaseUrl) {
  throw new Error("SUPABASE_URL is missing from environment variables");
}

if (!supabaseKey) {
  throw new Error("SUPABASE_KEY is missing from environment variables");
}

export const supabase = createClient(
  supabaseUrl,
  supabaseKey
);