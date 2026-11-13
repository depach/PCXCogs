# AutoRoom

AutoRoom creates a temporary voice channel when a member joins a configured source channel. The member is moved into the new room, which is deleted when it becomes empty.

This repository is a fork of [AutoRoom by PhasecoreX](https://github.com/PhasecoreX/PCXCogs/tree/master/autoroom).

Commands below use `.` as the Red bot prefix. Replace it with your server's configured prefix if different.

## Setup

Create a voice channel to use as the source and a category to hold generated rooms. The source and destination can be in different categories.

```text
.autoroomset create <source_voice_channel> <destination_category>
```

The setup wizard asks for a default room type and naming format. After creating the source, join it to test room creation. Run `.autoroomset permissions` if the bot reports missing permissions; `.autoroomset settings` shows configured sources and server-wide access settings.

AutoRoom needs permission to view and connect to the source, move members, and create/manage channels in the destination category. Permission requirements vary with room type and optional text channels; the permissions command reports the specific requirements.

## Member Commands

After creating a room, AutoRoom posts a command guide in its chat. This uses the room's built-in voice-channel chat, or its separate legacy text channel when that option is enabled. A server-managed room only shows the settings command because it has no member owner.

| Command | Description |
| --- | --- |
| `.autoroom settings` | Show room owner, access mode, and current allowed/denied members and roles. Aliases: `about`, `info`. |
| `.autoroom name <name>` | Rename your room. |
| `.autoroom bitrate <kbps>` | Set the room bitrate, subject to the server limit. Alias: `kbps`. |
| `.autoroom users <limit>` | Set the user limit. Use `0` for no limit. Alias: `userlimit`. |
| `.autoroom public` | Make the room visible and joinable according to its base access settings. |
| `.autoroom locked` | Keep the room visible but prevent default access from joining. You can still invite people with `allow`. |
| `.autoroom private` | Hide the room from default access. You can still invite people with `allow`. |
| `.autoroom allow <member or role>` | Allow a member or role into the room. Alias: `add`. |
| `.autoroom deny <member or role>` | Deny a member or role. If possible, members who lose access are disconnected. Aliases: `ban`, `block`. |
| `.autoroom claim` | Claim a room after its owner has left, subject to the claim cooldown. |

Room-management commands are owner-controlled. Server admin, moderator, and configured bot-role access can also grant join access to new rooms, depending on the room settings.

## Admin Commands

These commands require server management permissions.

| Command | Description |
| --- | --- |
| `.autoroomset create <source> <category>` | Set up a source channel through the interactive wizard. Aliases: `enable`, `add`. |
| `.autoroomset remove <source>` | Stop using a voice channel as a source. Aliases: `disable`, `delete`, `del`. |
| `.autoroomset settings` | Show server access settings and each source's configuration. |
| `.autoroomset permissions` | Check required and optional bot permissions. Alias: `perms`. |
| `.autoroomset access admin` | Toggle admin access to newly created locked/private rooms. Enabled by default. |
| `.autoroomset access mod` | Toggle moderator access to newly created locked/private rooms. Disabled by default. |
| `.autoroomset access bot add <role>` | Allow members with this bot role into all new rooms. |
| `.autoroomset access bot remove <role>` | Remove a bot role from the server-wide access list. |

### Source Settings

Use `.autoroomset modify` to change a configured source. `<source>` is its voice channel.

| Command | Description |
| --- | --- |
| `.autoroomset modify category <source> <category>` | Change the destination category. |
| `.autoroomset modify type public\|locked\|private\|server <source>` | Set the default type for new rooms. `server` rooms have no owner. |
| `.autoroomset modify name username\|game <source>` | Choose a built-in room-name format. |
| `.autoroomset modify name custom <source> <template>` | Set a custom room-name template. |
| `.autoroomset modify permissions clone <source>` | Copy permission overwrites from the source channel (default mode). |
| `.autoroomset modify permissions roles <source>` | Use explicit role rules instead of copying source overwrites. |
| `.autoroomset modify permissions allow <source> <role>` | Allow a role in new rooms and enable role mode. |
| `.autoroomset modify permissions deny <source> <role>` | Deny a role in new rooms and enable role mode. |
| `.autoroomset modify permissions remove <source> <role>` | Remove a role from both role lists. |
| `.autoroomset modify text set <source> <message>` | Set a template message sent to each new room's chat. |
| `.autoroomset modify text disable <source>` | Disable the custom message. The built-in command guide remains enabled. |
| `.autoroomset modify specialperms ownermodify <source>` | Toggle the owner's native Manage Channels permission. |
| `.autoroomset modify specialperms sendmessage <source>` | Toggle sending messages in the built-in voice-channel chat. |
| `.autoroomset modify legacytextchannel enable\|disable <source>` | Create or stop creating a separate text channel with each room. |
| `.autoroomset modify legacytextchannel topic set <source> <topic>` | Set a topic template for the separate text channel. |
| `.autoroomset modify legacytextchannel topic disable <source>` | Clear the topic template. |
| `.autoroomset modify defaults` | Explain how source channel settings are inherited. |

### Role Permission Mode

Clone mode remains the default and preserves the existing behavior: source-channel overwrites are copied to new rooms, except `Manage Roles`. The bot must have the relevant permissions allowed in the destination category or server for them to be copied.

Role mode does not copy source overwrites. New rooms start with the configured public, locked, or private access, then apply the source's allow and deny role lists. The source channel still controls who can join the source and create a room. Admin, moderator, bot-role, and room-owner access are added separately when a room is created.

For example, configure role mode and a permitted role with:

```text
.autoroomset modify permissions allow #CreateRoom @Members
```

Adding an allow or deny rule automatically enables role mode. Use `remove` to clear a rule, `roles` to enable role mode without adding one, or `clone` to return to copied overwrites. View the current mode and role lists with `.autoroomset settings`.

When a room owner switches their current room to `.autoroom locked` or `.autoroom private`, the room's explicit overwrites for roles on that source's default allow list are removed. This affects only the current room; the source defaults remain in effect for rooms created later. Owners can still grant specific room access with `.autoroom allow`.

### Member Roles and Hidden Sources

The source channel can also restrict who is allowed to create rooms. If `@everyone` cannot connect to the source, roles allowed to connect there are treated as member roles. Only members with one or more of those roles can use that source. You can also hide the source by denying `@everyone` view access while allowing eligible members to connect.

## Templates

Room names support these variables:

- `{{username}}`: the room owner's username.
- `{{game}}`: the game the owner is playing, or an empty value.
- `{{dupenum}}`: an incrementing number used to distinguish duplicate names.

Templates support `if`/`elif`/`else`/`endif` statements and `lower`/`upper` filters. For example:

```text
{{username}}'s Room{% if dupenum > 1 %} ({{dupenum}}){% endif %}
```

The same template syntax is available for the custom room-chat message and legacy text-channel topic. The message template also supports `{{mention}}` for the room owner's mention.
