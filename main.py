"""Rakan Bot - Wild Rift patch notes notifier for Discord."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from dataclasses import asdict, dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

import discord
from discord.ext import tasks
from aiohttp import web

BOT_NAME = "Rakan Bot"
PATCH_NOTES_URL = (
    "https://wildrift.leagueoflegends.com/en-us/news/tags/patch-notes/"
)
PATCH_NOTES_DOMAIN = "wildrift.leagueoflegends.com"
DISCORD_CHANNEL_ID = 1538342201631707197
POLL_INTERVAL_MINUTES = 30
EMBED_RED = discord.Colour.from_rgb(220, 53, 69)
EMBED_IMAGE_URL = (
    "https://cdn.discordapp.com/attachments/1513208957651386552/"
    "1538578334022238320/wr-cb1-announcementarticle-banner-1920x1080.png"
    "?ex=6a83303c&is=6a81debc&hm=f59ec1c0c8a362ac3c910ba49bf8d6fa571e644f744af8231882e14c37acce03&"
)
STATE_PATH = Path(
    os.getenv("RAKAN_STATE_PATH", "data/rakan_patch_state.json")
)
USER_AGENT = f"{BOT_NAME}/1.0 (+https://wildrift.leagueoflegends.com/)"

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(BOT_NAME)


@dataclass(frozen=True)
class PatchNote:
    title: str
    url: str


@dataclass
class BotState:
    initialized: bool = False
    last_posted_url: str | None = None


class PatchNotesParser(HTMLParser):
    """Extract patch-note cards from Riot's public patch-notes index."""

    _PATCH_TITLE = re.compile(
        r"Wild Rift Patch Notes\s+\d+(?:\.\d+)*[a-z]?",
        re.IGNORECASE,
    )

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._current_href: str | None = None
        self._current_aria_label: str | None = None
        self._current_text: list[str] = []
        self.notes: list[PatchNote] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        if tag.lower() != "a":
            return
        href = dict(attrs).get("href")
        if href:
            self._current_href = href
            self._current_aria_label = dict(attrs).get("aria-label")
            self._current_text = []

    def handle_data(self, data: str) -> None:
        if self._current_href is not None:
            self._current_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "a" or self._current_href is None:
            return

        card_text = " ".join("".join(self._current_text).split())
        title_source = self._current_aria_label or card_text
        title_match = self._PATCH_TITLE.search(title_source)
        url = urljoin(PATCH_NOTES_URL, self._current_href)
        parsed_url = urlparse(url)
        if (
            parsed_url.netloc == PATCH_NOTES_DOMAIN
            and parsed_url.path.startswith("/en-us/news/game-updates/")
            and title_match
        ):
            note = PatchNote(title=title_match.group(0), url=url)
            if note not in self.notes:
                self.notes.append(note)

        self._current_href = None
        self._current_aria_label = None
        self._current_text = []


def fetch_patch_notes() -> list[PatchNote]:
    request = Request(
        PATCH_NOTES_URL,
        headers={
            "Accept": "text/html",
            "User-Agent": USER_AGENT,
        },
    )
    with urlopen(request, timeout=30) as response:
        content_type = response.headers.get_content_type()
        if content_type != "text/html":
            raise RuntimeError(
                f"Expected HTML from Riot, received {content_type!r}"
            )
        html = response.read().decode("utf-8", errors="replace")

    parser = PatchNotesParser()
    parser.feed(html)
    parser.close()
    if not parser.notes:
        raise RuntimeError("Riot's patch-notes page contained no patch notes")
    return parser.notes


def load_state() -> BotState:
    if not STATE_PATH.exists():
        return BotState()

    try:
        raw: Any = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("state must be a JSON object")
        initialized = raw.get("initialized")
        last_posted_url = raw.get("last_posted_url")
        if not isinstance(initialized, bool) or (
            last_posted_url is not None and not isinstance(last_posted_url, str)
        ):
            raise ValueError("state has an invalid shape")
        return BotState(
            initialized=initialized,
            last_posted_url=last_posted_url,
        )
    except (OSError, json.JSONDecodeError, ValueError) as error:
        raise RuntimeError(f"Unable to read state file {STATE_PATH}: {error}") from error


