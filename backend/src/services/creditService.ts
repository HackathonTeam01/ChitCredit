import { execFile } from "node:child_process";
import { promisify } from "node:util";
import path from "node:path";
import { getMemberById } from "./memberService.js";
import { getMemberHistory } from "./historyService.js";

const execFileAsync = promisify(execFile);

function getRepoRoot(): string {
  const cwd = process.cwd();
  if (cwd.endsWith("backend") || cwd.endsWith("backend\\") || cwd.endsWith("backend/")) {
    return path.resolve(cwd, "..");
  }
  return path.resolve(cwd);
}

export interface ScoreWeights {
  w1_on_time: number;
  w2_streak: number;
  w3_tenure: number;
  w4_missed_penalty: number;
}

export interface ScoreBreakdown {
  on_time_component: number;
  streak_component: number;
  tenure_component: number;
  missed_payment_penalty: number;
  raw_score: number;
  clamped_score: number;
  weights: ScoreWeights;
  normalization_convention: string;
}

export interface ScoreResponse {
  member_id: string;
  on_time_pct: number;
  streak_count: number;
  tenure_cycles: number;
  score_value: number;
  score_band: "Gold" | "Silver" | "Bronze" | "Not Yet Eligible" | string;
  breakdown?: ScoreBreakdown;
}

export interface CreditOfferResponse {
  member_id: string;
  eligible_amount: number;
  interest_rate: number;
  unlock_date: string;
  partner_nbfc: string;
  is_eligible: boolean;
  score_band: "Gold" | "Silver" | "Bronze" | "Not Yet Eligible" | string;
  term_months: number;
  disclaimer: string;
}

export class CreditServiceError extends Error {
  statusCode: number;

  constructor(message: string, statusCode: number = 500) {
    super(message);
    this.name = "CreditServiceError";
    this.statusCode = statusCode;
  }
}

/**
 * Execute Python snippet safely against A2 scoring/offer engine.
 */
async function runPythonScript(script: string): Promise<any> {
  const pythonCmd = process.env.PYTHON_PATH || (process.platform === "win32" ? "python" : "python3");
  const repoRoot = getRepoRoot();

  try {
    const { stdout } = await execFileAsync(
      pythonCmd,
      ["-c", script],
      {
        cwd: repoRoot,
        timeout: 10000,
        env: { ...process.env },
      }
    );

    const result = JSON.parse(stdout.trim());
    if (result.status === "not_found") {
      throw new CreditServiceError(result.error || "Member not found", 404);
    }
    if (result.status === "bad_request") {
      throw new CreditServiceError(result.error || "Invalid request", 400);
    }
    if (result.status === "error") {
      throw new CreditServiceError(result.error || "Scoring engine error", 500);
    }
    return result.data;
  } catch (err: any) {
    if (err instanceof CreditServiceError) {
      throw err;
    }
    if (err.stdout) {
      try {
        const parsed = JSON.parse(err.stdout.trim());
        if (parsed.status === "not_found") throw new CreditServiceError(parsed.error, 404);
        if (parsed.status === "bad_request") throw new CreditServiceError(parsed.error, 400);
        if (parsed.status === "error") throw new CreditServiceError(parsed.error, 500);
      } catch {
        // Fall through to general error
      }
    }
    throw new CreditServiceError(err.message || "Failed to execute credit service", 500);
  }
}

/**
 * Derive metrics from A1 DB history for custom evaluation
 */
function deriveMetricsFromHistory(history: any[]) {
  if (!history || history.length === 0) {
    return {
      onTimePct: 0.0,
      streakCount: 0,
      tenureCycles: 0,
      missedPayments: 0,
    };
  }

  const total = history.length;
  const onTimeCount = history.filter((h) => h.paid_on_time).length;
  const onTimePct = total > 0 ? (onTimeCount / total) * 100 : 0.0;
  const missedPayments = total - onTimeCount;

  // Streak: consecutive on_time payments from latest
  let streak = 0;
  for (let i = history.length - 1; i >= 0; i--) {
    if (history[i].paid_on_time) {
      streak++;
    } else {
      break;
    }
  }

  // Tenure: full cycles completed (approx 6-month cycles)
  const tenureCycles = Math.floor(total / 6) || (total >= 1 ? 1 : 0);

  return {
    onTimePct: Math.round(onTimePct * 100) / 100,
    streakCount: streak,
    tenureCycles,
    missedPayments,
  };
}

/**
 * Get canonical Chit Credit Score for a member
 */
