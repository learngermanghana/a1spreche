/* Cloud Functions: simple multipart upload -> Storage + Firestore
   Endpoint used by public/recorder.html:  POST /api/upload-audio
*/
const functions = require("firebase-functions");
const admin = require("firebase-admin");
const Busboy = require("busboy");
const cors = require("cors")({ origin: true });

if (!admin.apps.length) {
  admin.initializeApp(); // uses default project credentials
}
const db = admin.firestore();
const bucket = admin.storage().bucket();

// Allow only these origins (adjust to your domains)
const ALLOW_ORIGINS = new Set([
  "https://language-academy-3e1de.web.app",
  "https://www.falowen.app",
  "https://falowen.app",
  "http://localhost:5000",
  "http://localhost:3000"
]);

function setCors(res, req) {
  const origin = req.headers.origin || "";
  if (ALLOW_ORIGINS.has(origin)) {
    res.set("Access-Control-Allow-Origin", origin);
    res.set("Vary", "Origin");
  } else {
    res.set("Access-Control-Allow-Origin", "*"); // fallback
  }
  res.set("Access-Control-Allow-Methods", "POST, OPTIONS, GET");
  res.set("Access-Control-Allow-Headers", "Content-Type, Authorization");
}

async function handleUpload(req, res) {
  if (req.method === "OPTIONS") {
    setCors(res, req);
    return res.status(204).end();
  }
  if (req.method !== "POST") {
    setCors(res, req);
    return res.status(405).json({ ok: false, error: "Method not allowed" });
  }

  setCors(res, req);

  const bb = Busboy({ headers: req.headers, limits: { fileSize: 25 * 1024 * 1024 } }); // 25MB
  let studentCode = "";
  let source = "web-recorder";
  let fileBuffer = Buffer.alloc(0);
  let fileMime = "application/octet-stream";
  let fileName = "speech.webm";

  let gotFile = false;

  bb.on("field", (name, val) => {
    if (name === "student_code") studentCode = String(val || "").trim().toLowerCase();
    if (name === "source") source = String(val || source);
  });

  bb.on("file", (_name, file, info) => {
    gotFile = true;
    fileMime = info?.mimeType || fileMime;
    fileName = info?.filename || fileName;
    file.on("data", (data) => { fileBuffer = Buffer.concat([fileBuffer, data]); });
  });

  bb.on("limit", () => {
    return res.status(413).json({ ok: false, error: "File too large (max 25MB)" });
  });

  bb.on("finish", async () => {
    try {
      if (!studentCode) {
        return res.status(400).json({ ok: false, error: "Missing student_code" });
      }
      if (!gotFile || !fileBuffer.length) {
        return res.status(400).json({ ok: false, error: "No file uploaded" });
      }

      const ts = Date.now();
      const safeCode = studentCode.replace(/[^a-z0-9_-]/g, "");
      const ext = (fileName.includes(".") ? fileName.split(".").pop() : "webm");
      const storagePath = `pron_inbox/${safeCode}/${ts}.${ext}`;

      await bucket.file(storagePath).save(fileBuffer, {
        contentType: fileMime,
        resumable: false,
        metadata: { cacheControl: "private, max-age=0" }
      });

      const docRef = await db.collection("pron_inbox").add({
        student_code: safeCode,
        storage_path: storagePath,
        mime_type: fileMime,
        file_name: fileName,
        source: source,
        status: "uploaded",
        createdAt: admin.firestore.FieldValue.serverTimestamp()
      });

      return res.json({ ok: true, id: docRef.id, path: storagePath });
    } catch (e) {
      console.error("upload-audio error:", e);
      return res.status(500).json({ ok: false, error: String(e.message || e) });
    }
  });

  req.pipe(bb);
}

// Small multiplexer so we can add more endpoints later
exports.api = functions.https.onRequest(async (req, res) => {
  const url = (req.path || req.url || "").toLowerCase();
  if (url.includes("/upload-audio")) {
    return handleUpload(req, res);
  }
  if (req.method === "GET" && url.includes("/health")) {
    setCors(res, req);
    return res.json({ ok: true, now: new Date().toISOString() });
  }
  setCors(res, req);
  return res.status(404).json({ ok: false, error: "Not found" });
});
