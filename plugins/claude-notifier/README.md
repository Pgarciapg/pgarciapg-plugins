# Claude Notifier

Audio notifications for Claude Code on macOS.

## Features

- **Glass sound** - Plays when Claude finishes a task (Stop hook)
- **Funk sound** - Plays when Claude needs permission approval (Notification hook)

## Installation

1. Copy the `claude-notifier` folder to `~/.claude/plugins/`
2. Enable the plugin in Claude Code settings or run `/plugins` and enable it

## Requirements

- macOS (uses built-in system sounds via `afplay`)

## Customization

To change the sounds, edit `plugin.json` and replace the sound file paths. Available macOS system sounds:

- `/System/Library/Sounds/Basso.aiff`
- `/System/Library/Sounds/Blow.aiff`
- `/System/Library/Sounds/Bottle.aiff`
- `/System/Library/Sounds/Frog.aiff`
- `/System/Library/Sounds/Funk.aiff`
- `/System/Library/Sounds/Glass.aiff`
- `/System/Library/Sounds/Hero.aiff`
- `/System/Library/Sounds/Morse.aiff`
- `/System/Library/Sounds/Ping.aiff`
- `/System/Library/Sounds/Pop.aiff`
- `/System/Library/Sounds/Purr.aiff`
- `/System/Library/Sounds/Sosumi.aiff`
- `/System/Library/Sounds/Submarine.aiff`
- `/System/Library/Sounds/Tink.aiff`
