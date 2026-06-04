import { Router, type Request, type Response } from "express";
import { getDemoUrl, isDemoReady } from "../lib/activegraph-process";

const router = Router();

/** Forward a GET request to the demo server, returning its JSON. */
async function proxyGet(
  req: Request,
  res: Response,
  demoPath: string,
): Promise<void> {
  if (!isDemoReady()) {
    res.status(503).json({ error: "ActiveGraph runtime is initialising — try again in a moment" });
    return;
  }
  const url = new URL(getDemoUrl() + demoPath);
  // Forward all query params
  Object.entries(req.query as Record<string, string>).forEach(([k, v]) =>
    url.searchParams.set(k, v),
  );
  try {
    const upstream = await fetch(url.toString());
    const data = await upstream.json();
    res.status(upstream.status).json(data);
  } catch (err) {
    res.status(502).json({ error: "Demo server unreachable" });
  }
}

/** Forward a POST request to the demo server with a JSON body. */
async function proxyPost(
  req: Request,
  res: Response,
  demoPath: string,
): Promise<void> {
  if (!isDemoReady()) {
    res.status(503).json({ error: "ActiveGraph runtime is initialising — try again in a moment" });
    return;
  }
  try {
    const upstream = await fetch(getDemoUrl() + demoPath, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req.body ?? {}),
    });
    const data = await upstream.json();
    res.status(upstream.status).json(data);
  } catch (err) {
    res.status(502).json({ error: "Demo server unreachable" });
  }
}

// ── Routes ──────────────────────────────────────────────────────────────────

router.get("/activegraph/trace", (req, res) => proxyGet(req, res, "/trace"));
router.get("/activegraph/graph", (req, res) => proxyGet(req, res, "/graph"));
router.get("/activegraph/packs", (req, res) => proxyGet(req, res, "/packs"));
router.get("/activegraph/frames", (req, res) => proxyGet(req, res, "/frames"));
router.get("/activegraph/summary", (req, res) => proxyGet(req, res, "/summary"));

router.get("/activegraph/chat/config", (req, res) => proxyGet(req, res, "/chat/config"));
router.get("/activegraph/secrets", (req, res) => proxyGet(req, res, "/secrets"));
router.get("/activegraph/profile", (req, res) => proxyGet(req, res, "/profile"));

router.post("/activegraph/chat", (req, res) => proxyPost(req, res, "/chat"));
router.post("/activegraph/reset", (req, res) => proxyPost(req, res, "/reset"));
router.post("/activegraph/chat/config", (req, res) => proxyPost(req, res, "/chat/config"));
router.post("/activegraph/secrets", (req, res) => proxyPost(req, res, "/secrets"));
router.post("/activegraph/profile", (req, res) => proxyPost(req, res, "/profile"));
router.post("/activegraph/profile/seed", (req, res) => proxyPost(req, res, "/profile/seed"));
router.post("/activegraph/profile/personality", (req, res) => proxyPost(req, res, "/profile/personality"));
router.post("/activegraph/profile/goal", (req, res) => proxyPost(req, res, "/profile/goal"));
router.post("/activegraph/profile/goal/delete", (req, res) => proxyPost(req, res, "/profile/goal/delete"));
router.post("/activegraph/profile/instruction", (req, res) => proxyPost(req, res, "/profile/instruction"));
router.post("/activegraph/profile/instruction/delete", (req, res) => proxyPost(req, res, "/profile/instruction/delete"));

export default router;
