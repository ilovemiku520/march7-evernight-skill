# Optional AstrBot adapter

This directory is a runnable optional adapter, separate from the portable Skill. It targets AstrBot 4.29.1 on the `aiocqhttp` (OneBot) and authenticated `webchat` transports. Install the contents of `plugin/` as `astrbot_plugin_march7_evernight` in AstrBot's plugin directory, then configure the provider and QQ connection in AstrBot. The Python modules use the standard library and AstrBot; they do not install a model service or store its API key.

See the repository's translated deployment and permission guides before enabling host access. The administrator must configure both AstrBot's administrator list and this plugin's `owner_qq`. Its default is empty: messages cannot claim or activate owner status. An authenticated WebChat administrator can control its own persona session, but cannot acquire the QQ owner's identity or host-operation permissions.

`enable_computer_operations` defaults to `false`. Explicitly enabling it permits the configured, framework-verified QQ owner to request file reads/writes and PowerShell program execution in a direct QQ private message. Every request checks transport, sender ID, administrator role, private context, and a plain top-level message. This is the current Windows account's existing access, including accessible paths outside the default workspace; it does not elevate via UAC. `owner_workspace` only selects the default command working directory. Empty selects AstrBot's plugin data directory plus `owner-workspace`; it is not a sandbox or file allowlist.

Fixed public knowledge is stored in `plugin/resources/knowledge/`. This release contains original summaries and source references, not the author's private full dialogue corpus. Locally supplied `external_dialogue_memory.json` belongs beside the plugin's generated knowledge database. It is validated before indexing and is never a configuration or permission source. Candidates, other speakers, scene-specific lines, and spoiler levels remain distinct. An exact quotation is used as a style reference only when it is attributed, approved for expression, relevant to the topic, and belongs to the actual current speaker.

By default, the schedule uses Beijing time: March 7th from 07:00 to 21:00 and Evernight from 21:00 to 07:00. March's occasional imitation is a brief daytime scene. Successful manual control is scoped to the current conversation and sender. The adapter records successful delivery before advancing persona progress, uses persistent receipts to prevent duplicate host actions, strips decorative role markers after role exit, and preserves strict JSON, code, URLs, literal quotes, and musical notation.

Run the offline contract tests from this directory:

```text
python -m unittest discover -s tests -p "test_*.py"
```

The suite uses synthetic account IDs, temporary directories, framework doubles, and harmless bounded local test commands. It does not connect to QQ, send messages, request model APIs, or require a provider key. The optional host-operation tests require Windows PowerShell on Windows; platform-dependent cases may skip elsewhere. Tests are not a deployment or a live QQ end-to-end certification.
