import { spawn, type ChildProcess } from "child_process";
import path from "path";
import { fileURLToPath } from "url";
import { logger } from "./logger";

const DEMO_PORT = parseInt(process.env["ACTIVEGRAPH_PORT"] ?? "7788", 10);
const DEMO_URL = `http://127.0.0.1:${DEMO_PORT}`;

let _proc: ChildProcess | null = null;
let _ready = false;

export function getDemoUrl(): string {
  return DEMO_URL;
}

export function isDemoReady(): boolean {
  return _ready;
}

export function startDemoServer(): void {
  if (_proc) return;

  // import.meta.url resolves to the built dist/index.mjs (everything is bundled into one file)
  // __dirname → artifacts/api-server/dist → go 3 levels up to reach the workspace root
  const repoRoot = path.resolve(process.cwd(), "../../");
  const script = path.join(repoRoot, "packs", "demo_server.py");

  logger.info({ script, port: DEMO_PORT }, "Starting ActiveGraph demo server");

  _proc = spawn("python3", [script, "--port", String(DEMO_PORT)], {
    cwd: repoRoot,
    env: { ...process.env, ACTIVEGRAPH_PORT: String(DEMO_PORT) },
    stdio: ["ignore", "pipe", "pipe"],
  });

  _proc.stdout?.on("data", (chunk: Buffer) => {
    const line = chunk.toString().trim();
    if (line.includes("Runtime ready")) _ready = true;
    logger.info({ source: "demo_server" }, line);
  });

  _proc.stderr?.on("data", (chunk: Buffer) => {
    logger.warn({ source: "demo_server" }, chunk.toString().trim());
  });

  _proc.on("exit", (code) => {
    logger.warn({ code }, "ActiveGraph demo server exited");
    _ready = false;
    _proc = null;
    // Auto-restart after 3 s
    setTimeout(startDemoServer, 3000);
  });

  // Poll until ready (up to 30 s)
  let attempts = 0;
  const poll = () => {
    fetch(`${DEMO_URL}/health`)
      .then(() => {
        _ready = true;
        logger.info("ActiveGraph demo server is healthy");
      })
      .catch(() => {
        attempts++;
        if (attempts < 60) setTimeout(poll, 500);
        else logger.error("ActiveGraph demo server failed to start within 30 s");
      });
  };
  setTimeout(poll, 1500);
}
