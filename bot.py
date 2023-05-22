from datetime import datetime, timedelta, time
from dotenv import load_dotenv
from discord.ext import commands, tasks
import discord
import investpy
import os

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

looping_time = time(hour=9)

# @tasks.loop(seconds=5.0)
@tasks.loop(time=looping_time)
async def send_cal():
    message_channel = client.get_channel(int(os.getenv('TARGET_CHANNEL')))
    print(f"Got channel {message_channel}")
    res = await get_calendar_data()
    if (len(res)) >= 2000:
        await message_channel.send('result over 2000 chars')
    await message_channel.send(res)

@send_cal.before_loop
async def before():
    await client.wait_until_ready()

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    send_cal.start()

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$today'):
        res = await get_calendar_data()
        if (len(res)) >= 2000:
            await message.channel.send('result over 2000 chars')
        await message.channel.send(res)

async def get_calendar_data(): 
    df = investpy.news.economic_calendar(time_zone=None, time_filter='time_only', countries=['United States'], importances=None, categories=None, from_date=datetime.today().strftime('%d/%m/%Y'), to_date=(datetime.today() + timedelta(1)).strftime('%d/%m/%Y'))

    df = df.drop(['id','zone','date', 'importance', 'currency', 'actual', 'forecast', 'previous'], axis=1)
    csv = df.to_csv(header=False, index=False)
    res = csv.replace(',', ' | ')
    return res

client.run(os.getenv("CLIENT_TOKEN"))



