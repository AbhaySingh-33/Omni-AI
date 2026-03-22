// import model from "../config/gemini.js";

// export const generateResponse = async (prompt) => {
//   try {
//     const result = await model.generateContent(prompt);
//     const response = await result.response;
//     return response.text();
//   } catch (error) {
//     console.error("Gemini Error:", error);
//     throw new Error("AI generation failed");
//   }
// };

import axios from "axios";

export const generateResponse = async (prompt) => {
  try {
    const res = await axios.post("http://localhost:8000/chat", {
      message: prompt,
    });

    return res.data.response;
  } catch (error) {
    console.error("AI Engine Error:", error.message);
    throw new Error("AI Engine failed");
  }
};