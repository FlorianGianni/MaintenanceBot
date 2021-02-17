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
    

    def __get_maintenance_mode(self, guild_id):
        # 0 -> Disabled
        # 1 -> Stopping
        # 2 -> Starting
        # 3 -> Enabled
        guild_infos_file = self.guilds_dir + str(guild_id) + '.json'
        if not os.path.exists(guild_infos_file):
            return 0
        else:
            with open(guild_infos_file) as json_file:
                guild_infos = json.load(json_file)
            return guild_infos['maintenance_mode']
    

    def __get_guild_infos(self, guild_id):
        guild_infos_file = self.guilds_dir + str(guild_id) + '.json'
        if os.path.exists(guild_infos_file):
            with open(guild_infos_file) as json_file:
                guild_infos = json.load(json_file)
            return guild_infos
        else:
            return {}
    

    def __dump_guild_infos(self, guild_id, guild_infos):
        if not os.path.exists(self.guilds_dir):
            os.makedirs(self.guilds_dir)
        guild_infos_file = self.guilds_dir + str(guild_id) + '.json'
        with open(guild_infos_file, 'w') as json_file:
            json.dump(guild_infos, json_file, indent=4)


    @commands.Cog.listener()
    async def on_member_join(self, member):
        # If a member joins during maintenance, add maintenance role
        if self.__get_maintenance_mode(member.guild.id) in (2, 3):
            guild_infos = self.__get_guild_infos(member.guild.id)
            if 'maintenance_role_id' in guild_infos.keys():
                maintenance_role_id = guild_infos['maintenance_role_id']
                maintenance_role = member.guild.get_role(maintenance_role_id)
                await member.edit(roles=[maintenance_role])
    

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        # If a channel is created during maintenance, add maintenance role overwrite
        if self.__get_maintenance_mode(channel.guild.id) == 3:
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
        # Check if maintenance mode can be enabled
        if self.__get_maintenance_mode(ctx.guild.id) == 1:
            await ctx.message.add_reaction('\N{CROSS MARK}')
            await ctx.reply("Maintenance mode is stopping! Please wait before trying to re-enable it.")
            return
        elif self.__get_maintenance_mode(ctx.guild.id) == 2:
            await ctx.message.add_reaction('\N{CROSS MARK}')
            await ctx.reply("Maintenance mode is already starting!")
            return
        elif self.__get_maintenance_mode(ctx.guild.id) == 3:
            await ctx.message.add_reaction('\N{CROSS MARK}')
            await ctx.reply("Maintenance mode is already enabled!")
            return
        
        await ctx.message.add_reaction('\N{HOURGLASS WITH FLOWING SAND}')
        
        # Store information about maintenance mode starting
        guild_infos = {}
        guild_infos['maintenance_mode'] = 2
        self.__dump_guild_infos(ctx.guild.id, guild_infos)

        # Create a maintenance role without any permission in every channel
        maintenance_role = await ctx.guild.create_role(name='MaintenanceRole')
        guild_infos['maintenance_role_id'] = maintenance_role.id
        self.__dump_guild_infos(ctx.guild.id, guild_infos)
        channels = ctx.guild.channels
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
        guild_infos['maintenance_channel_id'] = maintenance_channel.id
        self.__dump_guild_infos(ctx.guild.id, guild_infos)
        await maintenance_channel.send('This server is in maintenance!')
        
        # Store each role attributions
        users_roles = {}
        for member in ctx.guild.members:
            if member != ctx.author and not member.bot:
                # Store user role
                roles_ids_list = [role.id for role in member.roles[1:]]
                users_roles[member.id] = roles_ids_list
        
        guild_infos['users_roles'] = users_roles
        self.__dump_guild_infos(ctx.guild.id, guild_infos)

        # Disconnect all members from voice channels and add maintenance role
        for member in ctx.guild.members:
            if member != ctx.author and not member.bot:
                # Remove every role and add maintenance role
                await member.edit(roles=[maintenance_role])
            # Disconnect member from voice channel (including bots)
            await member.edit(voice_channel=None)
        
        # Store information about maintenance mode being enabled
        guild_infos['maintenance_mode'] = 3
        self.__dump_guild_infos(ctx.guild.id, guild_infos)

        # Confirms to user that maintenance mode is enabled
        await ctx.message.clear_reactions()
        await ctx.message.add_reaction('\N{WHITE HEAVY CHECK MARK}')
        await ctx.reply("Maintenance mode is now enabled!")


    @commands.command(name='disable')
    @is_guild_owner()
    async def _disable(self, ctx):
        # Check if maintenance mode can be disabled
        if self.__get_maintenance_mode(ctx.guild.id) == 0:
            await ctx.message.add_reaction('\N{CROSS MARK}')
            await ctx.reply("Maintenance mode is already disabled!")
            return
        elif self.__get_maintenance_mode(ctx.guild.id) == 1:
            await ctx.message.add_reaction('\N{CROSS MARK}')
            await ctx.reply("Maintenance mode is already stopping!")
            return
        elif self.__get_maintenance_mode(ctx.guild.id) == 2:
            await ctx.message.add_reaction('\N{CROSS MARK}')
            await ctx.reply("Maintenance mode is starting! Please wait before trying to disable it.")
            return
        
        await ctx.message.add_reaction('\N{HOURGLASS WITH FLOWING SAND}')

        # Store information about maintenance mode stopping
        guild_infos = self.__get_guild_infos(ctx.guild.id)
        guild_infos['maintenance_mode'] = 1
        self.__dump_guild_infos(ctx.guild.id, guild_infos)
        
        # Re-add each role attributions
        for member_id, roles_ids in guild_infos['users_roles'].items():
            member = ctx.guild.get_member(int(member_id))
            if member is not None:
                roles_list = [ctx.guild.get_role(role_id) for role_id in roles_ids if ctx.guild.get_role(role_id) is not None]
                await member.edit(roles=roles_list)
        
        # Delete the maintenance channel
        maintenance_channel_id = guild_infos['maintenance_channel_id']
        maintenance_channel = ctx.guild.get_channel(maintenance_channel_id)
        if maintenance_channel is not None:
            await maintenance_channel.delete()

        # Delete the maintenance role
        maintenance_role_id = guild_infos['maintenance_role_id']
        maintenance_role = ctx.guild.get_role(maintenance_role_id)
        if maintenance_role is not None:
            await maintenance_role.delete()
        
        # Store information about maintenance mode being disabled
        guild_infos = {}
        guild_infos['maintenance_mode'] = 0
        self.__dump_guild_infos(ctx.guild.id, guild_infos)

        # Confirms to user that maintenance mode is disabled
        await ctx.message.clear_reactions()
        await ctx.message.add_reaction('\N{WHITE HEAVY CHECK MARK}')
        await ctx.reply("Maintenance mode is now disabled!")


def setup(bot):
    bot.add_cog(MaintenanceMode(bot))
