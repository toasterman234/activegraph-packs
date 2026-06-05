---
name: Dual-target (Replit + off-platform) portability
description: How this repo stays runnable both on Replit and from a plain git checkout without two code paths.
---

# Dual-target portability pattern

The repo must run unchanged on Replit AND from a plain `git clone` + `pnpm`/`pip`.
The seam that makes this work, and the reasoning behind each choice:

- **Env vars with fallbacks, not hard requirements.** Replit injects `PORT` and
  `BASE_PATH` into each artifact; off-platform they're absent. The UI
  `vite.config.ts` reads them but defaults to `5173` / `/` when missing. Never
  `throw` on a missing platform-injected env var in code that must also run
  off-platform.

- **`REPL_ID` is the on-Replit signal.** Gate platform-only behavior on
  `process.env.REPL_ID !== undefined`.

- **`/api` reaches the API server differently per target.** On Replit the
  platform path-routes `/api` to the API-server artifact (the browser never goes
  through Vite for it), so Vite needs NO proxy. Off-platform the UI runs on its
  own port, so Vite must `server.proxy` `/api` → the API server. The proxy is
  added ONLY when `REPL_ID` is undefined — adding it on Replit is harmless (those
  requests never hit Vite) but the gate keeps intent clear and avoids a wrong
  hardcoded target.
  **Why:** the UI calls root-relative `/api/...` paths (orval client, no base URL
  set); without the proxy, off-platform those hit Vite's dev server instead of
  the API server.

- **Replit editor plugins load only on Replit dev.** `@replit/vite-plugin-*`
  (runtime-error-modal, cartographer, dev-banner) are dynamically imported only
  when `REPL_ID` is set and `NODE_ENV !== production`, wrapped in `.catch(() => [])`.
  They stay as devDependencies (harmless to install) but never activate in a
  plain checkout or a production build.

- **One-command local run.** Root `pnpm dev` → `node scripts/dev.mjs`: a
  dependency-free launcher that spawns the API server (which itself spawns the
  Python runtime) + the UI with the right ports, and tears both down on
  exit/Ctrl-C. The API server's `activegraph-process.ts` resolves `repoRoot` as
  `cwd/../../`, which holds because `pnpm --filter` runs the script from the
  package dir.

**How to apply:** when adding a new artifact/service, follow the same shape —
read platform env with a local default, gate Replit-only wiring on `REPL_ID`, and
make cross-service URLs work via platform path-routing on Replit vs. a dev proxy
off-platform. Verify off-platform by running with `env -u REPL_ID` and alternate
ports before claiming portability.
