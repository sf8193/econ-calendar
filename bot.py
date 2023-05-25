from datetime import datetime, timedelta, time, timezone
from dotenv import load_dotenv
from discord.ext import commands, tasks
import discord
import investpy
import os
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
import pandas as pd
import re
import csv as csvLib

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

looping_time = time(hour=9)

bot = commands.Bot(command_prefix='$', intents=intents)

@bot.command(name='list')
async def test(ctx):
    print('made it')
    pass

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
        await message.channel.send(file=discord.File('res.png'))
    elif message.content.startswith('$tomorrow'):
        res = await get_calendar_data(False)
        await message.channel.send(file=discord.File('res.png'))
    elif message.content.startswith('$'):
        await message.channel.send(f'hello {message.author.mention}! pls fuck off')


async def get_calendar_data(today=True):
    if today:
        df = investpy.news.economic_calendar(time_zone="GMT -4:00", time_filter='time_only', countries=['United States'], importances=None, categories=None)
    else:
        tom = (datetime.now(timezone(timedelta(hours=-5), 'EST')) + timedelta(1)).strftime('%d/%m/%Y')
        day_after_tom = (datetime.now(timezone(timedelta(hours=-5), 'EST')) + timedelta(2)).strftime('%d/%m/%Y')
        df = investpy.news.economic_calendar(time_zone=None, time_filter='time_only', countries=['United States'], importances=None, categories=None, from_date=tom, to_date=day_after_tom)
        df['date'] = pd.to_datetime(df['date'], dayfirst=True)
        df = df[df['date'] != pd.to_datetime((datetime.now(timezone(timedelta(hours=-5), 'EST')) + timedelta(2)).strftime('%Y-%m-%d'))]

    df = df.drop(['id', 'zone', 'date', 'currency'], axis=1)
    new_cols = ["time", "importance", "forecast", "previous", "actual", "event"]
    df = df.reindex(columns=new_cols)
    csv = df.to_csv(index=False, na_rep='')

    # Split the CSV data by newlines
    csv_lines = csv.strip().split('\n')

    # Create a CSV reader
    reader = csvLib.reader(csv_lines)

    # Get the headers from the first row
    headers = next(reader)

    # Iterate over each row
    rows = []
    for row in reader:
        rows.append(row)

    # Convert data into separate lists for each column
    time = [row[0] for row in rows]
    importance = [row[1] for row in rows]
    forecast = [row[2] for row in rows]
    previous = [row[3] for row in rows]
    actual = [row[4] for row in rows]
    event = [row[5] for row in rows]

    # Create the plot
    cellText = np.array([time, importance, event, previous, forecast, actual]).T.tolist()

    # Get the index of the "importance" column
    importance_index = headers.index("importance")

    # Remove the "importance" column from cellText
    cellText = [row[:importance_index] + row[importance_index + 1:] for row in cellText]

    # Remove the "importance" header from headers
    headers.pop(importance_index)

    fig, ax = plt.subplots(figsize=(18, 12))
    ax.axis('off')  # Turn off the axes

    table = ax.table(
        cellText=cellText,
        colLabels=['Time',f"Event ({datetime.now().strftime('%Y-%m-%d')})", 'Previous', 'Forecast', 'Actual'],
        colWidths=[1.5, 1.5, 3, 3, 3, 8],
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
        'medium': cm.Reds(0.25),    # Medium blue
        'low': cm.Reds(0.1),    # Dark blue
    }

    for row in range(len(importance)):
        importance_value = importance[row].lower()
        color = color_map.get(importance_value)
        if color:
            for col in range(len(headers)):
                cell = table[row + 1, col]
                cell.set_facecolor(color)

    table.scale(1.5, 1.5)  # Adjust the scale factor as needed
    for col in range(len(headers)):
        header_cell = table[0, col]
        header_cell.set_text_props(weight='bold')

    for i in range(len(importance)):
        table[i+1, 1]._loc = 'left'
        table[i+1, 1]._text.set_horizontalalignment('left') 
    # Save the image
    plt.savefig('res.png', bbox_inches='tight', dpi=300)
    plt.close()

    return 'res.png'

client.run(os.getenv("CLIENT_TOKEN"))
