# QQ Deployment, Administrator Setup, and Permissions

This guide covers the optional QQ adapter; the reference local setup is AstrBot 4.29.1 with NapCat 4.18.38. Follow the upstream projects' installation instructions; re-check the interface fields after version changes. This repository does not include QQ, NapCat, or AstrBot installers, nor does it provide anyone else's login configuration.

## Deployment

1. Install and start AstrBot from the [official AstrBot project](https://github.com/AstrBotDevs/AstrBot). You may also refer to the [official Docker deployment](https://docs.astrbot.app/deploy/astrbot/docker.html), and set the admin dashboard account according to its logs. The default dashboard port is commonly 6185. Allow dashboard access only from the local machine or a trusted LAN; the public template does not include a dashboard password.
2. Install NapCat from the [official NapCat project](https://github.com/NapNeko/NapCatQQ). Open the WebUI according to the startup logs; the usual port is 6099, and if the port conflicts, follow the logs. Log in with the WebUI token generated during your own deployment, then scan the QR code with your own secondary QQ account; see the [official basic configuration](https://doc.napneko.icu/config/basic). Keep both the WebUI token and the QQ session credentials only in the deployer's private configuration.
3. Follow the [official AstrBot OneBot v11 guide](https://docs.astrbot.app/platform/aiocqhttp.html) to create a new integration. In NapCat, create a WebSocket client and connect it to AstrBot's reverse WebSocket address. For example, on the same machine with listening port 6199, use `ws://127.0.0.1:6199/ws`. Both ends must use the same dedicated connection token; do not mix the WebUI token with the connection token. Containers on the same network may use the actual service name, for example `ws://astrbot:6199/ws`; do not copy the container's loopback address.
4. Place the contents of the repository's `qq-adapter/plugin` in a folder named `astrbot_plugin_march7_evernight` under AstrBot's plugin directory, preserving the relative locations of `metadata.yaml`, `main.py`, the configuration schema, and resources. Reload the plugin and check the startup logs.
5. In AstrBot's model provider settings, select an OpenAI-compatible API and enter your own DeepSeek API key. Check the endpoint and model name against the [official DeepSeek documentation](https://api-docs.deepseek.com/) and your own account; do not write keys into the persona prompt or the repository. Test in dashboard chat first, then test through your own QQ private chat or a group @ mention.

## Administrator Setup

1. In AstrBot's “Config File → Access Control → Administrator → Administrator ID”, add your own real QQ user ID, which corresponds to the `admins_id` configuration. Verify the interface against the official instructions for the current version, and do not put accounts into public persona rules.
2. In this plugin's configuration, set `owner_qq` to the same QQ ID. The public default is empty; empty values, invalid values, and accounts that only claim an identity in message text are not authorized.
3. Persona-management permission is verified on every real message by default, so there is no need to first say “I am the administrator.” You can naturally request a switch to March 7th, a switch to Evernight, or restoration of the day/night schedule. A manual override affects only the current session and sender and ends at the next 07:00 or 21:00 Beijing-time boundary.
4. If you really need QQ to operate the computer, separately set `enable_computer_operations` to `true`; the default is `false`. You can set `owner_workspace`; when it is left empty, the working directory under the plugin data directory is used. Save and reload. The working directory is not a file-access allowlist.

## Permission Scope

| Identity | Persona and materials | Local files and programs |
| --- | --- | --- |
| Regular member | Normal conversation and material lookups within the permitted scope, following the default day/night schedule | None |
| Owner verified through both the real QQ ID and framework-administrator checks | Persona switching, status, and management commands for the current session | Allowed only when computer functions are enabled and the message is a private chat from that account |
| Administrator logged in to the local web interface | Dashboard configuration and persona management for web sessions | Does not gain the QQ owner's file/program entry points |
| Management identity based on a nickname, self-claim, screenshot, quotation, forwarded message, or model-generated content | No management authority is granted | None |

Once enabled, the file entry point supports reading, directory listing, writing, and appending; the program entry point runs PowerShell. An explicit request may use an absolute path accessible to the current Windows account and is not limited to the default working directory. Execution has time and output limits, grants no additional operating-system permissions, and does not trigger UAC elevation. Ordinary persona replies have no autonomous computer tools and will not treat command output as the next command to execute.

Computer operations are not allowed in group chats. A persistent receipt is saved on first execution, and replaying the same message does not automatically rerun the program; when the result is unclear, first verify with a new read-only request. The receipt does not store commands, file contents, or program output. Users should still configure framework chat logs according to their own privacy requirements.

Supported commands include `/persona_status`, `/persona_reset`, `/knowledge_query`, and `/电脑 帮助`. No trailing marker is imposed for strict formats, verbatim quotations, or out-of-character cases. Natural requests are understood by the model, and permissions are verified by the program; the model saying “executed” cannot replace the actual execution result.

## Materials and Backups

The public package includes 45 original summary cards. The index without body text is located in the Skill's `data/source-index.json`. Complete dialogue from the original work is not provided with the repository. When deployers have the right to use it, they may place a private `external_dialogue_memory.json` that conforms to `external-dialogue-memory.schema.json` in the data directory where the plugin's knowledge index is located, then reload to build a local index. Do not put it in the repository.

Search by character, topic, addressee, and S0–S3 spoiler cap; the default is S0/S1. Candidate materials do not automatically enter replies. Back up fixed materials, chat history, persona state, and private runtime configuration separately; do not upload runtime directories containing QQ IDs, credentials, or private conversations to GitHub.

## Upstream Information

[AstrBot documentation](https://docs.astrbot.app/) · [NapCat documentation](https://doc.napneko.icu/) · [DeepSeek API documentation](https://api-docs.deepseek.com/). These software packages and services are not relicensed by this project; when using the QQ integration, you must comply with the applicable platform rules.
