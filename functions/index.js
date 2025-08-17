const functions = require("firebase-functions");
const express = require("express");
const cors = require("cors");
const multer = require("multer");
const admin = require("firebase-admin");

admin.initializeApp();
const app = express();
app.use(cors({ origin: true }));

// health check
app.get("/health", (req, res) => res.send("ok"));

// handle uploads: expects <input name="file">
const upload = multer({ storage: multer.memoryStorage() });
app.post("/upload", upload.single("file"), async (req, res) => {
  try {
    if (!req.file) return res.status(400).send("no file");

    const bucket = admin.storage().bucket(); // default Firebase Storage bucket
    const filename = `uploads/${Date.now()}_${req.file.originalname}`;
    const file = bucket.file(filename);
    await file.save(req.file.buffer, { contentType: req.file.mimetype });

    res.json({ ok: true, path: filename });
  } catch (e) {
    console.error(e);
    res.status(500).send("upload failed");
  }
});

// export *as* "api" (must match firebase.json rewrite)
exports.api = functions.https.onRequest(app);
