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
    def __init__(self, command_prefix):
        super().__init__(command_prefix=command_prefix)

bot = MaintenanceBot(command_prefix="!")
bot.run(TOKEN)
