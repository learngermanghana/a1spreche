// ADD: AI client (OpenAI shown; you can swap for any provider)
const fetch = require("node-fetch"); // if not on Node 18+, but Node 20 has fetch built-in; remove this line if so.

// If you deploy with a Functions v2 secret, you can use process.env.OPENAI_API_KEY
// Set this once: firebase functions:secrets:set OPENAI_API_KEY --project language-academy-3e1de

app.post("/feedback", express.json({ limit: "2mb" }), async (req, res) => {
  try {
    const { mode = "text", text, storagePath } = req.body || {};

    // 1) If audio: download from Firebase Storage and transcribe (optional)
    let studentAnswer = text || "";
    if (mode === "audio" && storagePath) {
      const [audioBuffer] = await admin.storage().bucket().file(storagePath).download();
      // Transcribe with Whisper (OpenAI) — or Google STT if you prefer
      const whisperResp = await fetch("https://api.openai.com/v1/audio/transcriptions", {
        method: "POST",
        headers: { Authorization: `Bearer ${process.env.OPENAI_API_KEY}` },
        body: (() => {
          const form = new (require("form-data"))();
          form.append("file", audioBuffer, { filename: "recording.webm", contentType: "audio/webm" });
          form.append("model", "whisper-1");
          form.append("response_format", "json");
          return form;
        })(),
      });
      const whisperJson = await whisperResp.json();
      studentAnswer = whisperJson.text || "";
    }

    if (!studentAnswer) return res.status(400).json({ error: "No answer text provided." });

    // 2) Ask the LLM for feedback (A1/A2 friendly, English explanations)
    const prompt = `
You are a German tutor. Give concise feedback in English for an A1–A2 student.
Rules:
- Correct grammar and word order.
- Show a corrected version first.
- Then a short explanation (simple English).
- Then 2 improvement tips.
- If it's a request/imperative, ensure "bitte" or a polite modal is used when appropriate.
- Keep it under 120 words total.

Student answer (German):
${studentAnswer}
`;

    // Chat call (OpenAI). If you use a different provider, swap this fetch.
    const llmResp = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${process.env.OPENAI_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: "gpt-4o-mini",
        messages: [
          { role: "system", content: "You teach German simply to beginners (A1–A2)." },
          { role: "user", content: prompt },
        ],
        temperature: 0.2,
      }),
    });
    const llmJson = await llmResp.json();
    const feedback = llmJson.choices?.[0]?.message?.content?.trim() || "No feedback generated.";

    // You can also add a simple 0–10 score:
    const scorePrompt = `Score 0-10 how correct/clear this A1–A2 answer is. Answer with only a number.\n\n${studentAnswer}`;
    const scoreResp = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${process.env.OPENAI_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: "gpt-4o-mini",
        messages: [{ role: "user", content: scorePrompt }],
        temperature: 0.0,
      }),
    });
    const scoreJson = await scoreResp.json();
    const rawScore = scoreJson.choices?.[0]?.message?.content?.trim() || "0";
    const score = Math.max(0, Math.min(10, parseInt(rawScore, 10) || 0));

    res.json({ ok: true, mode, transcript: studentAnswer, score, feedback });
  } catch (err) {
    console.error(err);
    res.status(500).json({ ok: false, error: "feedback-failed" });
  }
});
