import { generateResponse } from "../services/ai.service.js";

export const handleChat = async (req, res) => {
  try {
    const { message } = req.body;

    const reply = await generateResponse(message);

    res.json({
      success: true,
      data: reply,
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message,
    });
  }
};