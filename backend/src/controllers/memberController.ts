import { Request, Response } from "express";
import {
  getAllMembers,
  getMemberById,
} from "../services/memberService.js";

export async function getMembers(
  _req: Request,
  res: Response
) {
  try {
    const members = await getAllMembers();

    res.status(200).json({
      count: members?.length ?? 0,
      members: members ?? [],
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

export async function getMember(
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

    const member = await getMemberById(memberId);

    if (!member) {
      res.status(404).json({
        error: "Member not found",
      });
      return;
    }

    res.status(200).json({
      member,
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