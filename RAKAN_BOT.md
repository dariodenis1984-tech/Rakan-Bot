# Rakan Bot

Rakan Bot announces new Wild Rift patch notes in a Discord channel.

## What it does

- Checks Riot Games' official patch-notes index every 30 minutes.
- Posts a red Discord embed containing the patch title as a link.
- Mentions `@everyone` for each newly detected patch.
- Saves the last announced patch in `data/rakan_patch_state.json` so restarts do not repeat announcements.
- Performs an initial sync without announcing the patch that is already live when the bot starts for the first time.

Official source:
<https://wildrift.leagueoflegends.com/en-us/news/tags/patch-notes/>

## Discord setup

1. Create a bot in the Discord Developer Portal and add its token as the Replit Secret `DISCORD_BOT_TOKEN`.
2. Invite the bot to the Wild Rift server with these permissions in channel `1538342201631707197`:
   - View Channel
   - Send Messages
   - Embed Links
   - Mention Everyone
3. Start the **Rakan Bot** workflow.

The bot does not need Message Content intent because it only posts announcements and does not read Discord messages.

## Run

```bash
python main.py
```

The polling interval and channel are intentionally fixed to the requested values. The state file location can be changed with `RAKAN_STATE_PATH` if the runtime needs a different persistent directory.