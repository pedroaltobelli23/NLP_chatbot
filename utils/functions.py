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
from dotenv import load_dotenv,find_dotenv
import shutil
import pickle
from keras.layers import Input, Dense, Activation, TextVectorization, Embedding, GRU,Bidirectional
from keras.models import Model
import tensorflow as tf
from sklearn.preprocessing import OneHotEncoder

load_dotenv(find_dotenv())
CLF = tf.keras.saving.load_model("model/notebooks/model")
FILE_CLASS_PICKLE = os.getenv('FILE_CLASS_PICKLE')

class Website:
    def __init__(self,name,url,sentiment_value,text):
        self.name = name
        self.url = url
        self.sentiment_value = sentiment_value
        self.text = text

def URL_validate(url):
    re_url = "^((http|https)://)[-a-zA-Z0-9@:%._\\+~#?&//=]{2,256}\\.[a-z]{2,6}\\b([-a-zA-Z0-9@:%._\\+~#?&//=]*)$"
    r = re.compile(re_url)

    if (re.search(r, url)):
        return True
    return False


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
   
def web_scrapping(url,max_l=10):
    # Parametros:
    # url: Url where webscrapping will be made
    # dump_path: Path to cache folder
    # max_l: max requisitions

    jumped_urls = []

    # Doing the webscrapping
    nome_urls = []
    next_urls = [url]
    l=0
    stop_tag = False
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
                    
                    name = re.sub(r'[.:/]','',url_now)

                    if not os.path.isfile(FILE_CLASS_PICKLE):#if file with list of classes don't exist
                        with open(FILE_CLASS_PICKLE,"wb") as f:
                            predict_val = CLF.predict([clean_text])[0][1]
                            predict_val = fixed_sentiment_value(predict_val)
                            site = Website(name=name,url=url_now,sentiment_value=predict_val,text=clean_text) #getting the positive value
                            pickle.dump([site],f)
                    else:
                        with open(FILE_CLASS_PICKLE,'rb') as f:
                            list_websites = pickle.load(f)
                            for website in list_websites:
                                if website.name == name:
                                    stop_tag = True    
                                
                            if stop_tag == False:
                                predict_val = CLF.predict([clean_text])[0][1]
                                predict_val = fixed_sentiment_value(predict_val)
                                site = Website(name=name,url=url_now,sentiment_value=predict_val,text=clean_text) #getting the positive porcentage
                                list_websites.append(site)
                                nome_urls.append(url_now)
                                l+=1
                            else:
                                stop_tag=False
                            
                        with open(FILE_CLASS_PICKLE,"wb") as f:
                            pickle.dump(list_websites,f)
                    
                    for a in next_urls_tags:
                        
                        link = a['href']
                
                        if URL_validate(link) is False:
                            link = urljoin(url_now, link)                 
                            
                        next_urls.append(link)  
            except Exception as e:
                print(e)
                jumped_urls.append(url_now)
        next_urls.pop(0)
    return nome_urls,jumped_urls   
     
def inverted_index():
    with open(FILE_CLASS_PICKLE,'rb') as f:
        list_websites = pickle.load(f)
        total_data = [obj.text for obj in list_websites]
        doc_names = [obj.url for obj in list_websites]
        sentiment_values = [obj.sentiment_value for obj in list_websites]
        
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

def search_words(palavras, indice, th=-1):
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

def filter_by_th(resultado : dict,th : float = -1):
    new_resultado = dict()
    
    docs_sentiment = get_all_urls_and_positivity()
    
    for key in docs_sentiment.keys() & resultado.keys():
        if docs_sentiment.get(key) > th:
            new_resultado[key] = resultado.get(key)
    
    return new_resultado

def get_all_urls_and_positivity():
    with open(FILE_CLASS_PICKLE,'rb') as f:
        list_websites = pickle.load(f)
    
    docs_sentiment = dict()
    
    for obj in list_websites:
        docs_sentiment[obj.url] = obj.sentiment_value
    return docs_sentiment

def wn_search_words(palavra : str, indice : dict):
    # Only accepts one word. Using a lot of words make the bot send lots of messages because
    # would make one for each one of the possible combinations with the words synonims 
    
    palavra = palavra.lower()
    s_urlTfidf = dict()
    
    word_syn = wordnet.synsets(palavra)
    if not word_syn:
        # print("Palavra nao tem synset")
        return None
    word_syn = word_syn[0]

    maior_similaridade = 0
    maior_similar = None

    for w in indice.keys():
        w_syn = wordnet.synsets(w)
        if not w_syn:
            continue
        
        w_syn = w_syn[0]
        similarity = w_syn.wup_similarity(word_syn)
        if similarity > maior_similaridade:
            maior_similar = w
            maior_similaridade = similarity
    
    s_urlTfidf,b,c = search_words([maior_similar],indice)
    res = dict()
    res[maior_similar] = s_urlTfidf
    return res

def fixed_sentiment_value(value):
    return 2*value - 1

