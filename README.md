# Depach's Cogs

A collection of cogs for [Red-DiscordBot](https://github.com/Cog-Creators/Red-DiscordBot). AutoRoom is the only cog currently available in this repository.

AutoRoom is forked from [PhasecoreX's PCXCogs repository](https://github.com/PhasecoreX/PCXCogs), specifically its [AutoRoom cog](https://github.com/PhasecoreX/PCXCogs/tree/master/autoroom).

## AutoRoom

AutoRoom creates temporary voice rooms when members join a configured source channel. Room owners can manage access, set user limits, and customize their room. Rooms are removed when empty.

See the [AutoRoom guide](autoroom/README.md) for setup instructions, the full command list, and details about role-based permissions.

## Install

The examples use `.` as the bot prefix. Replace it with your configured prefix if different.

```text
.repo add depachcogs https://github.com/depach/PCXCogs
.cog install depachcogs autoroom
.load autoroom
```
