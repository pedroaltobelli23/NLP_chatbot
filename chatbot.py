import discord
import os
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

text_file = open("token.txt", "r")
TOKEN = text_file.read()
text_file.close()

client = discord.Client(intents=intents)
git_url = "https://github.com/pedroaltobelli23/NLP_chatbot"

@client.event
async def on_ready():
    guild = discord.utils.get(client.guilds, name='A Cidade dos Robôs')
    channel = discord.utils.get(guild.text_channels, name='privado')
    await channel.send('O bot está online!')

@client.event
async def on_message(message):
    if message.content=='!source':
        await message.channel.send(git_url)
    if message.content=='!author':
        await message.channel.send("Author: Pedro Altobelli \n e-mail: pedroatp@al.insper.edu.br")

client.run(TOKEN)