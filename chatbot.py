import discord
import os
import re
from dotenv import load_dotenv,find_dotenv
from discord.ext import commands
from functions import pretty_IP,address_get,MyHelp,inverted_index,search_words,web_scrapping,pretty_search,pretty_not_founded
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import shutil
import pickle

load_dotenv(find_dotenv())

TOKEN = os.getenv('TOKEN')
PATH = "db/cache"
PATH_PICKLE = "db/pickle"
FILE_PICKLE = PATH_PICKLE + "/parrot.pkl"
CLASSIFIER_PICKLE = PATH_PICKLE + "/classifier.pkl"

git_url = "https://github.com/pedroaltobelli23/NLP_chatbot"

cache_names = dict()

regexipv6 = "([0-9a-fA-F]{1,4}:){7,7}([0-9a-fA-F]{1,4})|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)"
regexipv4 = "((([0-9])|([1-9][0-9])|(1[0-9][0-9])|(2[0-5][0-5]))\.){3}((([0-9])|([1-9][0-9])|(1[0-9][0-9])|(2[0-5][0-5])))"

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

# client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix='!',intents=intents,help_command=commands.MinimalHelpCommand(no_category = "All commands"))
bot.help_command = MyHelp()

@bot.event
async def on_ready():
    # Se existir uma pasta chamada cache, ele apaga e cria outra.Tambem reseta a lista que esta guardada na memoria com o pickle
    if not os.path.exists(PATH):
        os.mkdir(PATH)
        os.mkdir(PATH_PICKLE)
        # pickle.dump([], open(FILE_PICKLE, 'wb'))

    guild = discord.utils.get(bot.guilds, name='A Cidade dos Robôs')
    channel = discord.utils.get(guild.text_channels, name='bot-fest')
    await channel.send('Hello world!\nType !help for more information.')

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
            await ctx.send(embed=pretty_IP(infos))
        else:
            await ctx.send("Invalid IPv4")
    elif(re.fullmatch("v6",version)):
        #versao v6
        if(re.fullmatch(regexipv6,ip)):
            infos = await address_get('http://ipwho.is/'+ip)
            await ctx.send(embed=pretty_IP(infos))
        else:
            await ctx.send("Invalid IPv6.")
    else:
        await ctx.send("Invalid version.See !help for more information.")

@bot.command(help="web crawling from webpage")
async def crawl(ctx,url):
    #Pega url e faz o webscrapping dela. As paginas serao salvas na pasta cache e a lista com os nomes das urls no doc_names

    nome_urls,jumped = web_scrapping(url=url,dump_path=PATH,max_l=10)

    try:
        if not os.path.isfile(FILE_PICKLE):
            with open(FILE_PICKLE,"wb") as f:
                cache_names = nome_urls
                pickle.dump(nome_urls,f)
        else:
            with open(FILE_PICKLE,'rb') as f:
                cache_names = pickle.load(f)
            cache_names.update(nome_urls)
            with open(FILE_PICKLE,"wb") as f:
                pickle.dump(cache_names,f)
        
        total_data = []        
        doc_names = []
        
        for filename,url_n in cache_names.items():
            f = os.path.join(PATH, filename)
            data = joblib.load(f,'r')
            total_data.append(data)
            doc_names.append(url_n)


        with open(CLASSIFIER_PICKLE,"wb") as f:
            classificador = inverted_index(total_data,doc_names)
            pickle.dump(classificador,f)
            
    except Exception as e:
        print(e)        
    await ctx.send(f'successful web crawling from {url}')
    
@bot.command(help="reset do web scrapping")
async def reset(ctx):
    shutil.rmtree(PATH)
    shutil.rmtree(PATH_PICKLE)
    
    os.mkdir(PATH)
    os.mkdir(PATH_PICKLE)
    
    await ctx.send("web scrapping de paginas antigas foram resetadas!")


@bot.command(help="Seach for a word in the documents")
async def search(ctx,*args):
    words = list(args)
    try:    
        if os.path.isfile(CLASSIFIER_PICKLE):#classificador nao esta vazio
            with open(CLASSIFIER_PICKLE,'rb') as f:
                classificador = pickle.load(f)

            res,not_founded_words,founded_words = search_words(words,classificador)
            
            if bool(res):#pelo menos uma palavra foi encontrada no classificador
                await ctx.send(embed=pretty_search(res,founded_words))
                
            if bool(not_founded_words):#existem palavras que nao estao no classificador
                await ctx.send(embed=pretty_not_founded(not_founded_words))
        else:#nao existe classificador
            await ctx.send(f"eh necessario usar o comando !crawl antes de buscar por palavras no classificador")
    except Exception as e:
        print(e)
                
@run.error
async def run_error(ctx,error):
    if isinstance(error,commands.MissingRequiredArgument):
        await ctx.send("Missing required argument. See !help for more information.")
        
@crawl.error
async def crawl_error(ctx,error):
    if isinstance(error,commands.MissingRequiredArgument):
        await ctx.send("Missing required argument. See !help for more information.")

@search.error
async def search_error(ctx,error):
    if isinstance(error,commands.MissingRequiredArgument):
        await ctx.send("Missing required argument. See !help for more information.")

bot.run(TOKEN)