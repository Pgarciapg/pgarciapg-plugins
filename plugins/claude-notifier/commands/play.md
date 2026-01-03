---
description: Play a specific system sound by name
allowed_args: sound_name
---

# Play Sound

Play a specific macOS system sound.

The user will provide a sound name as an argument. Play it using:

```bash
afplay /System/Library/Sounds/$ARGUMENTS.aiff
```

If the sound doesn't exist, list available sounds and let the user know.
