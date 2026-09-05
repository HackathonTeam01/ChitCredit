import { Router } from "express";
import {
  getMembers,
  getMember,
} from "../controllers/memberController.js";

const router = Router();

router.get("/members", getMembers);
router.get("/member/:id", getMember);

export default router;