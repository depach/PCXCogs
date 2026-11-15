# Depach's Cogs

A collection of cogs for [Red-DiscordBot](https://github.com/Cog-Creators/Red-DiscordBot).

AutoRoom is forked from [PhasecoreX's PCXCogs repository](https://github.com/PhasecoreX/PCXCogs), specifically its [AutoRoom cog](https://github.com/PhasecoreX/PCXCogs/tree/master/autoroom).

## AutoRoom

AutoRoom creates temporary voice rooms when members join a configured source channel. Room owners can manage access, set user limits, and customize their room. Rooms are removed when empty.

See the [AutoRoom guide](autoroom/README.md) for setup instructions, the full command list, and details about role-based permissions.

## FND (FlashNDash)

FND is an original cog by Depach for temporary posts. It watches one or more text channels and deletes posts after a selected duration. Posters can choose a duration through DM buttons or include one in the post text (for example, `5m` or `10m`). Role pings can use a server-wide role or a different role per channel, and are sent only for uploaded image/video media, not text-only posts or GIFs.

Configure FND with `.fnd settings`. Common setup commands:

```text
.fnd channel #posts
.fnd channels add #other-posts
.fnd role @PostNotifications
.fnd channelrole #other-posts @OtherNotifications
.fnd durationmode caption
```

Use `.fnd durationmode dm` to return to DM duration buttons, and `.fnd roleping off` to disable role pings globally. FND's command prefix is configurable with the bot.

## Install

The examples use `.` as the bot prefix. Replace it with your configured prefix if different.

```text
.repo add depachcogs https://github.com/depach/PCXCogs
.cog install depachcogs autoroom
.load autoroom
.cog install depachcogs fnd
.load fnd
```
