import discord
from utils.functions import Website

def pretty_crawl(url_sv):
    embed = discord.Embed(title="Web Crawling completed for the following pages: ")
    for a in url_sv:
        embed.add_field(name=a.url,value=f"Page Sentiment Value: {a.sentiment_value:.4f}",inline=False)
    embed.color = discord.Color.yellow()
    return embed

def pretty_search(url_tdidf : dict,words : list,th : float):
    wordss = " ".join(words)
    title=f"Documents containing: {wordss} Sorted by relevance using th={th:.4f}"
    embed = discord.Embed(title=title)
    
    for url,tfidf in url_tdidf.items():
        embed.add_field(name=url,value=f"TFiDF: {tfidf[0]:.4f} \n Page Sentiment Value: {tfidf[1]:.4f}",inline=False)

    embed.color = discord.Color.dark_blue()
    
    return embed

def pretty_not_founded(not_founded_words : list):
    title="the following word(s) was/were not found in the database: "
    embed = discord.Embed(title=title)
    
    for word in not_founded_words:
        embed.add_field(name=word,value="",inline=False)
    
    embed.color = discord.Color.red()
    return embed
        
def pretty_wn(name,dicio : dict,th : float):
    embed = discord.Embed(title=f"Documents containing: {name} Sorted by relevance using th={th:.4f}")

    for url,tfidf in dicio.items():
        embed.add_field(name=url,value=f"TFiDF: {tfidf[0]:.4f} \n Page Sentiment Value: {tfidf[1]:.4f}",inline=False)

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

def pretty_urls(urls_sentiment):
    embed = discord.Embed(title="Web scrapped urls: ")
    for url,sv in urls_sentiment.items():
        embed.add_field(name=url,value=f"Page Sentiment Value: {sv}",inline=False)
    embed.color = discord.Color.yellow()
    return embed
