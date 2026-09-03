import { Router } from "express";
import {
  getScore,
  getCreditOffer,
} from "../controllers/creditController.js";

const router = Router();

router.get("/member/:id/score", getScore);
router.get("/member/:id/credit-offer", getCreditOffer);

export default router;
