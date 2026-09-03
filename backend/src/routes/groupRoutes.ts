import { Router } from "express";
import { getMembersByGroup } from "../controllers/groupController.js";

const router = Router();

router.get("/group/:id/members", getMembersByGroup);

export default router;