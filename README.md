# fnvmm

A Nix-inspired mod manager for Fallout: New Vegas.

## Philosophy

- **Declarative.** You describe the mod setup you want, the tool figures out how to realize it, rather than performing setup steps by hand.
- **Store-backed.** Mod content is ingested into a managed store rather than left scattered across ad hoc folders. The live game directory is generated from the store plus your config, it isn't edited directly and isn't the source of truth.
- **Conflicts resolved by ordering, not luck.** Where mods overlap, resolution happens through an explicit priority/load order.
- **CLI, plain text config.** No GUI, no custom interactive TUI standing between you and the state of your install. Config is text you can read and edit directly.
- **Linux/Proton-first.** Built for a Linux modding setup from the ground up, not a Windows tool with Linux support bolted on.

## Status

Early and under active development.
