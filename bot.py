from datetime import datetime, timedelta, time
from dotenv import load_dotenv
from discord.ext import commands, tasks
import discord
import investpy
import os
import io
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np


load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

looping_time = time(hour=9)

#@tasks.loop(seconds=5.0)
@tasks.loop(time=looping_time)
async def send_cal():
    message_channel = client.get_channel(int(os.getenv('TARGET_CHANNEL')))
    print(f"Got channel {message_channel}")
    res = await get_calendar_data()
    if (len(res)) >= 2000:
        await message_channel.send('result over 2000 chars')
    await message_channel.send(file=discord.File('res.png'))
    print('sent news')

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
        await message.channel.send(file=discord.File('res.png'))
    elif message.content.startswith('$tomorrow'):
        await message.channel.send('maybe later')

async def get_calendar_data():
    df = investpy.news.economic_calendar(time_zone="GMT -4:00", time_filter='time_only', countries=['United States'], importances=None, categories=None)

    df = df.drop(['id','zone','date', 'currency'], axis=1)
    new_cols = ["time","importance","forecast","previous","actual","event"]
    df = df.reindex(columns=new_cols)
    csv = df.to_csv(index=False, na_rep='')
    res = csv.replace(',', ' | ')
    res = res.replace('medium', 'med')
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
    cellText = np.array([time, vol, event, previous, forecast, actual ]).T.tolist()
    # Get the index of the "vol" column
    vol_index = headers.index("vol")

# Remove the "vol" column from cellText
    cellText = [row[:vol_index] + row[vol_index + 1:] for row in cellText]

# Remove the "vol" header from headers
    headers.pop(vol_index)
    fig, ax = plt.subplots(figsize=(18, 12))
    ax.axis('off')  # Turn off the axes
    
    table = ax.table(
       cellText=cellText,
       colLabels=['Time', 'Event', 'Previous','Forecast', 'Actual'],
       colWidths=[1.5,1.5,3,3,3,8],
       cellLoc='center',
       loc='center',
       bbox=[0, 0, 1, 1]
    )
    # Adjust the width of the "events" column
    table.set_fontsize(20)

    table.auto_set_column_width(col=list(range(len(headers))))
    
# Adjust the width of the "time" column
    color_map = {    
    'high': cm.Reds(0.5),   # Light blue
    'med': cm.Reds(0.25),    # Medium blue
    'low': cm.Reds(0.1),    # Dark blue
    }

    for row in range(len(vol)):
        vol_value = vol[row].lower()
        color = color_map.get(vol_value)
        if color:
            for col in range(len(headers)):
                cell = table[row+1, col]
                cell.set_facecolor(color)

    table.scale(1.5, 1.5)  # Adjust the scale factor as needed
    for col in range(len(headers)):
        header_cell = table[0, col]
        header_cell.set_text_props(weight='bold')
    
# Save the image
    plt.savefig('res.png', bbox_inches='tight', dpi=300)
    plt.close()
    return res

client.run(os.getenv("CLIENT_TOKEN"))
