import discord
from discord.ext import commands
from rag import responder_con_estilo
from config import DISCORD_TOKEN

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")

@bot.command()
async def hola(ctx):
    await ctx.send("¡Hola! Soy un bot inteligente. Pregúntame algo sobre los documentos PDF.")


@bot.command()
async def pregunta(ctx, *, texto):
    message_to_edit = await ctx.send("Buscando respuesta...")
    respuesta = responder_con_estilo(texto)
    CHAR_LIMIT = 1990

    if len(respuesta) > CHAR_LIMIT:
        await message_to_edit.edit(content=respuesta[:CHAR_LIMIT])
        for i in range(CHAR_LIMIT, len(respuesta), CHAR_LIMIT):
            await ctx.reply(respuesta[i:i+CHAR_LIMIT], mention_author=False)
    else:
        await message_to_edit.edit(content=respuesta)

bot.run(DISCORD_TOKEN)
