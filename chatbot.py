import discord
import os
import re
from dotenv import load_dotenv,find_dotenv
from discord.ext import commands
from functions import pretty_IP,address_get,MyHelp,inverted_index,search_words,web_scrapping,pretty_search,pretty_not_founded,wn_search_words,pretty_wn,URL_validate
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import shutil
import pickle

load_dotenv(find_dotenv())

TOKEN = os.getenv('TOKEN')
KEY_RESET = os.getenv('KEY_RESET')
PATH = "cache"
PATH_PICKLE = "pickle"
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
    # If cache folder exists, erase cache and pickle and create another one.
    if not os.path.exists(PATH):
        os.mkdir(PATH)
        os.mkdir(PATH_PICKLE)

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

@bot.command(help="web crawling from webpage. Only receive 1 url and craw over a max of 15 pages. There is a timout with request takes more than 15 seconds.")
async def crawl(ctx,url):
    # pages text will be saved in the folder cache
    if URL_validate(url):
        nome_urls,jumped = await web_scrapping(url=url,dump_path=PATH,ctx=ctx,max_l=15)
        
        try:
            if not os.path.isfile(FILE_PICKLE):
                with open(FILE_PICKLE,"wb") as f:
                    cache_names = nome_urls
                    print(cache_names)
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
                await ctx.send(f'Successful web crawling from {url}')
                
        except Exception as e:
            print(e) 
    else:
        await ctx.send(f"Invalid URL '{url}': No scheme supplied. Perhaps you meant https://{url}?") 
        
@bot.command(help="Web scrapping reset")
async def reset(ctx,arg):
    if arg == KEY_RESET:
        shutil.rmtree(PATH)
        shutil.rmtree(PATH_PICKLE)
        
        os.mkdir(PATH)
        os.mkdir(PATH_PICKLE)
        await ctx.send("Database is now empty!")
    else:
        await ctx.send("Reset Key Incorrect")


@bot.command(help="Seach for a word in the documents")
async def search(ctx,*args):
    words = list(args)
    try:    
        if os.path.isfile(CLASSIFIER_PICKLE):# Classifier not empty
            with open(CLASSIFIER_PICKLE,'rb') as f:
                classificador = pickle.load(f)

            res,not_founded_words,founded_words = search_words(words,classificador)
            
            if bool(res):# At least one word was founded in the classifier
                sorted_res = dict(sorted(res.items(), key=lambda x:x[1]))
                await ctx.send(embed=pretty_search(sorted_res,founded_words))
                
            if bool(not_founded_words):# There are words that are't in the classifier
                await ctx.send(embed=pretty_not_founded(not_founded_words))
        else:# Classfier doesn't exists
            await ctx.send(f"It is necessary to use the command !crawl before searching for a word in the database")
    except Exception as e:
        print(e)
        
@bot.command(help="Seach for a word in the documents. If word not in documents, try to find its most similar synonim")
async def wn_search(ctx,arg):
    word = arg
    try:    
        if os.path.isfile(CLASSIFIER_PICKLE):# Classifier isn't empty
            with open(CLASSIFIER_PICKLE,'rb') as f:
                classificador = pickle.load(f)
            s_urlTfidf = wn_search_words(word,classificador)
            
            if bool(s_urlTfidf):
                for w,urlTfidf in s_urlTfidf.items():
                    sorted_urlTfidf = dict(sorted(urlTfidf.items(), key=lambda x:x[1]))
                    await ctx.send(embed=pretty_wn(w,sorted_urlTfidf))

            else:#Palavra nao tem um synset
                await ctx.send("Word don't have a synset from wordnet")
        else:#nao existe classificador
            await ctx.send(f"It is necessary to use the command !crawl before searching for a word in the database")
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

@reset.error
async def reset_error(ctx,error):
    if isinstance(error,commands.MissingRequiredArgument):
        await ctx.send("Missing required argument. See !help for more information.")

bot.run(TOKEN)