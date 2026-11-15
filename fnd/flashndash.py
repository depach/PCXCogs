"""FlashNDash - temporary posts for Red-DiscordBot.

Flow:
    1. Someone posts ANY message in the configured channel (bots are ignored).
    2. The bot selects a duration using DM buttons or a duration in the post text.
    3. The bot optionally posts a message pinging the configured role.
  4. When time is up, the original message AND the ping message are deleted.

Pending deletions are stored in Config, so they survive bot restarts.
"""
from __future__ import annotations

import asyncio
import logging
import re
import textwrap
import time
from typing import Optional

import discord
from discord.ext import tasks
from redbot.core import Config, commands
from redbot.core.bot import Red

log = logging.getLogger("red.flashndash")

REPLY_TIMEOUT = 300  # seconds the user has to press a button
CLEANUP_INTERVAL = 15  # seconds between deletion sweeps
DEFAULT_OPTIONS = [5, 10, 15, 30]
DEFAULT_MINUTES = 5
MAX_OPTIONS = 10
MAX_DURATION_MINUTES = 10080
DURATION_PATTERN = re.compile(
    r"(?<!\w)(\d+)\s*(?:m|min|mins|minute|minutes)\b", re.IGNORECASE
)


def fmt_minutes(minutes: int) -> str:
    return f"{minutes} minute{'s' if minutes != 1 else ''}"


def duration_from_text(text: str, default: int) -> int:
    """Return the first valid minute duration in text, or the configured default."""
    for match in DURATION_PATTERN.finditer(text):
        minutes = int(match.group(1))
        if 1 <= minutes <= MAX_DURATION_MINUTES:
            return minutes
    return default


class DurationView(discord.ui.View):
    """Row of buttons, one per duration option. Only the poster can press them."""

    def __init__(self, user_id: int, options: list[int], default: int, timeout: float):
        super().__init__(timeout=timeout)
        self.user_id = user_id
        self.choice: Optional[int] = None
        for minutes in options:
            button = discord.ui.Button(
                label=f"{minutes} min",
                style=(
                    discord.ButtonStyle.primary
                    if minutes == default
                    else discord.ButtonStyle.secondary
                ),
            )
            button.callback = self._make_callback(minutes)
            self.add_item(button)

    def _make_callback(self, minutes: int):
        async def callback(interaction: discord.Interaction):
            self.choice = minutes
            await interaction.response.edit_message(
                content=f"Got it! Your post will be deleted in **{fmt_minutes(minutes)}**.",
                view=None,
            )
            self.stop()

        return callback

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user_id


