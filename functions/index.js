/* Cloud Functions: multipart upload -> Cloud Storage + Firestore
   Public endpoints (behind Hosting rewrite):
     POST /api/upload-audio
     POST /api/upload          // alias for backward compatibility
     GET  /api/health
*/
const functions = require("firebase-functions");
const admin = require("firebase-admin");
const Busboy = require("busboy");

// Initialize Firebase Admin once
if (!admin.apps.length) {
  admin.initializeApp(); // uses default project credentials for your project
}
const db = admin.firestore();
const bucket = admin.storage().bucket();

// CORS allowlist — add your domains here
const ALLOW_ORIGINS = new Set([
  "https://language-academy-3e1de.web.app",
  "https://www.falowen.app",
  "https://falowen.app",
  "http://localhost:5000",
  "http://localhost:3000",
]);

function setCors(res, req) {
  const origin = req.headers.origin || "";
  if (ALLOW_ORIGINS.has(origin)) {
    res.set("Access-Control-Allow-Origin", origin);
    res.set("Vary", "Origin");
  } else {
    // Fallback: useful while testing; tighten in production if you prefer
    res.set("Access-Control-Allow-Origin", "*");
  }
  res.set("Access-Control-Allow-Methods", "POST, OPTIONS, GET");
  res.set("Access-Control-Allow-Headers", "Content-Type, Authorization");
}

async function handleUpload(req, res) {
  // Preflight
  if (req.method === "OPTIONS") {
    setCors(res, req);
    return res.status(204).end();
  }
  if (req.method !== "POST") {
    setCors(res, req);
    return res.status(405).json({ ok: false, error: "Method not allowed" });
  }

  setCors(res, req);

  // Parse multipart/form-data with Busboy
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

  bb.on("file", (_fieldname, file, info) => {
    gotFile = true;
    fileMime = info?.mimeType || fileMime;
    fileName = info?.filename || fileName;
    file.on("data", (data) => {
      fileBuffer = Buffer.concat([fileBuffer, data]);
    });
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
      const ext = fileName.includes(".") ? fileName.split(".").pop() : "webm";
      const storagePath = `pron_inbox/${safeCode}/${ts}.${ext}`;

      await bucket.file(storagePath).save(fileBuffer, {
        contentType: fileMime,
        resumable: false,
        metadata: { cacheControl: "private, max-age=0" },
      });

      const docRef = await db.collection("pron_inbox").add({
        student_code: safeCode,
        storage_path: storagePath,
        mime_type: fileMime,
        file_name: fileName,
        source: source,
        status: "uploaded",
        createdAt: admin.firestore.FieldValue.serverTimestamp(),
      });

      return res.json({ ok: true, id: docRef.id, path: storagePath });
    } catch (e) {
      console.error("upload error:", e);
      return res.status(500).json({ ok: false, error: String(e.message || e) });
    }
  });

  req.pipe(bb);
}

// Simple router so we can add more endpoints later
exports.api = functions.https.onRequest(async (req, res) => {
  const url = (req.path || req.url || "").toLowerCase();

  // Accept BOTH /upload-audio and /upload
  if (url.includes("/upload-audio") || url.includes("/upload")) {
    return handleUpload(req, res);
  }

  if (req.method === "GET" && url.includes("/health")) {
    setCors(res, req);
    return res.json({ ok: true, now: new Date().toISOString() });
  }

  setCors(res, req);
  return res.status(404).json({ ok: false, error: "Not found" });
});
