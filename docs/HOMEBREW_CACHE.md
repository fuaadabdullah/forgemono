---
description: "HOMEBREW_CACHE"
---

# Homebrew cache / temp — per-user (recommended)

Why
---
On some machines (small system volumes, external volumes mounted as `/Volumes/Fuaad`) Homebrew's default cache/temp location can end up on a nearly-full system volume which blocks downloads and upgrades (e.g. `brew upgrade gh`). To avoid that, it's safe and common to point Homebrew cache and temp to a per-user directory on your home volume.

What I changed for you (automated)
---

- Backed up your `~/.zshrc` to `~/.zshrc.bak.<timestamp>` before editing.
- Replaced any existing `HOMEBREW_CACHE` export with:

  export HOMEBREW_CACHE="$HOME/tmp/homebrew/cache"

- Ensured `HOMEBREW_TEMP` is set to:

  export HOMEBREW_TEMP="$HOME/tmp/homebrew/temp"

- Created the directories `~/tmp/homebrew/cache` and `~/tmp/homebrew/temp` with your user as owner.

Why this is safe
---

- The change is non-destructive: your old cache remains where it was unless you delete it explicitly. Homebrew will now download bottles to a path within your home directory where you typically have much more free space.
- If you prefer a different location (another drive), set those env vars to that path instead.

How to verify (one-liner)
---
After opening a new shell (or running `source ~/.zshrc`) run:

```bash
echo $HOMEBREW_CACHE
echo $HOMEBREW_TEMP
ls -ld "$HOME/tmp/homebrew"/*
```

How to temporarily override for a single command
---
If you want one run to use a different cache or temp (without changing `~/.zshrc`), do:

```bash

HOMEBREW_CACHE=/path/with/space HOMEBREW_TEMP=/path/with/space brew upgrade gh
```

Rollback / undo
---
If you want to revert the change, restore your previous `~/.zshrc` backup (replace `<timestamp>` with the timestamped backup created):

```bash
cp ~/.zshrc.bak.<timestamp> ~/.zshrc
source ~/.zshrc
```

Optional next steps
---
- If you want to reclaim the old cache contents under `/Volumes/Fuaad/tmp/Homebrew` you can move the files to another volume or delete them. Be careful — only delete caches you created intentionally.
- If you'd rather keep Homebrew cache on a different external volume, set the exports above to that volume's path instead.

Notes
---
This file was added automatically by a workspace maintenance run. If you'd like me to move existing cached bottles to the new location or create a symlink from the old cache to the new cache, tell me and I will perform that with your confirmation.