class FlashNDash(commands.Cog):
    """Temporary channel posts that delete themselves after a configured duration."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=8675309144, force_registration=True)
        self.config.register_guild(
            channel=None,  # channel ID to watch
            role=None,  # role ID to ping
            options=list(DEFAULT_OPTIONS),  # minutes offered to the poster
            default_minutes=DEFAULT_MINUTES,  # used if no button is pressed / DMs closed
            duration_mode="dm",  # dm buttons or a duration in the post text
            role_ping_enabled=True,
        )
        # List of dicts: guild_id, channel_id, image_id, notify_id, delete_at
        # ("image_id" is the ID of the user's original message.)
        self.config.register_global(pending=[])

        self._tasks: set = set()

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #
    async def cog_load(self) -> None:
        self.cleanup_loop.start()

    def cog_unload(self) -> None:
        self.cleanup_loop.cancel()
        for task in list(self._tasks):
            task.cancel()

    # ------------------------------------------------------------------ #
    # Listeners
    # ------------------------------------------------------------------ #
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.guild is None or message.author.bot:
            return
        # Ignore joins, pins, boosts, etc.
        if message.type not in (discord.MessageType.default, discord.MessageType.reply):
            return
        watched = await self.config.guild(message.guild).channel()
        if watched is None or message.channel.id != watched:
            return
        # Don't treat bot commands (e.g. admins running [p]fnd settings) as posts.
        ctx = await self.bot.get_context(message)
        if ctx.valid:
            return

        task = asyncio.create_task(self._handle_post(message))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent) -> None:
        """If the poster (or a mod) deletes the post early, clean up the ping too."""
        if payload.guild_id is None:
            return
        entry = None
        async with self.config.pending() as pending:
            for e in pending:
                if e["image_id"] == payload.message_id:
                    entry = e
                    pending.remove(e)
                    break
        if entry and entry.get("notify_id"):
            await self._delete_message(entry["channel_id"], entry["notify_id"])

    # ------------------------------------------------------------------ #
    # Core flow
    # ------------------------------------------------------------------ #
    async def _handle_post(self, message: discord.Message) -> None:
        try:
            await self._handle_post_inner(message)
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("Error handling post %s", message.id)

    async def _handle_post_inner(self, message: discord.Message) -> None:
        guild = message.guild
        channel = message.channel
        author = message.author
        settings = await self.config.guild(guild).all()
        default_minutes = settings["default_minutes"]

        # Register immediately with a fallback deletion time, so the post is
        # never left up forever if the bot dies while waiting for the user.
        entry = {
            "guild_id": guild.id,
            "channel_id": channel.id,
            "image_id": message.id,
            "notify_id": None,
            "delete_at": time.time() + REPLY_TIMEOUT + default_minutes * 60 + 30,
        }
        async with self.config.pending() as pending:
            pending.append(entry)

        minutes, dm_sent = await self._ask_minutes(message, settings)

        # Post may have been deleted while we waited for the user.
        if not await self._update_entry(message.id):
            return

        delete_at = time.time() + minutes * 60

        # Ping the role
        notify_id = None
        role = (
            guild.get_role(settings["role"])
            if settings["role"] and settings["role_ping_enabled"]
            else None
        )
        if role is not None:
            content = (
                f"{role.mention} {author.mention} just posted in {channel.mention} - "
                f"[go check it out!]({message.jump_url})\n"
                f"-# Disappears <t:{int(delete_at)}:R>"
            )
            try:
                notify = await channel.send(
                    content,
                    allowed_mentions=discord.AllowedMentions(
                        roles=[role], users=False, everyone=False
                    ),
                )
                notify_id = notify.id
            except discord.HTTPException:
                log.warning("Could not send role ping in channel %s", channel.id, exc_info=True)

        # Lock in the real deletion time
        still_there = await self._update_entry(
            message.id, delete_at=delete_at, notify_id=notify_id
        )
        if not still_there and notify_id:
            # Post was deleted right as we were pinging; remove the ping too.
            await self._delete_message(channel.id, notify_id)
            return

        if not dm_sent:
            try:
                await channel.send(
                    f"{author.mention} I couldn't DM you, so your post will stay up for "
                    f"the default **{fmt_minutes(minutes)}**. (Enable DMs from server "
                    f"members to choose your own time next time.)",
                    allowed_mentions=discord.AllowedMentions(users=[author]),
                    delete_after=30,
                )
            except discord.HTTPException:
                pass

    async def _ask_minutes(self, message: discord.Message, settings: dict) -> tuple:
        """Select a duration using the configured mode; return duration and DM status."""
        user = message.author
        options = settings["options"]
        default = settings["default_minutes"]

        if settings["duration_mode"] == "caption":
            return duration_from_text(message.clean_content, default), True

        preview = ""
        if message.clean_content:
            snippet = textwrap.shorten(message.clean_content, width=80, placeholder="…")
            preview = f"> {snippet}\n" if snippet else ""

        view = DurationView(user.id, options, default, REPLY_TIMEOUT)
        text = (
            f"Hey! I saw your post in {message.channel.mention} ({message.jump_url}).\n"
            f"{preview}"
            f"**How long should I leave it up?** Tap a button below. If you don't pick "
            f"within {REPLY_TIMEOUT // 60} minutes, I'll use the default of "
            f"**{fmt_minutes(default)}**."
        )
        try:
            dm = await user.create_dm()
            prompt = await dm.send(text, view=view)
        except (discord.Forbidden, discord.HTTPException):
            return default, False

        await view.wait()
        if view.choice is not None:
            return view.choice, True

        # Timed out
        try:
            await prompt.edit(
                content=f"No answer, so I'll leave your post up for the default "
                f"**{fmt_minutes(default)}**.",
                view=None,
            )
        except discord.HTTPException:
            pass
        return default, True

    # ------------------------------------------------------------------ #
    # Pending-deletion storage / cleanup
    # ------------------------------------------------------------------ #
    async def _update_entry(self, message_id: int, **fields) -> bool:
        """Update a pending entry. Returns False if it no longer exists."""
        async with self.config.pending() as pending:
            for e in pending:
                if e["image_id"] == message_id:
                    e.update(fields)
                    return True
        return False

    @tasks.loop(seconds=CLEANUP_INTERVAL)
    async def cleanup_loop(self) -> None:
        try:
            now = time.time()
            pending = await self.config.pending()
            due = [e for e in pending if e["delete_at"] <= now]
            finished = []
            for entry in due:
                if await self._delete_entry(entry):
                    finished.append(entry["image_id"])
            if finished:
                async with self.config.pending() as pending:
                    pending[:] = [e for e in pending if e["image_id"] not in finished]
        except Exception:
            log.exception("Error in cleanup loop")

    @cleanup_loop.before_loop
    async def _before_cleanup(self) -> None:
        await self.bot.wait_until_ready()

    async def _delete_entry(self, entry: dict) -> bool:
        """Delete the post + ping. Returns False only if we should retry later."""
        ok = True
        for key in ("image_id", "notify_id"):
            mid = entry.get(key)
            if mid:
                ok &= await self._delete_message(entry["channel_id"], mid)
        return ok

    async def _delete_message(self, channel_id: int, message_id: int) -> bool:
        channel = self.bot.get_channel(channel_id)
        if channel is None:
            return True  # channel is gone; nothing to delete
        try:
            await channel.get_partial_message(message_id).delete()
        except discord.NotFound:
            pass
        except discord.Forbidden:
            log.warning("Missing permission to delete message %s in %s", message_id, channel_id)
        except discord.HTTPException:
            log.warning(
                "Failed to delete %s in %s; will retry", message_id, channel_id, exc_info=True
            )
            return False
        return True

    # ------------------------------------------------------------------ #
    # Settings commands
    # ------------------------------------------------------------------ #
    @commands.group(name="flashndash", aliases=["fnd"])
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def fnd(self, ctx: commands.Context):
        """Configure FlashNDash."""

    @fnd.command(name="channel")
    async def fnd_channel(
        self, ctx: commands.Context, channel: Optional[discord.TextChannel] = None
    ):
        """Set the channel to watch. Run with no argument to disable."""
        if channel is None:
            await self.config.guild(ctx.guild).channel.set(None)
            return await ctx.send("Watched channel cleared - FlashNDash is now inactive.")
        await self.config.guild(ctx.guild).channel.set(channel.id)
        await ctx.send(f"Now watching {channel.mention} for posts.")

    @fnd.command(name="role")
    async def fnd_role(self, ctx: commands.Context, role: Optional[discord.Role] = None):
        """Set the role to ping on new posts. Run with no argument to disable pings."""
        if role is None:
            await self.config.guild(ctx.guild).role.set(None)
            return await ctx.send("Role cleared - no pings will be sent.")
        await self.config.guild(ctx.guild).role.set(role.id)
        await ctx.send(f"I'll ping **{role.name}** when someone posts.")

    @fnd.command(name="roleping", aliases=["ping"])
    async def fnd_role_ping(self, ctx: commands.Context, state: str):
        """Turn role pings on or off without changing the configured role."""
        state = state.lower()
        if state not in ("on", "off"):
            return await ctx.send("Choose `on` or `off`.")
        enabled = state == "on"
        await self.config.guild(ctx.guild).role_ping_enabled.set(enabled)
        await ctx.send(f"Role pings are now {'enabled' if enabled else 'disabled'}.")

    @fnd.command(name="durationmode", aliases=["duration"])
    async def fnd_duration_mode(self, ctx: commands.Context, mode: str):
        """Choose DM buttons or duration text in the post caption."""
        mode = mode.lower()
        if mode not in ("dm", "caption"):
            return await ctx.send("Choose `dm` or `caption`.")
        await self.config.guild(ctx.guild).duration_mode.set(mode)
        if mode == "caption":
            message = (
                "Caption duration mode enabled. Include a duration such as `5m` or `10m` "
                "in the post text; posts without one use the default."
            )
        else:
            message = "DM button duration mode enabled."
        await ctx.send(message)

    @fnd.command(name="options")
    async def fnd_options(self, ctx: commands.Context, *minutes: int):
        """Set the durations (in minutes) offered to posters.

        Example: `[p]fnd options 5 10 15 30`
        """
        opts = sorted(set(minutes))
        if (
            not opts
            or len(opts) > MAX_OPTIONS
            or opts[0] < 1
            or opts[-1] > MAX_DURATION_MINUTES
        ):
            return await ctx.send(
                f"Give me 1-{MAX_OPTIONS} values between 1 and {MAX_DURATION_MINUTES}, e.g. "
                f"`{ctx.clean_prefix}fnd options 5 10 15 30`."
            )
        await self.config.guild(ctx.guild).options.set(opts)
        default = await self.config.guild(ctx.guild).default_minutes()
        note = ""
        if default not in opts:
            default = opts[0]
            await self.config.guild(ctx.guild).default_minutes.set(default)
            note = f" The default was reset to **{default}** since it wasn't in the list."
        await ctx.send(f"Options set to: {', '.join(str(o) for o in opts)} minutes.{note}")

    @fnd.command(name="defaultminutes")
    async def fnd_default(self, ctx: commands.Context, minutes: int):
        """Set the default duration when no choice or caption duration is provided.

        Must be one of the configured options.
        """
        opts = await self.config.guild(ctx.guild).options()
        if minutes not in opts:
            return await ctx.send(
                f"The default must be one of the options: {', '.join(str(o) for o in opts)}."
            )
        await self.config.guild(ctx.guild).default_minutes.set(minutes)
        await ctx.send(f"Default duration set to **{fmt_minutes(minutes)}**.")

    @fnd.command(name="settings")
    async def fnd_settings(self, ctx: commands.Context):
        """Show the current settings."""
        s = await self.config.guild(ctx.guild).all()
        channel = ctx.guild.get_channel(s["channel"]) if s["channel"] else None
        role = ctx.guild.get_role(s["role"]) if s["role"] else None
        pending = [e for e in await self.config.pending() if e["guild_id"] == ctx.guild.id]
        await ctx.send(
            f"**FlashNDash settings**\n"
            f"Channel: {channel.mention if channel else '*not set*'}\n"
            f"Role: {role.mention if role else '*not set*'}\n"
            f"Role pings: {'enabled' if s['role_ping_enabled'] else 'disabled'}\n"
            f"Duration mode: {s['duration_mode']}\n"
            f"Options: {', '.join(str(o) for o in s['options'])} minutes\n"
            f"Default: {s['default_minutes']} minutes\n"
            f"Posts awaiting deletion: {len(pending)}",
            allowed_mentions=discord.AllowedMentions.none(),
        )
