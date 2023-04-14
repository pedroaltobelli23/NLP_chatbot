import aiohttp
import asyncio
import discord
from discord.ext import commands
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import os
import joblib
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
from nltk.corpus import wordnet

def URL_validate(url):
    re_url = "^((http|https)://)[-a-zA-Z0-9@:%._\\+~#?&//=]{2,256}\\.[a-z]{2,6}\\b([-a-zA-Z0-9@:%._\\+~#?&//=]*)$"
    r = re.compile(re_url)

    if (re.search(r, url)):
        return True
    return False

def pretty_search(url_tdidf : dict,words : list):
    title="Documentos contendo: "+" ".join(words)
    embed = discord.Embed(title=title)
    
    for url,tfidf in url_tdidf.items():
        embed.add_field(name=url,value=tfidf,inline=False)
    
    embed.color = discord.Color.dark_blue()
    
    return embed

def pretty_not_founded(not_founded_words : list):
    title="Nao encontradas do banco de dados"
    embed = discord.Embed(title=title)
    
    for word in not_founded_words:
        embed.add_field(name=word,value="",inline=False)
    
    embed.color = discord.Color.red()
    return embed
        
def pretty_wn(name,dicio:dict):
    embed = discord.Embed(title=f"Documentos contendo: {name}")

    for url,tfidf in dicio.items():
        embed.add_field(name=url,value=tfidf,inline=False)

    embed.color = discord.Color.dark_blue()
         
    return embed

def pretty_IP(info):
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
   
async def web_scrapping(url,dump_path,ctx,max_l=10):
    # Parametros:
    # url: Url where webscrapping will be made
    # dump_path: Path to cache folder
    # max_l: max requisitions

    jumped_urls = []

    # Doing the webscrapping
    nome_urls = dict()
    next_urls = [url]
    l=0
    while next_urls:
        url_now = next_urls[0]
        if l<max_l:
            
            try:
                page = requests.get(url=url_now,timeout=15)
                #Twitter don't work very well
                if page.status_code == 200 and re.search("^text/html",page.headers["Content-Type"]):
                    soup = BeautifulSoup(page.content, "html.parser")
                    next_urls_tags = soup.find_all('a',href=True)
                    text = soup.get_text()
                    clean_text = re.sub(r'[^\x00-\x7F]+', '', text)
                    
                    # Filename creation
                    name = re.sub(r'[.:/]','',url_now)
                    data_name = name + ".joblib"
                    filename = os.path.join(dump_path,data_name)

                    if not os.path.exists(filename):
                        with open(filename,'wb') as f:
                            nome_urls[data_name] = url_now
                            await ctx.send(f"Webscrapping from <{url_now}> was sucessesful")
                            joblib.dump(clean_text,f)
                            l+=1                    
                    
                    for a in next_urls_tags:
                        
                        link = a['href']
                
                        if URL_validate(link) is False:
                            link = urljoin(url_now, link)                 
                            
                        next_urls.append(link)  
                        
            except Exception as e:
                print(e)
                jumped_urls.append(url_now)
                await ctx.send(f"The following url was jumped: {url_now}")
        
        next_urls.pop(0)
        
    return nome_urls,jumped_urls   
     
def inverted_index(total_data,doc_names):

    vectorizer = TfidfVectorizer()
    tfidf = vectorizer.fit_transform(total_data)

    res = dict()
    
    for word in vectorizer.get_feature_names_out():
        j = vectorizer.vocabulary_[word]
        doc_df = dict()
        for i in range(len(doc_names)):
            if tfidf[i,j]>0:
                doc_df[doc_names[i]] = tfidf[i,j]
        res[word] = doc_df
    
    return res

def search_words(palavras, indice):
    assert type(palavras)==list
    resultado = dict()
    notfounded = []
    founded_words = []
    
    for p in palavras:
        p = p.lower()
        if p in indice.keys():
            founded_words.append(p)        
            for documento in indice[p].keys():
                if documento not in resultado.keys():
                    resultado[documento] = indice[p][documento]
                else:
                    resultado[documento] += indice[p][documento]
        else:
            notfounded.append(p)
    return resultado,notfounded,founded_words

def wn_search_words(palavra : str, indice : dict):
    # Only accepts one word. Using a lot of words make the bot send lots of messages because
    # would make one for each one of the possible combinations with the words synonims 
    
    palavra = palavra.lower()
    s_urlTfidf = dict()
    
    word_syn = wordnet.synsets(palavra)
    if not word_syn:
        return None
    word_syn = word_syn[0]

    maior_similaridade = 0
    maior_similar = None

    for palavra in indice.keys():
        palavra_syn = wordnet.synsets(palavra)
        if not palavra_syn:
            continue
        palavra_syn = palavra_syn[0]
        similarity = palavra_syn.wup_similarity(word_syn)
        if similarity > maior_similaridade:
            maior_similar = palavra
            maior_similaridade = similarity
    
    s_urlTfidf,b,c = search_words(maior_similar,indice)
    return s_urlTfidf


