import { Request, Response } from "express";
import { getMemberHistory } from "../services/historyService.js";

export async function getHistory(
  req: Request,
  res: Response
) {
  try {
    const memberId = Number(req.params.id);

    if (!Number.isInteger(memberId) || memberId <= 0) {
      res.status(400).json({
        error: "Invalid member ID",
      });
      return;
    }

    const history = await getMemberHistory(memberId);

    res.status(200).json({
      member_id: memberId,
      count: history?.length ?? 0,
      history: history ?? [],
    });
  } catch (error) {
    const message =
      error instanceof Error
        ? error.message
        : "Unknown server error";

    res.status(500).json({
      error: message,
    });
  }
}