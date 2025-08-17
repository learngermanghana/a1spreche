// index.js
const express = require("express");
const cors = require("cors");
const multer = require("multer");
const admin = require("firebase-admin");

// v2 import:
const { onRequest } = require("firebase-functions/v2/https");
// (optional) pick a region explicitly so rewrites never get confused
const { setGlobalOptions } = require("firebase-functions/v2");
setGlobalOptions({ region: "us-central1" });

admin.initializeApp();
const app = express();
app.use(cors({ origin: true }));

app.get("/health", (req, res) => res.send("ok"));

const upload = multer({ storage: multer.memoryStorage() });
app.post("/upload", upload.single("file"), async (req, res) => {
  try {
    if (!req.file) return res.status(400).send("no file");
    const bucket = admin.storage().bucket();
    const filename = `uploads/${Date.now()}_${req.file.originalname}`;
    await bucket.file(filename).save(req.file.buffer, { contentType: req.file.mimetype });
    res.json({ ok: true, path: filename });
  } catch (e) {
    console.error(e);
    res.status(500).send("upload failed");
  }
});

// name must stay "api" to match your firebase.json rewrite
exports.api = onRequest(app);
