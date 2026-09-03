import { Request, Response } from "express";
import { createContribution } from "../services/contributionService.js";

export async function addContribution(
  req: Request,
  res: Response
) {
  try {
    const {
      member_id,
      chit_group_id,
      due_date,
      amount_due,
      amount_paid,
      paid_on_time,
    } = req.body;

    if (
      !Number.isInteger(member_id) ||
      member_id <= 0
    ) {
      res.status(400).json({
        error: "Invalid member_id",
      });
      return;
    }

    if (
      !Number.isInteger(chit_group_id) ||
      chit_group_id <= 0
    ) {
      res.status(400).json({
        error: "Invalid chit_group_id",
      });
      return;
    }

    if (
      typeof due_date !== "string" ||
      !/^\d{4}-\d{2}-\d{2}$/.test(due_date)
    ) {
      res.status(400).json({
        error: "Invalid due_date. Use YYYY-MM-DD",
      });
      return;
    }

    if (
      typeof amount_due !== "number" ||
      amount_due <= 0
    ) {
      res.status(400).json({
        error: "amount_due must be greater than 0",
      });
      return;
    }

    if (
      typeof amount_paid !== "number" ||
      amount_paid < 0
    ) {
      res.status(400).json({
        error: "amount_paid must be 0 or greater",
      });
      return;
    }

    if (amount_paid > amount_due) {
      res.status(400).json({
        error: "amount_paid cannot exceed amount_due",
      });
      return;
    }

    if (typeof paid_on_time !== "boolean") {
      res.status(400).json({
        error: "paid_on_time must be boolean",
      });
      return;
    }

    const contribution = await createContribution({
      member_id,
      chit_group_id,
      due_date,
      amount_due,
      amount_paid,
      paid_on_time,
    });

    res.status(201).json({
      message: "Contribution created successfully",
      contribution,
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