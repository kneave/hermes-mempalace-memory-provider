# Hermes MemPalace Memory Provider

A small [Hermes Agent](https://github.com/NousResearch/hermes-agent) memory-provider plugin that uses [MemPalace](https://github.com/MemPalace/mempalace) for automatic semantic recall.

When enabled, Hermes searches your local MemPalace before each turn and injects relevant past context as a fenced `<memory-context>` block. This gives Hermes automatic recall from MemPalace without requiring the model to explicitly call a MemPalace MCP tool.

## What this plugin does

- Registers a context-only Hermes `MemoryProvider` named `mempalace`.
- Runs `mempalace search <query> --results 3` before each user turn.
- Extracts only drawer content lines from the CLI output.
- Fails open: if MemPalace is unavailable, slow, or returns no matches, Hermes continues normally with no injected context.
- Exposes **no LLM tools**. MemPalace MCP tools remain separate for explicit search/write operations.

## What this plugin does not do

- It does not upload data to a cloud service.
- It does not write new memories into MemPalace.
- It does not replace Hermes built-in `MEMORY.md` / `USER.md` memory.
- It does not bundle or install MemPalace itself.

## Requirements

- Hermes Agent with memory-provider plugin support.
- MemPalace installed and initialized.
- The `mempalace` command available on the PATH used by Hermes.

Check MemPalace:

```bash
mempalace status
mempalace search "test" --results 1
```

If Hermes runs from a virtualenv and `mempalace` is installed there, ensure that virtualenv's `bin/` directory is on Hermes' PATH.

## Installation

Hermes user-installed memory providers live directly under `~/.hermes/plugins/<name>/`.

```bash
mkdir -p ~/.hermes/plugins/mempalace
curl -fsSL https://raw.githubusercontent.com/rusty4444/hermes-mempalace-memory-provider/main/__init__.py \
  -o ~/.hermes/plugins/mempalace/__init__.py
curl -fsSL https://raw.githubusercontent.com/rusty4444/hermes-mempalace-memory-provider/main/plugin.yaml \
  -o ~/.hermes/plugins/mempalace/plugin.yaml

hermes config set memory.provider mempalace
hermes memory status
```

Then start a new Hermes session or run `/reset`.

## Activation

```yaml
# ~/.hermes/config.yaml
memory:
  memory_enabled: true
  user_profile_enabled: true
  provider: mempalace
```

Verify:

```bash
hermes memory status
```

Expected:

```text
Provider:  mempalace
Plugin:    installed ✓
Status:    available ✓
```

## How it works

The provider implements `agent.memory_provider.MemoryProvider`:

- `name` returns `mempalace`.
- `is_available()` runs `mempalace status`.
- `system_prompt_block()` tells Hermes that MemPalace automatic recall is active.
- `prefetch(query)` runs `mempalace search`, extracts `>`-prefixed drawer content lines, and returns:

```xml
<memory-context>
[System note: The following is recalled memory context from MemPalace, NOT new user input. Treat as authoritative reference data.]
> recalled drawer content
</memory-context>
```

- `get_tool_schemas()` returns `[]`, making this a context-only provider.

## Privacy and security

This repo contains no credentials, hostnames, private IP addresses, tokens, or user-specific configuration.

Runtime privacy is determined by your local MemPalace database and Hermes configuration:

- The plugin shells out to the local `mempalace` CLI.
- It does not send data over the network itself.
- It injects search results from your MemPalace into Hermes prompts, so anything stored in MemPalace can become visible to the selected LLM provider.
- Treat MemPalace contents as prompt context, not as a secret store.

## Troubleshooting

### `hermes memory status` says provider is unavailable

Run:

```bash
which mempalace
mempalace status
```

If `mempalace` is only available in a virtualenv, start Hermes from that environment or expose the venv `bin/` directory in PATH.

### No context appears

Run a direct search:

```bash
mempalace search "the thing you asked Hermes about" --results 3
```

If MemPalace returns no `>` content lines, the provider has nothing to inject.

### Changes do not take effect

Memory providers initialize at agent startup. Start a new Hermes session or run `/reset` after installing or changing `memory.provider`.

## Related projects

- [MemPalace](https://github.com/MemPalace/mempalace) — local searchable memory palace for projects and conversations.
- [Hermes Agent](https://github.com/NousResearch/hermes-agent) — open-source AI agent framework.

## License

MIT
