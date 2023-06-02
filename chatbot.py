import discord
import os
import re
from dotenv import load_dotenv,find_dotenv
from discord.ext import commands
from utils.functions import address_get,MyHelp,inverted_index,search_words,web_scrapping,wn_search_words,URL_validate,filter_by_th,get_texts_with_word,get_urls,generategpt
from utils.prettify import pretty_IP,pretty_search,pretty_not_founded,pretty_wn,pretty_crawl,pretty_urls
import numpy as np
import tensorflow as tf
from generate import ModelGenerate
import sys
import openai

load_dotenv(find_dotenv())

TOKEN = os.getenv('TOKEN_TESTE')
KEY_RESET = os.getenv('KEY_RESET')
FILE_CLASS_PICKLE = os.getenv('FILE_CLASS_PICKLE')
CHANNEL = os.getenv('CHANNEL')
GUILD = os.getenv('GUILD')
openai.api_key = os.getenv('API_KEY') 

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
incredible_model = ModelGenerate()

@bot.event
async def on_ready():
    guild = discord.utils.get(bot.guilds, name=GUILD)
    channel = discord.utils.get(guild.text_channels, name=CHANNEL)
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

@bot.command(help="web crawling from webpage. Only receive 1 url and craw over a max of 15 pages. There is a timout with request takes more than 15 seconds.",usage="!crawl <url>")
async def crawl(ctx,url):
    # pages text will be saved in the folder cache
    if URL_validate(url):
        nome_urls,jumped = web_scrapping(url=url,max_l=15)
        print("=========================================foi====================================")
        await ctx.send(embed=pretty_crawl(nome_urls))
    else:
        await ctx.send(f"Invalid URL '{url}': No scheme supplied. Perhaps you meant https://{url}?")

        
@bot.command(help="Web scrapping reset",usage="!reset <secret_key>")
async def reset(ctx,arg):
    if arg == KEY_RESET:
        if os.path.exists(FILE_CLASS_PICKLE):
            os.remove(FILE_CLASS_PICKLE)
        await ctx.send("Database is now empty!")
    else:
        await ctx.send("Reset Key Incorrect")


@bot.command(help="Seach for a word or a phrase in the documents.You can use the argument th=X in the end for filtering pages by positivity.th default is -1 which means that filter wasn't applied.Goes from -1 to 1",usage="!search <word> [th=<value>]")
async def search(ctx,*args): 
    params = list(args)
    threshold = -1
    i = 0
    while i < len(params):
        if params[i].startswith("th="):
            threshold = float(params[i].replace("th=",""))
            if threshold > 1:
                threshold = 1
            elif threshold < -1:
                threshold = -1
            break
        i+=1
            
    words = params[0:i]
    try:    
        if os.path.isfile(FILE_CLASS_PICKLE):
            classificador = inverted_index()
            # print(classificador)
            # print(words)
            res,not_founded_words,founded_words = search_words(words,classificador)
            if bool(res):# At least one word was founded in the classifier
                filtered = filter_by_th(res,threshold)
                sorted_res = dict(sorted(filtered.items(), key=lambda x:x[1],reverse=True))
                await ctx.send(embed=pretty_search(sorted_res,founded_words,threshold))
                    
            if bool(not_founded_words):# There are words that aren't in the classifier
                await ctx.send(embed=pretty_not_founded(not_founded_words))
        else:
            await ctx.send("Utilize o comando !crawl primeiro")
    except Exception as e:
        print(e)
        
@bot.command(help="Search for one word in the documents. If word not in documents, try to find its most similar synonim.You can use the argument th=X in the end for filtering pages by positivity.th default is -1 which means that filter wasn't applied.Goes from -1 to 1",usage="!search <word> [th=<value>]")
async def wn_search(ctx,*args):
    params = list(args)
    threshold = -1
    i = 0
    while i < len(params):
        if params[i].startswith("th="):
            threshold = float(params[i].replace("th=",""))
            if threshold>1:
                threshold=1
            elif threshold<-1:
                threshold=-1
            break
        i+=1
            
    word = params[0]
    
    try:    
        if os.path.isfile(FILE_CLASS_PICKLE):
            classificador = inverted_index()
            res = wn_search_words(word,classificador)
            if bool(res):
                for w,urlTfidf in res.items():
                    filtered = filter_by_th(urlTfidf,threshold)
                    sorted_urlTfidf = dict(sorted(filtered.items(), key=lambda x:x[1],reverse=True))
                    await ctx.send(embed=pretty_wn(w,sorted_urlTfidf,threshold))
            else:#Palavra nao tem um synset
                await ctx.send("Word don't have a synset from wordnet")
        else:#nao existe classificador
            await ctx.send(f"It is necessary to use the command !crawl before searching for a word in the database")
    except Exception as e:
        print(e)
        
@bot.command(help="Get the url from all pages that have been webscrapped.You can use the argument th=X in the end for filtering pages by positivity.th default is -1 which means that filter wasn't applied.Goes from -1 to 1",usage="!get_all_pages <value>")
async def get_all_pages(ctx,arg):
    th = max(-1,min(1,float(arg)))
    urls = get_urls(th)
    await ctx.send(embed=pretty_urls(urls=urls))
            
@bot.command(help="Generate text from database",usage="!generate word")
async def generate(ctx,*args):
    word = args[0]
    # print(word)
    try:
        if os.path.isfile(FILE_CLASS_PICKLE):
            res = get_texts_with_word(word)
            # print(res)
            if bool(res):# At least one word was founded in the classifier
                # print(res)
                # print(word)
                phrase = incredible_model.prediction(res,word)
                await ctx.send(phrase)
            else:
                await ctx.send(embed=pretty_not_founded([word]))
        else:
            await ctx.send("Utilize o comando !crawl primeiro")
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        
@bot.command(help="Generate text from database using GPT API",usage="!")
async def gptgenerate(ctx,arg):
    word = str(arg)
    try:
        if os.path.isfile(FILE_CLASS_PICKLE):
            texts = get_texts_with_word(word)
            # print(res)
            if bool(texts):# At least one word was founded in the classifier
                # print(res)
                # print(word)
                phrase = generategpt(texts)
                await ctx.send(phrase)
            else:
                await ctx.send(embed=pretty_not_founded([word]))
        else:
            await ctx.send("Utilize o comando !crawl primeiro")
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
    
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
        
@wn_search.error
async def wn_search_error(ctx,error):
    if isinstance(error,commands.MissingRequiredArgument):
        await ctx.send("Missing required argument. See !help for more information.")
        
@generate.error
async def generate_error(ctx,error):
    if isinstance(error,commands.MissingRequiredArgument):
        await ctx.send("Missing required argument. See !help for more information.")
        
@get_all_pages.error
async def get_all_pages_error(ctx,error):
    if isinstance(error,commands.MissingRequiredArgument):
        await ctx.send("Missing required argument. See !help for more information.")
        
@reset.error
async def reset_error(ctx,error):
    if isinstance(error,commands.MissingRequiredArgument):
        await ctx.send("Missing required argument. See !help for more information.")

bot.run(TOKEN)