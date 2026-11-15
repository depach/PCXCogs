# Depach's Cogs

A collection of cogs for [Red-DiscordBot](https://github.com/Cog-Creators/Red-DiscordBot). The repository currently includes AutoRoom and FlashNDash.

AutoRoom is forked from [PhasecoreX's PCXCogs repository](https://github.com/PhasecoreX/PCXCogs), specifically its [AutoRoom cog](https://github.com/PhasecoreX/PCXCogs/tree/master/autoroom).

## AutoRoom

AutoRoom creates temporary voice rooms when members join a configured source channel. Room owners can manage access, set user limits, and customize their room. Rooms are removed when empty.

See the [AutoRoom guide](autoroom/README.md) for setup instructions, the full command list, and details about role-based permissions.

## FlashNDash

FlashNDash watches configured text channels and deletes posts after a selected or configured duration. Durations can be chosen through DM buttons or included in the post text, and role pings can be disabled. Configure it with `.flashndash settings`; `.fnd` remains as a command alias.

## Install

The examples use `.` as the bot prefix. Replace it with your configured prefix if different.

```text
.repo add depachcogs https://github.com/depach/PCXCogs
.cog install depachcogs autoroom
.load autoroom
.cog install depachcogs flashndash
.load flashndash
```
