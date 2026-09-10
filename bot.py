"""
Eclipse Ticket Bot
Panel with dropdown menu (3 categories: Support, Payment, Reseller).
"""

import asyncio
import os
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID") or 0) or None
PANEL_CHANNEL_ID = int(os.getenv("PANEL_CHANNEL_ID") or 0)
STAFF_ROLE_ID = int(os.getenv("STAFF_ROLE_ID") or 0) or None

CATEGORIES = {
    "support": {
        "label": "Support",
        "emoji": "🛠️",
        "description": "Need help",
        "category_id": int(os.getenv("CATEGORY_SUPPORT_ID") or 0),
    },
    "payment": {
        "label": "Payment",
        "emoji": "💳",
        "description": "Purchase or payment help",
        "category_id": int(os.getenv("CATEGORY_PAYMENT_ID") or 0),
    },
    "reseller": {
        "label": "Reseller",
        "emoji": "🤝",
        "description": "Submit application",
        "category_id": int(os.getenv("CATEGORY_RESELLER_ID") or 0),
    },
}

EMBED_COLOR = discord.Color.from_str("#FFFFFF")
BRAND_NAME = "Eclipse"
BANNER_GIF = "https://media.discordapp.net/attachments/1547328699274231858/1547337325057413230/eclipse_banner.gif?ex=6aa3b66e&is=6aa264ee&hm=e2b4488396e6f2057e3b92486ff9e7c3372b5d948a7e5757f610002b87384065&=&width=1280&height=800"

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


# --------------------------------------------------------------------------
# Panel embed
# --------------------------------------------------------------------------

def build_panel_embed() -> discord.Embed:
    embed = discord.Embed(
        title="Open a Ticket",
        description="Select the topic of your request using the dropdown menu below.",
        color=EMBED_COLOR,
    )
    embed.set_author(name=BRAND_NAME)
    embed.set_image(url=BANNER_GIF)
    embed.add_field(
        name="Support Rules",
        value=(
            "**One ticket per topic** — please do not open multiple tickets for the same issue.\n\n"
            "**No staff pinging** — avoid repeatedly mentioning staff members.\n\n"
            "**Be patient** — response times may vary. Extended wait times will be taken into account.\n\n"
            "**Reason required** — any ticket without a clear description will be automatically deleted."
        ),
        inline=False,
    )
    return embed


# --------------------------------------------------------------------------
# Check for existing ticket
# --------------------------------------------------------------------------

def find_existing_ticket(
    guild: discord.Guild, member: discord.Member, category_key: str
) -> Optional[discord.TextChannel]:
    category = guild.get_channel(CATEGORIES[category_key]["category_id"])
    if not isinstance(category, discord.CategoryChannel):
        return None
    marker = f"user:{member.id}"
    for channel in category.text_channels:
        if channel.topic and marker in channel.topic:
            return channel
    return None


# --------------------------------------------------------------------------
# Create ticket channel
# --------------------------------------------------------------------------

async def create_ticket_channel(
    interaction: discord.Interaction, category_key: str, reason: str
) -> None:
    guild = interaction.guild
    member = interaction.user
    info = CATEGORIES[category_key]

    await interaction.response.defer(ephemeral=True)

    existing = find_existing_ticket(guild, member, category_key)
    if existing:
        await interaction.followup.send(
            f"You already have an open ticket in **{info['label']}**: {existing.mention}",
            ephemeral=True,
        )
        return

    category = guild.get_channel(info["category_id"])
    if not isinstance(category, discord.CategoryChannel):
        await interaction.followup.send(
            "Category not found, please contact an administrator.", ephemeral=True
        )
        return

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        member: discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            read_message_history=True,
            attach_files=True,
        ),
        guild.me: discord.PermissionOverwrite(
            view_channel=True, send_messages=True, manage_channels=True
        ),
    }
    if STAFF_ROLE_ID:
        staff_role = guild.get_role(STAFF_ROLE_ID)
        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(
                view_channel=True, send_messages=True, read_message_history=True
            )

    safe_name = "".join(c for c in member.name.lower() if c.isalnum()) or "user"
    channel_name = f"{category_key}-{safe_name}"[:90]

    channel = await guild.create_text_channel(
        name=channel_name,
        category=category,
        overwrites=overwrites,
        topic=f"Ticket {info['label']} | user:{member.id}",
        reason=f"Ticket opened by {member} ({member.id})",
    )

    await interaction.followup.send(
        f"Your ticket has been created: {channel.mention}", ephemeral=True
    )

    ticket_embed = discord.Embed(
        title=f"Ticket — {info['label']}",
        description=(
            f"Hello {member.mention}, a staff member will respond as soon as possible.\n\n"
            f"**Reason:**\n{reason}"
        ),
        color=EMBED_COLOR,
    )
    ticket_embed.set_author(name=BRAND_NAME)
    await channel.send(content=member.mention, embed=ticket_embed, view=TicketControlView())


