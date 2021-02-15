import os
import json
from discord.ext import commands

class MaintenanceMode(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.guilds_dir = './guilds/'
        if not os.path.exists(self.guilds_dir):
            os.makedirs(self.guilds_dir)


    @commands.command(name='start')
    async def _start(self, ctx):
        # Check if not already in maintenance mode
        guild_infos = {}
        guild_infos_file = self.guilds_dir + str(ctx.guild.id) + '.json'
        if os.path.exists(guild_infos_file):
            with open(guild_infos_file) as json_file:
                guild_infos = json.load(json_file)
            if guild_infos['is_in_maintenance'] == True:
                await ctx.send("Maintenance mode already running!")
                return
        
        # Store and remove all roles attributions
        users_roles = {}
        for member in ctx.guild.members:
            if member != ctx.author and member != self.bot.user:
                roles_list = member.roles[1:]
                roles_ids_list = [role.id for role in roles_list]
                users_roles[member.id] = roles_ids_list
                # await member.remove_roles(*roles_list)
                await member.edit(roles=[])
        
        # Store and remove everyone's "view channel" permission
        everyone_view_channels_permission = ctx.guild.default_role.permissions.view_channel
        permissions = ctx.guild.default_role.permissions
        permissions.update(view_channel=False)
        await ctx.guild.default_role.edit(permissions=permissions)
        
        # Save in json file
        guild_infos['users_roles'] = users_roles
        guild_infos['everyone_view_channels_permission'] = everyone_view_channels_permission
        guild_infos['is_in_maintenance'] = True

        with open(guild_infos_file, 'w') as json_file:
            json.dump(guild_infos, json_file, indent=4)

        # Feedback
        await ctx.message.add_reaction('\N{WHITE HEAVY CHECK MARK}')


    @commands.command(name='stop')
    async def _stop(self, ctx):
        # Check if in maintenance mode
        guild_infos = {}
        guild_infos_file = self.guilds_dir + str(ctx.guild.id) + '.json'
        if not os.path.exists(guild_infos_file):
            await ctx.send("Maintenance mode already stopped!")
            return
        else:
            with open(guild_infos_file) as json_file:
                guild_infos = json.load(json_file)
            if guild_infos['is_in_maintenance'] == False:
                await ctx.send("Maintenance mode already stopped!")
                return
        
        # Rerieve and re-add all roles attributions
        for member_id, roles_ids in guild_infos['users_roles'].items():
            member = ctx.guild.get_member(int(member_id))
            roles_list = [ctx.guild.get_role(role_id) for role_id in roles_ids if ctx.guild.get_role(role_id) is not None]
            # await member.add_roles(*roles_list)
            await member.edit(roles=roles_list)
        
        # Retrieve and re-add everyone's "view channel" permission
        everyone_view_channels_permission = guild_infos['everyone_view_channels_permission']
        permissions = ctx.guild.default_role.permissions
        permissions.update(view_channel=everyone_view_channels_permission)
        await ctx.guild.default_role.edit(permissions=permissions)
        
        # Update json file
        guild_infos['is_in_maintenance'] = False

        with open(guild_infos_file, 'w') as json_file:
            json.dump(guild_infos, json_file, indent=4)

        # Feedback
        await ctx.message.add_reaction('\N{WHITE HEAVY CHECK MARK}')
        await ctx.send("INFO: Take note that the everyone role's permission for \"View Channels\" has been set to " + str(everyone_view_channels_permission))


def setup(bot):
    bot.add_cog(MaintenanceMode(bot))
