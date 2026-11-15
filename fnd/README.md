# FlashNDash

FlashNDash is an original cog by Depach for temporary posts. It watches one or more configured text channels and deletes each post after its selected duration. Pending deletions are stored so they survive bot restarts.

Commands below use `.` as the Red bot prefix. Replace it with your server's configured prefix if different. The command group is `.flashndash`, with `.fnd` as a shorter alias; examples use `.fnd`.

## Setup

Choose one or more text channels to watch and, optionally, a role to notify when media is posted.

```text
.fnd channel #posts
.fnd channels add #more-posts
.fnd role @PostNotifications
```

The bot needs permission to read messages in watched channels, send messages there, and manage messages so it can delete posts and notification messages. Role mentions must also be allowed by the server's role and bot permissions.

Use `.fnd settings` to review the current configuration.

## How Posts Work

Every non-bot message in a watched channel is scheduled for deletion, including text-only messages. Duration is chosen using DM buttons by default. You can instead use caption mode, where the bot reads the first valid minute duration such as `5m` or `10m` from the message text. If no valid duration appears, it uses the configured default.

Role notifications are separate from post tracking. They are sent only when a post includes an uploaded image or video attachment. Text-only posts, linked media, and GIF/GIFV uploads do not trigger a role ping. When sent, the notification is deleted along with the original post.

### Duration Modes

- `dm`: the poster gets buttons for the configured duration options. If they do not choose within five minutes, the default is used.
- `caption`: the poster does not receive a duration DM. Include a duration such as `5m`, `10m`, or `30m` in the post text. Values from 1 minute to 7 days are supported; missing or invalid values use the default.

The default options are 5, 10, 15, and 30 minutes. You can configure up to 10 duration options, from 1 minute to 7 days. The default duration must be one of the configured options.

## Admin Commands

These commands require server management permissions.

| Command | Description |
| --- | --- |
| `.fnd channel <channel>` | Set the primary watched channel. Running without a channel clears all watched channels. |
| `.fnd channels` | List watched channels. Alias form: `.fnd channels list`. |
| `.fnd channels add <channel>` | Add another watched text channel. |
| `.fnd channels remove <channel>` | Stop watching one channel. |
| `.fnd channels clear` | Stop watching all channels. |
| `.fnd role [role]` | Set the global ping role. Omit the role to clear the global role. |
| `.fnd channelrole <channel> [role]` | Set a role for one channel. Omit the role to remove that channel's override and use the global role. |
| `.fnd roleping on\|off` | Enable or disable role pings globally without clearing role settings. |
| `.fnd durationmode dm\|caption` | Choose DM buttons or duration text in the post caption. |
| `.fnd options <minutes...>` | Set 1-10 DM button durations, each from 1 to 10080 minutes. Example: `.fnd options 5 10 15 30`. |
| `.fnd defaultminutes <minutes>` | Set the fallback duration. It must match one of the configured options. |
| `.fnd settings` | Show watched channels, global and per-channel roles, duration settings, and pending deletions. |

A channel-specific ping role overrides the global role only for that channel. If the override is removed, the global role is used. Clearing the global role does not clear channel-specific roles. Turning role pings off disables notifications in all watched channels, including those with overrides.

## Install

```text
.repo add depachcogs https://github.com/depach/PCXCogs
.cog install depachcogs fnd
.load fnd
```
