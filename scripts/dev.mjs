#!/usr/bin/env node
// Dependency-free launcher for the full local demo stack: the API server
// (which spawns the Python ActiveGraph runtime as a subprocess) and the React
// Inspector UI, running together with one command.
//
// Usage: pnpm dev   (from the repo root)
// Prereqs: `pip install -e ".[dev]"` and `pnpm install` must have been run.
// Shells: assumes a POSIX shell (macOS / Linux / Replit). On Windows, use WSL.
//
// Override ports with API_PORT / UI_PORT env vars.
import { spawn } from "node:child_process";

const API_PORT = process.env.API_PORT ?? "5000";
const UI_PORT = process.env.UI_PORT ?? "3000";
const isWindows = process.platform === "win32";

const children = [];
let shuttingDown = false;

function hasExited(child) {
  return child.exitCode !== null || child.signalCode !== null;
}

// Terminate a child and its whole subprocess tree (pnpm -> node -> python).
function killTree(child) {
  if (hasExited(child)) return;
  try {
    if (isWindows) {
      spawn("taskkill", ["/pid", String(child.pid), "/f", "/t"]);
    } else {
      // Each child is its own process-group leader (detached), so a negative
      // PID signals the entire group, reaching grandchildren too.
      process.kill(-child.pid, "SIGTERM");
    }
  } catch {
    try {
      child.kill("SIGTERM");
    } catch {
      /* already gone */
    }
  }
}

function shutdown(code) {
  if (shuttingDown) return;
  shuttingDown = true;
  for (const c of children) killTree(c);

  const deadline = Date.now() + 5000;
  const wait = setInterval(() => {
    if (children.every(hasExited) || Date.now() > deadline) {
      clearInterval(wait);
      process.exit(code);
    }
  }, 100);
}

function run(name, args, env) {
  const child = spawn("pnpm", args, {
    stdio: "inherit",
    env: { ...process.env, ...env },
    // POSIX: own process group so we can signal the whole tree on shutdown.
    detached: !isWindows,
    // Windows: needs a shell to resolve pnpm.cmd.
    shell: isWindows,
  });
  child.on("exit", (exitCode) => {
    if (!shuttingDown) {
      console.log(`\n[${name}] exited (code ${exitCode}). Shutting down...`);
      shutdown(exitCode ?? 0);
    }
  });
  children.push(child);
}

process.on("SIGINT", () => shutdown(0));
process.on("SIGTERM", () => shutdown(0));

run("api", ["--filter", "@workspace/api-server", "run", "dev"], {
  PORT: API_PORT,
});
run("ui", ["--filter", "@workspace/activegraph-ui", "run", "dev"], {
  PORT: UI_PORT,
  BASE_PATH: "/",
  API_PROXY_TARGET: `http://localhost:${API_PORT}`,
});

console.log(
  `\nActiveGraph demo starting:\n` +
    `  UI:             http://localhost:${UI_PORT}\n` +
    `  API server:     http://localhost:${API_PORT}\n` +
    `  Python runtime: http://localhost:7788 (spawned by the API server)\n\n` +
    `Press Ctrl+C to stop.\n`,
);
