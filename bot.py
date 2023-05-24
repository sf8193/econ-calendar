from datetime import datetime, timedelta, time
from dotenv import load_dotenv
from discord.ext import commands, tasks
import discord
import investpy
import os
import base64
import PIL
from PIL import Image
import io
import matplotlib.pyplot as plt
import numpy as np


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
        #await message.channel.send(res)
        await message.channel.send(file=discord.File('res.png'))

async def get_calendar_data():
    df = investpy.news.economic_calendar(time_zone="GMT -4:00", time_filter='time_only', countries=['United States'], importances=None, categories=None)

    df = df.drop(['id','zone','date', 'currency'], axis=1)
    new_cols = ["time","importance","forecast","previous","actual","event"]
    df = df.reindex(columns=new_cols)
    csv = df.to_csv(index=False, na_rep='None')
    res = csv.replace(',', ' | ')
    res = res.replace('importance', 'vol')
    # Remove leading/trailing spaces in headers and data
# Split the data into rows
    rows = res.strip().split("\n")

    # Split each row into columns
    columns = [row.split("|") for row in rows]

    headers = columns[0]
    data = columns[1:]  # Adjusted to start from the second row

    # Remove leading/trailing spaces in headers and data
    headers = [header.strip() for header in headers]
    data = [[item.strip() for item in row] for row in data]

    # Ensure all rows have the same number of columns
    max_columns = max(len(row) for row in data)
    data = [row + [''] * (max_columns - len(row)) for row in data]

# Convert data into separate lists for each column
    time = [row[0] for row in data]
    vol = [row[1] for row in data]
    forecast = [row[2] for row in data]
    previous = [row[3] for row in data]
    actual = [row[4] for row in data]
    event = [row[5] for row in data]

# Create the plot
    cellText = np.array([time, vol, forecast, previous, actual, event]).T.tolist()
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.axis('off')  # Turn off the axes
   # Create the table
    
    table = ax.table(
       cellText=cellText,
       colLabels=headers,
       cellLoc='center',
       loc='center',
    )
# Adjust the width of the "events" column
    table.auto_set_column_width(col=list(range(len(headers))))
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.5)  # Adjust the scale factor as needed

# Save the image
    plt.savefig('res.png', bbox_inches='tight', dpi=300)
    plt.close()
    return res

client.run(os.getenv("CLIENT_TOKEN"))
