# Rakan Bot

Rakan Bot watches Riot Games' official Wild Rift patch notes and announces new patches in a configured Discord channel.

## Run & Operate

- `python main.py` — run Rakan Bot locally
- `python3 -m pip install -r requirements.txt` — install the deployment dependencies
- Required secret: `DISCORD_BOT_TOKEN`

## Stack

- Python 3.11
- Discord client: `discord.py` 2.7.1
- Deployment: Reserved VM background worker running `python3 -u main.py`

## Where things live

- `main.py` — Discord client, Riot patch-note parser, 30-minute polling loop, and deduplication state
- `requirements.txt` — deployment dependency list
- `pyproject.toml` / `uv.lock` — local Python environment and locked Discord dependency
- `data/rakan_patch_state.json` — runtime checkpoint for the last announced patch (created automatically)

## Architecture decisions

- The bot reads the official Riot patch-notes index instead of scraping third-party feeds.
- A local JSON checkpoint prevents duplicate announcements across polling cycles and restarts.
- The first successful check seeds the current patch without announcing historical content; later new patches are announced in chronological order.
- Network fetching runs in a worker thread so it cannot block Discord's async event loop.
- The deployment uses a Reserved VM background worker because Discord gateway connections must stay online continuously.

## Product

Rakan Bot logs into Discord, checks Riot's official Wild Rift patch-notes page every 30 minutes, and posts a red embed with the patch title and link while mentioning `@everyone` for newly published patches.

## User preferences

_Populate as you build — explicit user instructions worth remembering across sessions._

## Gotchas

- The Discord bot must have View Channel, Send Messages, Embed Links, and Mention Everyone permissions in channel `1538342201631707197`.
- The bot token is stored as the `DISCORD_BOT_TOKEN` Replit Secret and must never be committed to source.
- Publishing should use Reserved VM / background worker settings, not Autoscale or a web server configuration.

## Pointers

- See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details
