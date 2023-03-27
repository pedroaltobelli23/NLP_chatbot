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
   
def web_scrapping(url,dump_path,max_l=10):
    # Parametros:
    # url: url aonde sera feito o web scrapping
    # dump_path: path para a pasta de cache
    # max_l: max de requesicoes que podem ser feitas
    # Retorna nada
    jumped_urls = []
    # Fazendo o web scrapping da url
    nome_urls = dict()
    next_urls = [url]
    l=0
    while next_urls:
        url_now = next_urls[0]
        if l<max_l:
            
            try:
                page = requests.get(url=url_now,timeout=15)
                #Twitter nao funciona muito bem
                if page.status_code == 200 and re.search("^text/html",page.headers["Content-Type"]):
                    soup = BeautifulSoup(page.content, "html.parser")
                    next_urls_tags = soup.find_all('a',href=True)
                    # print(len(next_urls_tags))
                    text = soup.get_text()
                    clean_text = re.sub(r'[^\x00-\x7F]+', '', text)
                    
                    # Criacao do nome do arquivo aonde o texto sera guardado
                    name = re.sub(r'[.:/]','',url_now)
                    data_name = name + ".joblib"
                    filename = os.path.join(dump_path,data_name)
                    # print(url_now)
                    # print(filename)
                    # dump do texto contido na url em um arquivo .joblib. 
                    # So 'e feito o dump se o arquivo nao existe
                    if not os.path.exists(filename):
                        with open(filename,'wb') as f:
                            nome_urls[data_name] = url_now
                            joblib.dump(clean_text,f)
                            l+=1
                            # print("foi")
                    
                    
                    for a in next_urls_tags:
                        
                        link = a['href']
                
                        if URL_validate(link) is False:
                            link = urljoin(url_now, link)                 
                            
                        next_urls.append(link)  

            except Exception as e:
                # print(f"algo deu errado,pulando essa url:{url_now}")
                print(e)
                jumped_urls.append(url_now)
        
        next_urls.pop(0)
        
    # dict_words = inverted_index(PATH,doc_names)
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