export async function getMemberScore(
  memberId: string,
  includeBreakdown: boolean = true
): Promise<ScoreResponse> {
  const sanitizedId = memberId.trim();
  if (!sanitizedId) {
    throw new CreditServiceError("member_id must be a non-empty string", 400);
  }

  const repoRoot = getRepoRoot();
  const script = `
import sys, json
from pathlib import Path

repo_root = Path(r"${repoRoot}").resolve()
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from backend.a2.scoring.service import default_score_service

try:
    score = default_score_service.get_score_for_member(
        member_id="${sanitizedId}",
        include_breakdown=${includeBreakdown ? "True" : "False"}
    )
    print(json.dumps({"status": "ok", "data": score.to_dict()}))
except KeyError as e:
    print(json.dumps({"status": "not_found", "error": str(e)}))
except ValueError as e:
    print(json.dumps({"status": "bad_request", "error": str(e)}))
except Exception as e:
    print(json.dumps({"status": "error", "error": str(e)}))
`;

  try {
    return await runPythonScript(script);
  } catch (err: any) {
    // If not found in MockDataProvider, check if member exists in A1 Supabase DB
    if (err instanceof CreditServiceError && err.statusCode === 404) {
      const numId = Number(sanitizedId);
      if (Number.isInteger(numId) && numId > 0) {
        const dbMember = await getMemberById(numId);
        if (dbMember) {
          const history = await getMemberHistory(numId);
          const metrics = deriveMetricsFromHistory(history || []);

          const customScript = `
import sys, json
from pathlib import Path

repo_root = Path(r"${repoRoot}").resolve()
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from backend.a2.scoring.service import default_score_service

try:
    score = default_score_service.calculate_custom_score(
        on_time_pct=${metrics.onTimePct},
        streak_count=${metrics.streakCount},
        tenure_cycles=${metrics.tenureCycles},
        missed_payment_count=${metrics.missedPayments},
        member_id="${sanitizedId}",
        include_breakdown=${includeBreakdown ? "True" : "False"}
    )
    print(json.dumps({"status": "ok", "data": score.to_dict()}))
except ValueError as e:
    print(json.dumps({"status": "bad_request", "error": str(e)}))
except Exception as e:
    print(json.dumps({"status": "error", "error": str(e)}))
`;
          return await runPythonScript(customScript);
        }
      }
    }
    throw err;
  }
}

/**
 * Get canonical NBFC credit offer for a member
 */
export async function getMemberCreditOffer(
  memberId: string,
  unlockDate?: string
): Promise<CreditOfferResponse> {
  const sanitizedId = memberId.trim();
  if (!sanitizedId) {
    throw new CreditServiceError("member_id must be a non-empty string", 400);
  }

  const repoRoot = getRepoRoot();
  const unlockDateArg = unlockDate ? `"${unlockDate}"` : "None";

  const script = `
import sys, json
from pathlib import Path

repo_root = Path(r"${repoRoot}").resolve()
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from backend.a2.offers.service import default_offer_service

try:
    offer = default_offer_service.get_offer_for_member(
        member_id="${sanitizedId}",
        unlock_date=${unlockDateArg}
    )
    print(json.dumps({"status": "ok", "data": offer.to_dict()}))
except KeyError as e:
    print(json.dumps({"status": "not_found", "error": str(e)}))
except ValueError as e:
    print(json.dumps({"status": "bad_request", "error": str(e)}))
except Exception as e:
    print(json.dumps({"status": "error", "error": str(e)}))
`;

  try {
    return await runPythonScript(script);
  } catch (err: any) {
    if (err instanceof CreditServiceError && err.statusCode === 404) {
      const numId = Number(sanitizedId);
      if (Number.isInteger(numId) && numId > 0) {
        const dbMember = await getMemberById(numId);
        if (dbMember) {
          const score = await getMemberScore(sanitizedId);
          const bandScript = `
import sys, json
from pathlib import Path

repo_root = Path(r"${repoRoot}").resolve()
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from backend.a2.offers.service import default_offer_service

try:
    offer = default_offer_service.get_offer_for_band(
        score_band="${score.score_band}",
        member_id="${sanitizedId}",
        unlock_date=${unlockDateArg}
    )
    print(json.dumps({"status": "ok", "data": offer.to_dict()}))
except ValueError as e:
    print(json.dumps({"status": "bad_request", "error": str(e)}))
except Exception as e:
    print(json.dumps({"status": "error", "error": str(e)}))
`;
          return await runPythonScript(bandScript);
        }
      }
    }
    throw err;
  }
}
