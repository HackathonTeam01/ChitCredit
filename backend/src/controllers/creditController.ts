import { Request, Response } from "express";
import {
  getMemberScore,
  getMemberCreditOffer,
  CreditServiceError,
} from "../services/creditService.js";

export async function getScore(req: Request, res: Response): Promise<void> {
  try {
    const rawId = req.params.id;
    const memberId = Array.isArray(rawId) ? rawId[0] : rawId;

    if (!memberId || typeof memberId !== "string" || !memberId.trim()) {
      res.status(400).json({
        error: "member_id must be a non-empty string",
      });
      return;
    }

    const includeBreakdown =
      req.query.include_breakdown === undefined ||
      req.query.include_breakdown === "true";

    const score = await getMemberScore(memberId, includeBreakdown);

    res.status(200).json(score);
  } catch (error) {
    if (error instanceof CreditServiceError) {
      res.status(error.statusCode).json({
        error: error.message,
      });
      return;
    }

    const message =
      error instanceof Error ? error.message : "Unknown server error";

    res.status(500).json({
      error: message,
    });
  }
}

export async function getCreditOffer(req: Request, res: Response): Promise<void> {
  try {
    const rawId = req.params.id;
    const memberId = Array.isArray(rawId) ? rawId[0] : rawId;

    if (!memberId || typeof memberId !== "string" || !memberId.trim()) {
      res.status(400).json({
        error: "member_id must be a non-empty string",
      });
      return;
    }

    const unlockDate =
      typeof req.query.unlock_date === "string"
        ? req.query.unlock_date
        : undefined;

    const offer = await getMemberCreditOffer(memberId, unlockDate);

    res.status(200).json(offer);
  } catch (error) {
    if (error instanceof CreditServiceError) {
      res.status(error.statusCode).json({
        error: error.message,
      });
      return;
    }

    const message =
      error instanceof Error ? error.message : "Unknown server error";

    res.status(500).json({
      error: message,
    });
  }
}
