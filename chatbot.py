import discord


intents = discord.Intents.default()
intents.members = True

text_file = open("token.txt", "r")
TOKEN = text_file.read()
text_file.close()

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    guild = discord.utils.get(client.guilds, name='A Cidade dos Robôs')
    channel = discord.utils.get(guild.text_channels, name='bot-training')
    await channel.send('O bot está online!')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.lower() == '!oi':
        await message.channel.send('Olá!')

client.run(TOKEN)