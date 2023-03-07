import aiohttp
import asyncio
import discord
from discord.ext import commands

def pretty(info):
    embed = discord.Embed(title="IP finder")
    if(info['success']):
        embed.color = discord.Color.fuchsia()
        connect = info['connection']
        embed.add_field(name="IP",value=info['ip'])
        embed.add_field(name="Type",value=info['type'])
        embed.add_field(name="Country",value=info['country'])
        embed.add_field(name="Region",value=info['region'])
        embed.add_field(name="City",value=info['city'])
        embed.add_field(name="Latitude",value=info['latitude'])
        embed.add_field(name="Longitude",value=info['longitude'])
        embed.add_field(name="ASN",value=connect['asn'])
        embed.add_field(name="Domain",value=connect['domain'])
        embed.add_field(name="ASN org",value=connect['org'])
    else:
        embed.color = discord.Color.dark_blue()
        embed.add_field(name="IP",value=info['ip'])
        embed.add_field(name="Message",value=info['message'])
    return embed

async def address_get(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            infos = await response.json()
    return infos

class MyHelp(commands.HelpCommand):
    async def send_bot_help(self, mapping):
        embed = discord.Embed(title="Help",color=discord.Color.yellow())
        
        filtered = await self.filter_commands(self.context.bot.commands,sort=False)
        all_commands = []
        
        for command in filtered:
            embed.add_field(name=command.name,value=command.help,inline=False)
        
        await self.context.send(embed=embed)
        
    async def send_error_message(self, error):
        """If there is an error, send a embed containing the error."""
        channel = self.get_destination() # this defaults to the command context channel
        await channel.send(error)