def save_state(state: BotState) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = STATE_PATH.with_suffix(f"{STATE_PATH.suffix}.tmp")
    temporary_path.write_text(
        json.dumps(asdict(state), indent=2) + "\n",
        encoding="utf-8",
    )
    temporary_path.replace(STATE_PATH)


def find_unposted_notes(
    notes: list[PatchNote], state: BotState
) -> list[PatchNote]:
    if not state.initialized:
        return []

    if not state.last_posted_url:
        return list(reversed(notes))

    try:
        last_index = next(
            index
            for index, note in enumerate(notes)
            if note.url == state.last_posted_url
        )
    except StopIteration:
        # If Riot removes an old card from the index, announce only the current
        # card rather than replaying the entire historical feed.
        return notes[:1]

    return list(reversed(notes[:last_index]))


class RakanBot(discord.Client):
    def __init__(self) -> None:
        intents = discord.Intents.none()
        intents.guilds = True
        super().__init__(intents=intents)
        self.state = load_state()
        async def setup_hook(self) -> None:
        app = web.Application()

        async def health(request: web.Request) -> web.Response:
            return web.Response(text="Rakan Bot is online!")

        app.router.add_get("/", health)
        app.router.add_get("/health", health)

        runner = web.AppRunner(app)
        await runner.setup()

        port = int(os.getenv("PORT", "10000"))
        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()

        logger.info("Health server listening on port %s", port)
    async def on_ready(self) -> None:
        if self.user is not None:
            logger.info("Logged in as %s (%s)", self.user, self.user.id)
        if not self.patch_check.is_running():
            self.patch_check.start()

    @tasks.loop(minutes=POLL_INTERVAL_MINUTES)
    async def patch_check(self) -> None:
        try:
            notes = await asyncio.to_thread(fetch_patch_notes)
            await self.process_patch_notes(notes)
        except Exception:
            logger.exception("Patch-note check failed; will retry next cycle")

    @patch_check.before_loop
    async def wait_for_bot_ready(self) -> None:
        await self.wait_until_ready()

    async def process_patch_notes(self, notes: list[PatchNote]) -> None:
        if not notes:
            return

        if not self.state.initialized:
            self.state.initialized = True
            self.state.last_posted_url = notes[0].url
            save_state(self.state)
            logger.info(
                "Initial sync complete at %s; waiting for the next new patch",
                notes[0].title,
            )
            return

        new_notes = find_unposted_notes(notes, self.state)
        if not new_notes:
            logger.info("No new Wild Rift patch notes found")
            return

        channel = self.get_channel(DISCORD_CHANNEL_ID)
        if channel is None:
            channel = await self.fetch_channel(DISCORD_CHANNEL_ID)
        if not isinstance(channel, discord.abc.Messageable):
            raise RuntimeError(
                f"Discord channel {DISCORD_CHANNEL_ID} is not messageable"
            )

        for note in new_notes:
            embed = discord.Embed(
                title=note.title,
                url=note.url,
                colour=EMBED_RED,
            )
            embed.set_image(url=EMBED_IMAGE_URL)
            embed.set_footer(text="Official Wild Rift patch notes")
            await channel.send(
                content="@everyone",
                embed=embed,
                allowed_mentions=discord.AllowedMentions(everyone=True),
            )
            self.state.last_posted_url = note.url
            save_state(self.state)
            logger.info("Posted %s", note.title)


def main() -> None:
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        raise RuntimeError(
            "DISCORD_BOT_TOKEN is not configured. Add the bot token as a Replit Secret."
        )

    bot = RakanBot()
    bot.run(token, log_handler=None)


if __name__ == "__main__":
    main()
