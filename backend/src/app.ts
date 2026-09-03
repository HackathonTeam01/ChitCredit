import express from "express";
import cors from "cors";

import memberRoutes from "./routes/memberRoutes.js";
import contributionRoutes from "./routes/contributionRoutes.js";
import historyRoutes from "./routes/historyRoutes.js";
import groupRoutes from "./routes/groupRoutes.js";
import creditRoutes from "./routes/creditRoutes.js";

const app = express();

app.use(cors());
app.use(express.json());

app.use("/", memberRoutes);
app.use("/", contributionRoutes);
app.use("/", historyRoutes);
app.use("/", groupRoutes);
app.use("/", creditRoutes);

app.get("/health", (_req, res) => {
  res.status(200).json({
    status: "ok",
    service: "chit-credit-backend",
  });
});

export default app;