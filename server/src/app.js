import express from "express";
import cors from "cors";

import aiRoutes from "./routes/ai.routes.js";

const app = express();

app.use(cors());
app.use(express.json());

app.get("/", (req, res) => {
  res.send("OmniAI Server Running 🚀");
});

app.use("/api/ai", aiRoutes);

export default app;