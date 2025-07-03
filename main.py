import discord
import os
import aiofiles
import re
import random
import string

TOKEN = 'MTM4Nzk1MjAwMDA1ODI2NTY4MA.GnNJYd.LH4nPBoSxfWUxvhVifwcfz7r8jmoqZbmhkAUx4'

intents = discord.Intents.default()
intents.messages = True
intents.dm_messages = True

client = discord.Client(intents=intents)

def random_name(length=8):
    return ''.join(random.choices(string.ascii_letters, k=length))

def obfuscate_lua(code: str) -> str:
    # Remove comments
    code = re.sub(r'--.*', '', code)
    # Remove multiline comments
    code = re.sub(r'--\[\[.*?\]\]', '', code, flags=re.DOTALL)
    # Remove extra whitespace
    code = re.sub(r'\n\s*\n', '\n', code)
    code = re.sub(r'[ \t]+', ' ', code)

    # Find all variable/function names (simple heuristic)
    names = set(re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', code))
    # Exclude Lua keywords
    keywords = {
        'and','break','do','else','elseif','end','false','for','function','goto','if','in','local','nil','not','or','repeat','return','then','true','until','while'
    }
    names = [n for n in names if n not in keywords]

    # Map to random names
    name_map = {n: random_name() for n in names}

    # Replace names in code
    def replace_names(match):
        word = match.group(0)
        return name_map.get(word, word)
    code = re.sub(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', replace_names, code)

    # Optionally encode strings (simple hex encoding)
    def encode_string(match):
        s = match.group(0)
        encoded = ''.join('\\x{:02x}'.format(ord(c)) for c in s[1:-1])
        return '"' + encoded + '"'
    code = re.sub(r'\".*?\"', encode_string, code)

    return "-- Obfuscated by PythonObfuscator\n" + code

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

@client.event
async def on_message(message):
    # Only respond to DMs, ignore bot's own messages
    if message.author == client.user or not isinstance(message.channel, discord.DMChannel):
        return

    # Only process .lua files
    if message.attachments:
        for attachment in message.attachments:
            if attachment.filename.endswith('.lua'):
                input_path = f'tmp_{message.author.id}.lua'
                output_path = f'obf_{message.author.id}.lua'
                await attachment.save(input_path)

                try:
                    # Read the original Lua code
                    async with aiofiles.open(input_path, 'r') as f:
                        code = await f.read()

                    # Obfuscate
                    obfuscated = obfuscate_lua(code)

                    # Write the obfuscated code
                    async with aiofiles.open(output_path, 'w') as f:
                        await f.write(obfuscated)

                    # Send back the obfuscated file
                    async with aiofiles.open(output_path, 'rb') as f:
                        await message.channel.send("Here's your obfuscated script:", file=discord.File(f, output_path))

                except Exception as e:
                    await message.channel.send(f"Error: {e}")

                finally:
                    if os.path.exists(input_path):
                        os.remove(input_path)
                    if os.path.exists(output_path):
                        os.remove(output_path)
            else:
                await message.channel.send("Please send a `.lua` file to obfuscate.")
    else:
        await message.channel.send("Send me a Lua script as a file attachment to obfuscate it!")

client.run(TOKEN)