# --------------------------------------------------------------------------
# Reason modal
# --------------------------------------------------------------------------

class TicketReasonModal(discord.ui.Modal):
    def __init__(self, category_key: str):
        super().__init__(title=f"Ticket — {CATEGORIES[category_key]['label']}")
        self.category_key = category_key
        self.reason = discord.ui.TextInput(
            label="Describe your request",
            style=discord.TextStyle.paragraph,
            placeholder="Clearly explain the reason for this ticket...",
            min_length=10,
            max_length=1000,
            required=True,
        )
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await create_ticket_channel(interaction, self.category_key, self.reason.value)


# --------------------------------------------------------------------------
# Category dropdown
# --------------------------------------------------------------------------

class TicketCategorySelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label=info["label"],
                value=key,
                emoji=info["emoji"],
                description=info["description"],
            )
            for key, info in CATEGORIES.items()
        ]
        super().__init__(
            placeholder="Open a new ticket",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="ticket_panel:select",
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        category_key = self.values[0]
        existing = find_existing_ticket(interaction.guild, interaction.user, category_key)
        if existing:
            await interaction.response.send_message(
                f"You already have an open ticket in **{CATEGORIES[category_key]['label']}**: "
                f"{existing.mention}",
                ephemeral=True,
            )
            return
        await interaction.response.send_modal(TicketReasonModal(category_key))


class TicketPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketCategorySelect())


# --------------------------------------------------------------------------
# Close confirmation
# --------------------------------------------------------------------------

class ConfirmCloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.edit_message(content="Closing ticket...", view=None)
        await interaction.channel.send("🔒 This ticket will be deleted in a few seconds.")
        await asyncio.sleep(3)
        await interaction.channel.delete(reason=f"Ticket closed by {interaction.user}")

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.edit_message(content="Closure cancelled.", view=None)


# --------------------------------------------------------------------------
# Ticket control view
# --------------------------------------------------------------------------

class TicketControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Close Ticket",
        style=discord.ButtonStyle.danger,
        emoji="🔒",
        custom_id="ticket_control:close",
    )
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_message(
            "Are you sure you want to close this ticket?",
            view=ConfirmCloseView(),
            ephemeral=True,
        )


# --------------------------------------------------------------------------
# Events & commands
# --------------------------------------------------------------------------

_ready_once = False


@bot.event
async def on_ready():
    global _ready_once
    if not _ready_once:
        bot.add_view(TicketPanelView())
        bot.add_view(TicketControlView())
        try:
            if GUILD_ID:
                guild_obj = discord.Object(id=GUILD_ID)
                bot.tree.copy_global_to(guild=guild_obj)
                synced = await bot.tree.sync(guild=guild_obj)
            else:
                synced = await bot.tree.sync()
            print(f"{len(synced)} command(s) synced.")
        except Exception as e:
            print(f"Sync error: {e}")
        _ready_once = True
    print(f"Logged in as {bot.user} ({bot.user.id})")


@bot.tree.command(name="panel", description="Send the ticket panel.")
@app_commands.checks.has_permissions(administrator=True)
async def panel(interaction: discord.Interaction) -> None:
    channel = bot.get_channel(PANEL_CHANNEL_ID)
    if channel is None:
        await interaction.response.send_message("Panel channel not found.", ephemeral=True)
        return
    await channel.send(embed=build_panel_embed(), view=TicketPanelView())
    await interaction.response.send_message(f"Panel sent in {channel.mention}.", ephemeral=True)


@bot.tree.error
async def on_app_command_error(
    interaction: discord.Interaction, error: app_commands.AppCommandError
) -> None:
    if isinstance(error, app_commands.MissingPermissions):
        message = "You must be an administrator to use this command."
    else:
        print(f"Command error: {error}")
        message = "An error occurred."
    if interaction.response.is_done():
        await interaction.followup.send(message, ephemeral=True)
    else:
        await interaction.response.send_message(message, ephemeral=True)


if __name__ == "__main__":
    if not TOKEN:
        raise SystemExit("DISCORD_TOKEN missing: add it to your .env file")
    bot.run(TOKEN)
