import discord
from influxdb_client_3 import InfluxDBClient3, Point, flight_client_options
import settings
import certifi
from datetime import datetime, date
from discord import app_commands
from discord.ext import commands
from discord.app_commands import Choice
import asyncio
import pandas as pd
import matplotlib.pyplot as plt
import datetime as dt
from PIL import Image
from collections import Counter
import matplotlib.dates as mdates
import numpy as np
import matplotlib.ticker as ticker
from cogs.get_graph import get_channel_stats, get_author_data, get_all_channel_stats, plot_graph
import itertools

 

fh = open(certifi.where(), "r")
cert = fh.read()
fh.close()

def is_owner():
    def predicate(interaction: discord.Interaction):
        if interaction.user.id == 461496649324167168:
            return True
        else:
            return False
    return app_commands.check(predicate)
db = InfluxDBClient3(
    token=settings.DB_TOKEN,
    host="https://us-east-1-1.aws.cloud2.influxdata.com",
    database="Discord Bot Data",
    flight_client_options=flight_client_options(
        tls_root_certs=cert))


    
database = "Discord Bot Data"

class MessageStats(commands.GroupCog, name="message_stats"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

                
    @app_commands.command()
    @is_owner()
    async def test2(self, interaction: discord.Interaction):
        await interaction.response.send_message("Hi!")

    def get_user_data(userid,guildname,guildid):
        query = f"""SELECT COUNT(CASE WHEN author == {userid} THEN author END) FROM '{guildname} - {guildid}'"""
        table = db.query(query=query, database="Discord Bot Data", language='sql') 
        return table
    
    @app_commands.command(
        name="user",
        description="Get stats of User")
    @is_owner()
    async def user_stats(self, interaction: discord.Interaction, user: discord.Member = None):
        if user == None:
            user = interaction.user
        try:
            await interaction.response.defer()
            data = MessageStats.get_user_data(user.id, interaction.guild.name, interaction.guild.id)
            embed = discord.Embed(title=f"{user}'s Messages in {interaction.guild.name}", description=f"## {data[0][0]} ##")
            await asyncio.sleep(delay=0)
            await interaction.followup.send(embed=embed)
        except Exception as e:
            print(e)
    
    @app_commands.command(
        name="channel",
        description="Get stats of Channels"
    )
    @is_owner()
    async def channel_stats(self, interaction: discord.Interaction):
        await interaction.response.defer()
        print(f"{interaction.guild.name} - {interaction.guild.id}")
        channel_data = get_all_channel_stats(guildname=interaction.guild.name, guildid=interaction.guild.id)
        channel_data = dict(sorted(channel_data.items(), key=lambda item: item[1], reverse=True))
        channel_data = dict(itertools.islice(channel_data.items(), 10)) 
        print(channel_data)
        text = ''
        for data in channel_data:
            text += f"<#{data}>: {channel_data[data]}\n"
        await interaction.followup.send(text)
        

    @app_commands.command(
        name="get_graph",
        description="Get a graph of messages in channels"
    )
    @is_owner()
    async def get_graph(self, interaction: discord.Interaction, channel: discord.TextChannel):
        channel = interaction.channel
        await interaction.response.defer()
        plot_graph(author_data=get_author_data(guildname=interaction.guild.name, guildid = interaction.guild.id), channel_data=get_channel_stats(guildname=interaction.guild.name, guildid= interaction.guild.id, channelid=channel.id))
        filename =  "test.png"
        plt.savefig(filename)
        image = discord.File(filename)
        await interaction.followup.send(file = image)



async def setup(bot):
    await bot.add_cog(MessageStats(bot))