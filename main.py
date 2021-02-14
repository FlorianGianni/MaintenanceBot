# +---------------+
# |    LIBRARY    |
# +---------------+

import discord
import logging
import os
from dotenv import load_dotenv
from discord.ext import commands



# +---------------+
# |    LOGGING    |
# +---------------+

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)



# +---------------+
# |  ENVIRONMENT  |
# +---------------+

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')



# +---------------+
# |      BOT      |
# +---------------+

class MaintenanceBot(commands.Bot):
    def __init__(self, command_prefix, intents):
        super().__init__(command_prefix=command_prefix, intents=intents)
    
    async def on_ready(self):
        print('Logged in as {0} ({0.id})'.format(self.user))
        print('---------')
    

intents = discord.Intents.default()
intents.members = True # Needed in order to store the members' roles

bot = MaintenanceBot(command_prefix=commands.when_mentioned_or("!m "), intents=intents)
bot.load_extension('cogs.maintenancemode')
bot.run(TOKEN)
