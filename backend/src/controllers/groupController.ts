import { Request, Response } from "express";
import { getGroupMembers } from "../services/groupService.js";

export async function getMembersByGroup(
  req: Request,
  res: Response
) {
  try {
    const groupId = Number(req.params.id);

    if (!Number.isInteger(groupId) || groupId <= 0) {
      res.status(400).json({
        error: "Invalid group ID",
      });
      return;
    }

    const members = await getGroupMembers(groupId);

    res.status(200).json({
      chit_group_id: groupId,
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