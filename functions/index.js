// functions/index.js
"use strict";

const express = require("express");
const cors = require("cors");
const multer = require("multer");
const admin = require("firebase-admin");

// --- Firebase Functions v2 (Node 20 friendly)
const { onRequest } = require("firebase-functions/v2/https");
const { setGlobalOptions } = require("firebase-functions/v2");
const { defineSecret } = require("firebase-functions/params");

// Secret: set via CLI: firebase functions:secrets:set OPENAI_API_KEY --project language-academy-3e1de
const OPENAI_API_KEY = defineSecret("OPENAI_API_KEY");

// Region explicit so rewrites never get confused
setGlobalOptions({ region: "us-central1" });

admin.initializeApp();

const app = express();
app.use(cors({ origin: true }));

// --- health check
app.get("/health", (_req, res) => res.send("ok"));

// --- upload (expects <input name="file">)
const upload = multer({ storage: multer.memoryStorage() });
app.post("/upload", upload.single("file"), async (req, res) => {
  try {
    if (!req.file) return res.status(400).send("no file");

    const bucket = admin.storage().bucket(); // default bucket <project-id>.appspot.com
    const filename = `uploads/${Date.now()}_${req.file.originalname}`;
    await bucket.file(filename).save(req.file.buffer, { contentType: req.file.mimetype });

    res.json({ ok: true, path: filename });
  } catch (e) {
    console.error(e);
    res.status(500).send("upload failed");
  }
});

// --- feedback (text or audio-from-storage)
app.post("/feedback", express.json({ limit: "2mb" }), async (req, res) => {
  try {
    const apiKey = process.env.OPENAI_API_KEY; // mounted by secret
    if (!apiKey) {
      return res.status(500).json({ ok: false, error: "OPENAI_API_KEY not set" });
    }

    const { mode = "text", text, storagePath } = req.body || {};

    // 1) Prepare student's answer (either provided text or transcribed audio)
    let studentAnswer = (text || "").trim();

    if (!studentAnswer && mode === "audio" && storagePath) {
      // download audio from Firebase Storage
      const [audioBuffer] = await admin.storage().bucket().file(storagePath).download();

      // Transcribe with Whisper
      const form = new FormData();
      const blob = new Blob([audioBuffer], { type: "audio/webm" });
      form.append("file", blob, "recording.webm");
      form.append("model", "whisper-1");
      form.append("response_format", "json");

      const whisperResp = await fetch("https://api.openai.com/v1/audio/transcriptions", {
        method: "POST",
        headers: { Authorization: `Bearer ${apiKey}` },
        body: form,
      });

      const whisperJson = await whisperResp.json();
      if (!whisperResp.ok) {
        console.error("whisper error:", whisperJson);
        return res.status(502).json({ ok: false, error: "transcription-failed" });
      }
      studentAnswer = (whisperJson.text || "").trim();
    }

    if (!studentAnswer) {
      return res.status(400).json({ ok: false, error: "No answer text provided." });
    }

    // 2) Ask the LLM for concise feedback
    const prompt = `
You are a German tutor. Give concise feedback in English for an A1–A2 student.
Rules:
- Show a corrected version first (1–2 lines).
- Then a very short explanation (simple English).
- Then 2 improvement tips.
- If it's a request/imperative, ensure "bitte" or a polite modal is used when appropriate.
- Max 120 words.

Student answer (German):
${studentAnswer}
`.trim();

    const chatResp = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
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
    const chatJson = await chatResp.json();
    if (!chatResp.ok) {
      console.error("chat error:", chatJson);
      return res.status(502).json({ ok: false, error: "feedback-generation-failed" });
    }
    const feedback =
      chatJson.choices?.[0]?.message?.content?.trim() || "No feedback generated.";

    // 3) Lightweight score 0–10
    const scorePrompt = `Score 0-10 how correct/clear this A1–A2 answer is. Answer with only a number.\n\n${studentAnswer}`;
    const scoreCall = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: "gpt-4o-mini",
        messages: [{ role: "user", content: scorePrompt }],
        temperature: 0.0,
      }),
    });
    const scoreJson = await scoreCall.json();
    let score = parseInt(scoreJson.choices?.[0]?.message?.content?.trim() || "0", 10);
    if (Number.isNaN(score)) score = 0;
    score = Math.max(0, Math.min(10, score));

    res.json({ ok: true, mode, transcript: studentAnswer, score, feedback });
  } catch (err) {
    console.error(err);
    res.status(500).json({ ok: false, error: "feedback-failed" });
  }
});

// Export as "api" to match firebase.json rewrite
exports.api = onRequest({ secrets: [OPENAI_API_KEY] }, app);
