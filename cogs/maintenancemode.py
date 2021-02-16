import os
import json
import discord
from discord.ext import commands


def is_guild_owner():
    def predicate(ctx):
        return ctx.guild is not None and ctx.guild.owner_id == ctx.author.id
    return commands.check(predicate)


class MaintenanceMode(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.guilds_dir = './guilds/'
        if not os.path.exists(self.guilds_dir):
            os.makedirs(self.guilds_dir)
    

    def __is_in_maintenance(self, guild_id):
        guild_infos_file = self.guilds_dir + str(guild_id) + '.json'
        if not os.path.exists(guild_infos_file):
            return False
        else:
            with open(guild_infos_file) as json_file:
                guild_infos = json.load(json_file)
            return guild_infos['is_in_maintenance']
    

    def __get_guild_infos(self, guild_id):
        guild_infos_file = self.guilds_dir + str(guild_id) + '.json'
        if os.path.exists(guild_infos_file):
            with open(guild_infos_file) as json_file:
                guild_infos = json.load(json_file)
            return guild_infos
        else:
            return None
    

    def __dump_guild_infos(self, guild_id, guild_infos):
        if not os.path.exists(self.guilds_dir):
            os.makedirs(self.guilds_dir)
        guild_infos_file = self.guilds_dir + str(guild_id) + '.json'
        with open(guild_infos_file, 'w') as json_file:
            json.dump(guild_infos, json_file, indent=4)


    @commands.Cog.listener()
    async def on_member_join(self, member):
        if self.__is_in_maintenance(member.guild.id):
            guild_infos = self.__get_guild_infos(member.guild.id)
            maintenance_role_id = guild_infos['maintenance_role_id']
            maintenance_role = member.guild.get_role(maintenance_role_id)
            await member.edit(roles=[maintenance_role])
    

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        # If in maintenance, add maintenance role permission to new channel
        if self.__is_in_maintenance(channel.guild.id):
            guild_infos = self.__get_guild_infos(channel.guild.id)
            maintenance_role_id = guild_infos['maintenance_role_id']
            maintenance_role = channel.guild.get_role(maintenance_role_id)
            allow = discord.Permissions.none()
            deny = discord.Permissions.all()
            overwrite = discord.PermissionOverwrite.from_pair(allow=allow, deny=deny)
            await channel.set_permissions(maintenance_role, overwrite=overwrite)


    @commands.command(name='enable')
    @is_guild_owner()
    async def _enable(self, ctx):
        # Check if not already in maintenance mode
        if self.__is_in_maintenance(ctx.guild.id):
            await ctx.send("Maintenance mode already enabled!")
            return

        # Create a maintenance role without any permissions in aevery channel
        maintenance_role = await ctx.guild.create_role(name='MaintenanceRole')
        maintenance_role_id = maintenance_role.id
        channels = await ctx.guild.fetch_channels()
        for channel in channels:
            allow = discord.Permissions.none()
            deny = discord.Permissions.all()
            overwrite = discord.PermissionOverwrite.from_pair(allow=allow, deny=deny)
            await channel.set_permissions(maintenance_role, overwrite=overwrite)
        
        # Create a maintenance channel with read-only permission
        allow = discord.Permissions.none()
        allow.update(view_channel=True, read_message_history=True)
        deny = discord.Permissions.all()
        deny.update(view_channel=False, read_message_history=False)
        permissions = discord.PermissionOverwrite.from_pair(allow=allow, deny=deny)
        overwrites={ctx.guild.default_role: permissions}
        maintenance_channel = await ctx.guild.create_text_channel('maintenance', overwrites=overwrites)
        maintenance_channel_id = maintenance_channel.id
        await maintenance_channel.send('This server is in maintenance!')
        
        # Disconnect members from voice channels and store and remove all roles attributions
        users_roles = {}
        for member in ctx.guild.members:
            if member != ctx.author and not member.bot:
                # Store and remove his role
                roles_list = member.roles[1:]
                roles_ids_list = [role.id for role in roles_list]
                users_roles[member.id] = roles_ids_list
                await member.edit(roles=[maintenance_role])

            # Disconnect member from voice channel (including bots)
            await member.edit(voice_channel=None)
        
        # Save in json file
        guild_infos = {}
        guild_infos['maintenance_role_id'] = maintenance_role_id
        guild_infos['maintenance_channel_id'] = maintenance_channel_id
        guild_infos['users_roles'] = users_roles
        guild_infos['is_in_maintenance'] = True

        self.__dump_guild_infos(ctx.guild.id, guild_infos)

        # Feedback
        await ctx.message.add_reaction('\N{WHITE HEAVY CHECK MARK}')


    @commands.command(name='disable')
    @is_guild_owner()
    async def _disable(self, ctx):
        # Check if in maintenance mode
        if not self.__is_in_maintenance(ctx.guild.id):
            await ctx.send("Maintenance mode already disabled!")
            return

        guild_infos = self.__get_guild_infos(ctx.guild.id)
        
        # Rerieve and re-add all roles attributions
        for member_id, roles_ids in guild_infos['users_roles'].items():
            member = ctx.guild.get_member(int(member_id))
            if member is not None:
                roles_list = [ctx.guild.get_role(role_id) for role_id in roles_ids if ctx.guild.get_role(role_id) is not None]
                await member.edit(roles=roles_list)
        
        # Delete maintenance channel
        maintenance_channel_id = guild_infos['maintenance_channel_id']
        maintenance_channel = ctx.guild.get_channel(maintenance_channel_id)
        await maintenance_channel.delete()

        # Delete the maintenance role
        maintenance_role_id = guild_infos['maintenance_role_id']
        await ctx.guild.get_role(maintenance_role_id).delete()
        
        # Update json file
        guild_infos = {}
        guild_infos['is_in_maintenance'] = False

        self.__dump_guild_infos(ctx.guild.id, guild_infos)

        # Feedback
        await ctx.message.add_reaction('\N{WHITE HEAVY CHECK MARK}')


def setup(bot):
    bot.add_cog(MaintenanceMode(bot))
