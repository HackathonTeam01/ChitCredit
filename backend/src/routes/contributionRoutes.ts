import { Router } from "express";
import { addContribution } from "../controllers/contributionController.js";

const router = Router();

router.post("/contribution", addContribution);

export default router;