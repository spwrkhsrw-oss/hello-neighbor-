import os

import discord
from discord.ext import commands

# Role ID that is allowed to use .ayochill
AUTHORIZED_ROLE_ID = 1533701155580809377

# Command prefix
PREFIX = "."

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("Bot is ready.")


def has_authorized_role(member: discord.Member) -> bool:
    """Return True if the member has the required authorization role."""
    return any(role.id == AUTHORIZED_ROLE_ID for role in member.roles)


@bot.command(name="ayochill")
@commands.guild_only()
async def ayochill(ctx: commands.Context, role_id: int, user_id: int):
    """
    Usage:
        .ayochill [role_id] [user_id]

    Gives the specified role to the specified server member.
    Only members with AUTHORIZED_ROLE_ID can use it.
    """

    # Check that the person running the command has the required role.
    if not isinstance(ctx.author, discord.Member):
        return

    if not has_authorized_role(ctx.author):
        await ctx.reply(
            "❌ You do not have permission to use `.ayochill`.",
            mention_author=False,
        )
        return

    # Find the role in this server.
    role = ctx.guild.get_role(role_id)
    if role is None:
        await ctx.reply(
            f"❌ I couldn't find a role with ID `{role_id}` in this server.",
            mention_author=False,
        )
        return

    # Find the target member in this server.
    try:
        target = ctx.guild.get_member(user_id)
        if target is None:
            target = await ctx.guild.fetch_member(user_id)
    except discord.NotFound:
        await ctx.reply(
            f"❌ I couldn't find a member with ID `{user_id}` in this server.",
            mention_author=False,
        )
        return
    except discord.HTTPException:
        await ctx.reply(
            "❌ Discord returned an error while looking up that member.",
            mention_author=False,
        )
        return

    # Discord only allows a bot to manage roles below its highest role.
    me = ctx.guild.me
    if me is None:
        await ctx.reply(
            "❌ I couldn't determine my bot member in this server.",
            mention_author=False,
        )
        return

    if role >= me.top_role:
        await ctx.reply(
            f"❌ I can't give `{role.name}` because that role is at or above my highest role.",
            mention_author=False,
        )
        return

    if target == me:
        await ctx.reply(
            "❌ I can't give a role to myself.",
            mention_author=False,
        )
        return

    if role in target.roles:
        await ctx.reply(
            f"ℹ️ {target.mention} already has the role {role.mention}.",
            mention_author=False,
        )
        return

    try:
        await target.add_roles(
            role,
            reason=f".ayochill used by {ctx.author} ({ctx.author.id})",
        )
    except discord.Forbidden:
        await ctx.reply(
            "❌ I don't have permission to manage that role. "
            "Make sure the bot has **Manage Roles** and its highest role is above the role you're giving.",
            mention_author=False,
        )
        return
    except discord.HTTPException:
        await ctx.reply(
            "❌ Discord rejected the role change. Please try again.",
            mention_author=False,
        )
        return

    await ctx.reply(
        f"✅ Gave {role.mention} to {target.mention}.",
        mention_author=False,
    )


@ayochill.error
async def ayochill_error(ctx: commands.Context, error: commands.CommandError):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.reply(
            "Usage: `.ayochill [role_id] [user_id]`\n"
            "Example: `.ayochill 123456789012345678 987654321098765432`",
            mention_author=False,
        )
    elif isinstance(error, commands.BadArgument):
        await ctx.reply(
            "❌ Role ID and user ID must both be numbers.\n"
            "Usage: `.ayochill [role_id] [user_id]`",
            mention_author=False,
        )
    elif isinstance(error, commands.NoPrivateMessage):
        await ctx.reply(
            "❌ This command can only be used inside a server.",
            mention_author=False,
        )
    else:
        # Don't expose internal errors to users, but log them for the bot owner.
        print(f"Command error: {error}")


token = os.getenv("DISCORD_TOKEN")

if not token:
    raise RuntimeError(
        "DISCORD_TOKEN is not set. Set your Discord bot token as an environment variable."
    )

bot.run(token)
