import discord
import os
import re
from dotenv import load_dotenv,find_dotenv
from discord.ext import commands
from functions import pretty,address_get,MyHelp
load_dotenv(find_dotenv())

TOKEN = os.getenv('TOKEN')

git_url = "https://github.com/pedroaltobelli23/NLP_chatbot"

regexipv6 = "([0-9a-fA-F]{1,4}:){7,7}([0-9a-fA-F]{1,4})|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)"
regexipv4 = "((([0-9])|([1-9][0-9])|(1[0-9][0-9])|(2[0-4][0-9])|(25[0-5]))\.){3}((([0-9])|([1-9][0-9])|(1[0-9][0-9])|(2[0-4][0-9])|(25[0-5])))"

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

# client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix='!',intents=intents,help_command=commands.MinimalHelpCommand(no_category = "All commands"))
bot.help_command = MyHelp()

@bot.event
async def on_ready():
    guild = discord.utils.get(bot.guilds, name='A Cidade dos Robôs')
    channel = discord.utils.get(guild.text_channels, name='bot-fest')
    await channel.send('Hello world!\ntype !help for more information.')

@bot.command(help="returns the source code from this bot")
async def source(ctx):
    embed = discord.Embed(title="Source",color=discord.Color.blue())
    embed.description = git_url
    await ctx.send(embed=embed)

@bot.command(help="returns the author's name")
async def author(ctx):
    embed = discord.Embed(title="Author",color=discord.Color.red())
    embed.description = 'Author: Pedro Altobelli \n e-mail: pedroatp@al.insper.edu.br'
    await ctx.send(embed=embed)

@bot.command(help="get informations from IP address.\nIPv4 format: x.x.x.x\nIPv6 format y:y:y:y:y:y:y:y (also works with abreviation.e.g->2001:db8::)\n!run [IPv4]\n!run [IPv6] v6\nAPI used: https://rapidapi.com/xakageminato/api/ip-geolocation-ipwhois-io")
async def run(ctx, ip,version="v4"):
    #!run x.x.x.x v4
    #!run y:y:y:y:y:y:y:y v6
    #!run x.x.x.x [default v4]
        
    if(re.fullmatch("v4",version)):
        #versao v4
        if(re.fullmatch(regexipv4,ip)):
            infos = await address_get('http://ipwho.is/'+ip)
            await ctx.send(embed=pretty(infos))
        else:
            await ctx.send("Invalid IPv4")
    elif(re.fullmatch("v6",version)):
        #versao v6
        if(re.fullmatch(regexipv6,ip)):
            infos = await address_get('http://ipwho.is/'+ip)
            await ctx.send(embed=pretty(infos))
        else:
            await ctx.send("Invalid IPv6.")
    else:
        await ctx.send("Invalid version.See !help for more information.")
    
@run.error
async def run_error(ctx,error):
    if isinstance(error,commands.MissingRequiredArgument):
        await ctx.send("Missing required argument. See !help for more information.")

bot.run(TOKEN)