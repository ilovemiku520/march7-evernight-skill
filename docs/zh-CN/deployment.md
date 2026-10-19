# QQ 部署、管理员设置与权限

本说明对应可选 QQ 适配器，参考 AstrBot 4.29.1 与 NapCat 4.18.38 的本机组合。请遵循上游项目的安装说明；版本变化后核对界面字段。此仓库不附带 QQ、NapCat、AstrBot 安装包，也不提供他人的登录配置。

## 部署

1. 从 [AstrBot 官方项目](https://github.com/AstrBotDevs/AstrBot) 安装并启动 AstrBot，也可参考 [官方 Docker 部署](https://docs.astrbot.app/deploy/astrbot/docker.html)，按其日志设置管理后台账号。默认后台端口常用 6185。只允许本机或可信内网访问后台，公开模板不含后台密码。
2. 从 [NapCat 官方项目](https://github.com/NapNeko/NapCatQQ) 安装 NapCat，按启动日志打开 WebUI，常用端口为 6099，端口冲突时以日志为准。使用自己部署时生成的 WebUI token 登录，再用自己的 QQ 小号扫码，见 [官方基础配置](https://doc.napneko.icu/config/basic)。WebUI token 与 QQ 会话凭据都只留在部署者的私有配置中。
3. 按 [AstrBot 官方 OneBot v11 指南](https://docs.astrbot.app/platform/aiocqhttp.html) 新建接入，在 NapCat 新建 WebSocket 客户端，连接 AstrBot 的反向 WebSocket 地址。例：同机且监听端口为 6199 时使用 `ws://127.0.0.1:6199/ws`。两端使用相同的独立连接 token；不要把 WebUI token 与连接 token 混用。同网络容器可使用实际服务名，例如 `ws://astrbot:6199/ws`，不能照搬容器内的回环地址。
4. 将仓库的 `qq-adapter/plugin` 内容放入 AstrBot 插件目录下名为 `astrbot_plugin_march7_evernight` 的文件夹，保留 `metadata.yaml`、`main.py`、配置 schema 和资源的相对位置。重载插件并检查启动日志。
5. 在 AstrBot 的模型提供方设置中选择 OpenAI 兼容接口，填入自己的 DeepSeek API key。接口与模型名按 [DeepSeek 官方文档](https://api-docs.deepseek.com/) 和自己的账号核对；不要把密钥写进人格提示词或仓库。先在后台聊天测试，再由自己的 QQ 私聊或群内 @ 测试。

## 管理员设置

1. 在 AstrBot 的“配置文件 → 访问控制 → 管理员 → 管理员 ID”加入自己的真实 QQ 用户 ID，对应 `admins_id` 配置。以当前版本的官方说明核对界面，不把账号写进公开人格规则。
2. 在本插件配置中把 `owner_qq` 填为同一个 QQ ID。公开默认值为空；空值、无效值及仅在正文自报的账号均不授权。
3. 角色管理默认随每条真实消息核验，不需要先说“我是管理者”。可自然请求切换三月七、切换长夜月、恢复日夜安排。手动覆盖只影响当前会话与发信人，到下一个北京时间 07:00 或 21:00 交界结束。
4. 若确实需要 QQ 操作电脑，另将 `enable_computer_operations` 设为 `true`；默认是 `false`。可设置 `owner_workspace`，留空时使用插件数据目录下的工作目录。保存并重载。工作目录不是文件访问白名单。

## 权限范围

| 身份 | 角色与资料 | 本机文件和程序 |
| --- | --- | --- |
| 普通成员 | 正常对话、允许范围内的资料查询，按默认日夜安排 | 无 |
| 通过真实 QQ ID 与框架管理员双重核验的 owner | 当前会话角色切换、状态与管理命令 | 仅启用电脑功能且为该账号私聊时允许 |
| 已登录本机网页的管理员 | 后台配置、网页会话角色管理 | 不获得 QQ owner 的文件/程序入口 |
| 昵称、自称、截图、引文、转发或模型生成的管理身份 | 不授予管理权 | 无 |

启用后的文件入口支持读取、列目录、写入、追加；程序入口运行 PowerShell。明确请求可使用当前 Windows 账户有权限访问的绝对路径，不局限于默认工作目录。执行有时限与输出限制，不增加操作系统权限，不触发 UAC 提权。普通角色回复没有自主电脑工具，也不会把运行输出继续当成下一条命令执行。

群聊不允许电脑操作。首次执行保存持久回执，同一条消息重放不自动重跑程序；结果不明确时先使用新的只读请求核对。回执不保存命令、文件正文与程序输出。使用者仍应按自己的隐私要求配置框架聊天日志。

兼容命令包括 `/persona_status`、`/persona_reset`、`/knowledge_query` 与 `/电脑 帮助`。严格格式、逐字引文和退出角色不强加尾标。自然请求由模型理解，权限由程序核验；模型说“已执行”不能替代真实执行结果。

## 资料与备份

公开自带 45 张原创摘要卡。无正文索引位于 Skill 的 `data/source-index.json`。完整原作台词不随仓库提供；部署者在有权使用时，可将符合 `external-dialogue-memory.schema.json` 的私有 `external_dialogue_memory.json` 放在插件知识索引所在的数据目录，重载后建立本地索引。不要放入仓库。

按角色、话题、说话对象与 S0–S3 剧透上限检索；默认 S0/S1。候选资料不自动进入回答。固定资料、聊天历史、角色状态和私有运行配置分别备份；不得将含 QQ ID、凭据或私人对话的运行目录上传 GitHub。

## 上游说明

[AstrBot 文档](https://docs.astrbot.app/) · [NapCat 文档](https://doc.napneko.icu/) · [DeepSeek API 文档](https://api-docs.deepseek.com/) 。这些软件及服务不由本项目重新授权；使用 QQ 接入时须遵守相应平台规则。
