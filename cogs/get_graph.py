import settings
from influxdb_client_3 import InfluxDBClient3, Point, flight_client_options
import certifi
import pandas as pd
import matplotlib.pyplot as plt
import datetime as dt
from datetime import datetime
from PIL import Image
import matplotlib.dates as mdates
import numpy as np
import matplotlib.ticker as ticker



def query(querytype: str, guildname, guildid, time :str, channelid = None):

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
        time >= now() - interval '{time}'
        """
    elif querytype == "time":
        query = f"""
        SELECT *
        FROM '{guildname} - {guildid}'
        WHERE
        "channelID" = {channelid}
        AND
        time >= now() - interval '{time}'
        """
    else:
        raise ValueError("Invalid querytype")
    
    print(query)
    ans = db.query(query=query, language='sql') 
    df = ans.to_pandas()
    df = df.sort_values(by="time")
    return df

def get_all_channel_stats(guildname, guildid, time):
    df = query(querytype="notime",guildname=guildname, guildid=guildid, time=time)
    channel_df = df.drop(columns=["author"])
    channel_data = {}
    for channel in channel_df["channelID"]:
        if channel not in channel_data:
            channel_data[channel] = 1
        else:
            channel_data[channel] += 1 
    return channel_data
    

def get_channel_stats(channelid, guildname, guildid, time, df=None):
    if df == None:
        df = query(querytype="time", channelid=channelid, guildname=guildname, guildid=guildid,  time=time)
    channel_df = df.drop(columns=["author"])
    channel_df.loc[:, ('time')] = channel_df['time'].dt.round('60min')
    channel_data = {}
    for time in channel_df["time"]:
        if time not in channel_data:
            channel_data[time] = 1
        else:
            channel_data[time] += 1
    return channel_data


def get_author_data(guildname, guildid, time, df=None):
    if df == None:
        df = query(querytype="notime", guildname=guildname, guildid=guildid,  time=time)
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

def get_graph_data(guildname, guildid, channelid,time):
    df = query(querytype="notime", guildid=guildid, guildname=guildname,time=time)
    graph_df = df[df['channelID'] == f'{channelid}']
    print(graph_df)
    graph_df.loc[:, ('time')] = graph_df['time'].dt.round('60min')
    print(graph_df)
    channel_data = {}
    author_data = {}
    for value in graph_df['time']:
        channel_data[value] = channel_data.get(value, 0) + 1
        tempdf = graph_df.loc[graph_df['time'] == value]
        author_data[value] = len(tempdf['author'].unique().tolist())
    return channel_data, author_data


def plot_graph(time, guildid, guildname, channelid):
    channel_data, author_data = get_graph_data(guildname=guildname, guildid=guildid, channelid=channelid, time=time.value)
    fig, ax1 = plt.subplots(figsize=(12, 6))
    
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

    ax1.plot(dates, values, linestyle='-', color='#43b581', linewidth=2.5, label='Time Series Data')
    ax1.set_xlabel('Date', color='white')
    ax1.set_ylabel('Time Series Values', color='#43b581')
    ax1.tick_params(axis='y', labelcolor='#43b581')
    ax1.tick_params(axis='x', colors='white')

    # Custom date formatter
    def custom_date_format(x, pos=None):
        current_date = mdates.num2date(x)
        previous_date = mdates.num2date(ax1.get_xticks()[pos-1]) if pos > 0 else None
        if time.value == "7 days":
            return current_date.strftime('%b %d')
        elif time.value == "1 day":
            if previous_date is None or current_date.day != previous_date.day:
                return current_date.strftime('%B-%d')
            else:
                return current_date.strftime('%H:%M')

    ax1.xaxis.set_major_formatter(ticker.FuncFormatter(custom_date_format))
    ax1.xaxis.set_minor_locator(mdates.HourLocator(interval=3)) # Customize interval as needed

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
    ax2.bar(author_dates, author_values, color='#7289da', alpha=0.6, width=0.03, label='Bar Data')
    ax2.set_ylabel('Number of Users', color='#7289da')
    ax2.tick_params(axis='y', labelcolor='#7289da')
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
