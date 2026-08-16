# Rakan Bot

Rakan Bot watches Riot Games' official Wild Rift patch notes and announces new patches in a configured Discord channel.

## Run & Operate

- `pnpm --filter @workspace/api-server run dev` — run the API server (port 5000)
- `pnpm run typecheck` — full typecheck across all packages
- `pnpm run build` — typecheck + build all packages
- `pnpm --filter @workspace/api-spec run codegen` — regenerate API hooks and Zod schemas from the OpenAPI spec
- `pnpm --filter @workspace/db run push` — push DB schema changes (dev only)
- Required env: `DATABASE_URL` — Postgres connection string
- `python main.py` — run Rakan Bot locally or through the Rakan Bot workflow
- Required secret: `DISCORD_BOT_TOKEN`

## Stack

- pnpm workspaces, Node.js 24, TypeScript 5.9
- API: Express 5
- DB: PostgreSQL + Drizzle ORM
- Validation: Zod (`zod/v4`), `drizzle-zod`
- API codegen: Orval (from OpenAPI spec)
- Build: esbuild (CJS bundle)

## Where things live

- `main.py` — Discord client, Riot patch-note parser, 30-minute polling loop, and deduplication state
- `pyproject.toml` / `uv.lock` — Python runtime and Discord dependency
- `data/rakan_patch_state.json` — runtime checkpoint for the last announced patch (created automatically)

## Architecture decisions

- The bot reads the official Riot patch-notes index instead of scraping third-party feeds.
- A local JSON checkpoint prevents duplicate announcements across polling cycles and restarts.
- The first successful check seeds the current patch without announcing historical content; later new patches are announced in chronological order.
- Network fetching runs in a worker thread so it cannot block Discord's async event loop.

## Product

Rakan Bot logs into Discord, checks Riot's official Wild Rift patch-notes page every 30 minutes, and posts a red embed with the patch title and link while mentioning `@everyone` for newly published patches.

## User preferences

_Populate as you build — explicit user instructions worth remembering across sessions._

## Gotchas

- The Discord bot must have View Channel, Send Messages, Embed Links, and Mention Everyone permissions in channel `1538342201631707197`.
- The bot token is stored as the `DISCORD_BOT_TOKEN` Replit Secret and must never be committed to source.

## Pointers

- See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details
