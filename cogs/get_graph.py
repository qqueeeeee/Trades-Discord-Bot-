from influxdb_client_3 import InfluxDBClient3, Point, flight_client_options
import certifi
import pandas as pd
import matplotlib.pyplot as plt
import datetime as dt
from datetime import datetime
from PIL import Image
from collections import Counter
import matplotlib.dates as mdates
import numpy as np
import matplotlib.ticker as ticker
import settings

def query(querytype: str, guildname, guildid,  channelid = None ):


    if(querytype == "time" and channelid == None):
        raise ValueError("Channel ID is required when using time querytype")
    
    fh = open(certifi.where(), "r")
    cert = fh.read()
    fh.close()

    db = InfluxDBClient3(
        token=settings.DB_TOKEN,
        host="https://us-east-1-1.aws.cloud2.influxdata.com",
        database="Discord Bot Data",
        flight_client_options=flight_client_options(
            tls_root_certs=cert))

    if querytype == "notime":
        query = f"""
        SELECT *
        FROM '{guildname} - {guildid}'
        WHERE
        time >= now() - interval '1 day'
        """
    elif querytype == "time":
        query = f"""
        SELECT *
        FROM '{guildname} - {guildid}'
        WHERE
        "channelID" = {channelid}
        AND
        time >= now() - interval '1 day'
        """
    else:
        raise ValueError("Invalid querytype")
    
    
    ans = db.query(query=query, language='sql') 
    df = ans.to_pandas()
    df = df.sort_values(by="time")
    return df

def get_all_channel_stats(guildname, guildid):
    df = query(querytype="notime",guildname=guildname, guildid=guildid)
    channel_df = df.drop(columns=["author"])
    channel_data = {}
    for channel in channel_df["channelID"]:
        if channel not in channel_data:
            channel_data[channel] = 1
        else:
            channel_data[channel] += 1 
    return channel_data
    

def get_channel_stats(channelid, guildname, guildid):
    df = query(querytype="time", channelid=channelid, guildname=guildname, guildid=guildid)
    channel_df = df.drop(columns=["author"])
    channel_df['time'] = channel_df['time'].round("h")
    channel_data = {}
    for time in channel_df["time"]:
        if time not in channel_data:
            channel_data[time] = 1
        else:
            channel_data[time] += 1
    return channel_data


def get_author_data(guildname, guildid):
    df = query(querytype="notime", guildname=guildname, guildid=guildid)
    author_df = df.drop(columns=["channelID"])
    author_data = {}
    for time in author_df["time"]:
        authorid = author_df.loc[df['time'] == time, 'author'].values[0]
        time = time.round("h")
        if time not in author_data:
            author_data[time] = [authorid]
        else:
            author_data[time].append(authorid) 
    bar_data = {}
    for time in author_data:
        uniqueids = len(np.unique(author_data[time]))
        bar_data[time] = uniqueids
    return bar_data

def plot_graph(author_data, channel_data):
    print(author_data)
    print("DONE AUTHOR")
    print(channel_data)

    fig, ax1 = plt.subplots(figsize=(12, 6))
    
    # Set the face color for the figure and axes
    fig.patch.set_facecolor('#2c2f33')
    ax1.set_facecolor('#2c2f33')

    ### TIME SERIES
    dates = list(channel_data.keys())
    if isinstance(dates[0], str):
        dates = [datetime.strptime(date, "%Y-%m-%d %H:%M") for date in dates]
    values = list(channel_data.values())

    # Insert NaN at the start and end to break the line
    values = [np.nan] + values + [np.nan]
    dates = [dates[0]] + dates + [dates[-1]]

    ax1.plot(dates, values, marker='o', linestyle='-', color='#43b581', linewidth=2.5, label='Messages')
    ax1.set_xlabel('Time', color='white')
    ax1.set_ylabel('Number of Messages', color='white')
    ax1.tick_params(axis='y', labelcolor='white')
    ax1.tick_params(axis='x', colors='white')
    
    ax1.xaxis.set_major_locator(mdates.HourLocator(interval=3)) # Customize interval as needed
    
    # Custom date formatter
    def custom_date_format(x, pos):
        current_date = mdates.num2date(x)
        previous_date = mdates.num2date(ax1.get_xticks()[pos-1]) if pos > 0 else None
        if previous_date is None or current_date.day != previous_date.day:
            return current_date.strftime('%B-%d')
        else:
            return current_date.strftime('%H:%M')

    ax1.xaxis.set_major_formatter(ticker.FuncFormatter(custom_date_format))

    ax1.spines['top'].set_color('#2c2f33')
    ax1.spines['bottom'].set_color('white')
    ax1.spines['left'].set_color('#43b581')
    ax1.spines['right'].set_color('white')

    ### BAR GRAPH
    author_dates = list(author_data.keys())
    if isinstance(author_dates[0], str):
        author_dates = [datetime.strptime(date, "%Y-%m-%d %H:%M") for date in author_dates]
    author_values = list(author_data.values())
    
    ax2 = ax1.twinx()
    ax2.bar(author_dates, author_values, color='#7289da', alpha=0.6, width=0.03, label='Users')
    ax2.set_ylabel('Number of Users', color='white')
    ax2.tick_params(axis='y', labelcolor='white')
    ax2.spines['top'].set_color('#2c2f33')
    ax2.spines['bottom'].set_color('white')
    ax2.spines['left'].set_color('#2c2f33')
    ax2.spines['right'].set_color('#7289da')

    ### TITLE AND LEGEND
    fig.suptitle('Combined Time Series and Bar Graph', color='white')
    fig.tight_layout()
    fig.legend(loc='upper left', bbox_to_anchor=(0.1, 0.9), facecolor='#2c2f33', edgecolor='white', framealpha=1, fontsize='medium', labelcolor='white')

    # Rotate x-axis labels
    fig.autofmt_xdate(rotation=45)
