import { Router } from "express";
import { calculateMemberForecast, calculateRepayment, calculateReserve } from "../controllers/productController.js";

const router = Router();

router.post("/smoothing/reserve", calculateReserve);
router.post("/repayment/simulate", calculateRepayment);
router.post("/member/:id/forecast", calculateMemberForecast);
router.get("/member/:id/forecast", calculateMemberForecast);

export default router;
