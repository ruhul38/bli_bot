import discord
from discord.ext import commands
from discord import app_commands
import re
import tzlocal
from datetime import datetime, timezone
from secret import d_api_key
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Set up intents to allow tracking of messages
intents = discord.Intents.default()
intents.message_content = True  # Enable the MESSAGE CONTENT INTENT
intents.messages = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)
local_timezone = tzlocal.get_localzone()

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name('composed-garden-428307-h9-de6905d7d7b0.json', scope)
client = gspread.authorize(creds)
print("authorized")
sheet = client.open("bli_employee_log").sheet1 
print(sheet.url)# Open the first sheet
print(client.open("record001").title)# Open the first sheet

# Predefined keywords for autocomplete
keywords = ["singing", "break", "back", "dancing", "coding"]

def utc_to_local(utc_dt):
    return utc_dt.replace(tzinfo=timezone.utc).astimezone(local_timezone)

class MyBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Register the command within the bot's command tree
        bot.tree.add_command(app_commands.Command(
            name="status",
            description="Set your status",
            callback=self.status
        ))

    async def status(self, interaction: discord.Interaction, status: str):
        print(f"Status command invoked with status: {status}")
        await interaction.response.send_message(f'Status set to: {status}', ephemeral=True)

    @app_commands.autocomplete()
    async def autocomplete_status(self, interaction: discord.Interaction, current: str):
        print(f"Autocomplete invoked with current: {current}")
        return [
            app_commands.Choice(name=keyword, value=keyword)
            for keyword in keywords if current.lower() in keyword.lower()
        ]

    @commands.command(name="attendance")
    async def take_attendance(self, ctx):
        guild = ctx.guild
        present_members = [member for member in guild.members if member.status != discord.Status.offline]

        attendance_list = []
        for member in present_members:
            joined_at = member.joined_at
            if joined_at:
                local_joined_at = joined_at.replace(tzinfo=pytz.utc).astimezone(local_timezone)
                formatted_time = local_joined_at.strftime('%Y-%m-%d %H:%M:%S %Z')
            else:
                formatted_time = "Unknown"
            attendance_list.append([member.display_name, formatted_time])

        # Log attendance to Google Sheets
        # sheet.append_row(["Name", "Joined At", ])
        # for entry in attendance_list:
        #     sheet.append_row(entry)

        await ctx.send(f"Attendance has been logged to the Google Sheet.")
@bot.event
async def on_ready():
    print(f'Bot is ready. Logged in as {bot.user}')
    try:
        await bot.tree.sync()  # Sync the commands with Discord
        print("Commands synced successfully")
    except Exception as e:
        print(f"Failed to sync commands: {e}")





@bot.event
async def on_message(message):
    # Prevent the bot from responding to its own messages
    if message.author == bot.user:
        return
    created_at = utc_to_local(datetime.strptime(message.created_at.strftime("%Y-%m-%d %H:%M:%S%z"),"%Y-%m-%d %H:%M:%S%z")).strftime("%d/%m/%Y %I:%M%p")

    # Regular expression to match the various status formats
    match = re.match(r'(signedIn|signedOut|breakStarted|breakEnded)@(\d{2}:\d{2}[ap]m)', message.content)
    attendance_list=[]
    if match:
        status = match.group(1)
        
        time_str = match.group(2)
        
        # Convert the time string to a datetime object
        time_obj = datetime.strptime(time_str, '%I:%M%p').time()
        created_at = utc_to_local(datetime.strptime(message.created_at.strftime("%Y-%m-%d %H:%M:%S%z"),"%Y-%m-%d %H:%M:%S%z")).strftime("%d/%m/%Y %I:%M%p")


        print(f'Message from {message.author} at {created_at}: {status} at {time_obj}')

        # Optionally send a response to a logging channel
        logging_channel_id = 1257575721593864285  # replace with your channel ID
        logging_channel = bot.get_channel(logging_channel_id)
        if logging_channel:
            await logging_channel.send(f'Message from {message.author} at {created_at}: {status} at {time_obj}')
            attendance_list.append([message.author.global_name,message.author.name, utc_to_local(message.created_at).strftime("%d %b %y"),utc_to_local(message.created_at).strftime("%I:%M%p"), status, time_obj.strftime("%I:%M%p")])
            print(attendance_list)
                # Log attendance to Google Sheets
                # sheet.append_row(["Id", "Joined At"])
            for entry in attendance_list:
                sheet.append_row(entry)
                print(sheet.get())

                # print(sheet.get("A1"))

                print(f"Attendance has been logged to the Google Sheet.")
        
        await bot.process_commands(message)
    else:
        match1 = re.match(r'(signingIn|signingOut|break|back)', message.content)
        if match1:
            created_at = utc_to_local(datetime.strptime(message.created_at.strftime("%Y-%m-%d %H:%M:%S%z"),"%Y-%m-%d %H:%M:%S%z")).strftime("%d/%m/%Y %I:%M%p")
            # created_at = message.created_at.utcoffset.strftime("%d/%m/%Y %H:%M:%p")
            time_obj = datetime.now().strftime("%I:%M%p")
            status = match1.group(1)
            logging_channel_id = 1257575721593864285  # replace with your channel ID
            logging_channel = bot.get_channel(logging_channel_id)
            if logging_channel:
                await logging_channel.send(f'Message from {message.author} at {created_at}: {status} at {time_obj}')
                attendance_list.append([message.author.global_name,message.author.name, message.created_at.strftime("%d %b %y"),message.created_at.strftime("%I:%M%p"), message.content, message.created_at.strftime("%I:%M%p")])
                print(attendance_list)
                # Log attendance to Google Sheets
                # sheet.append_row(["Id", "Joined At"])
            for entry in attendance_list:
                sheet.append_row(entry)
                print(sheet.get())

                # print(sheet.get("A1"))

                print(f"Attendance has been logged to the Google Sheet.")
        else:
            logging_channel_id = 1257575721593864285  # replace with your channel ID
            logging_channel = bot.get_channel(logging_channel_id)
            if logging_channel:
                await logging_channel.send(f'Sorry! I haven\'t recognized it')
        


        await bot.process_commands(message)

    
    # Process commands if any



bot.add_cog(MyBot(bot))
# Run the bot
bot.run(d_api_key)