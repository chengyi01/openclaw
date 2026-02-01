# 保留的 Skills（9个）

## 金融工具
- **cmb-credit-card-analysis** - 招商银行信用卡分析（✓ 中国本地服务）

## 开发工具
- **coding-agent** - 代码助手（✓ 本地工具）
- **model-usage** - 模型使用统计（✓ 本地分析）
- **skill-creator** - Skill 创建工具（✓ 本地工具）

## 笔记工具
- **notion** - Notion API（可通过 VPN 使用）
- **obsidian** - Obsidian 本地笔记（✓ 本地工具）

## 系统工具
- **session-logs** - 会话日志分析（✓ 本地工具）
- **tmux** - 终端复用管理（✓ 本地工具）
- **video-frames** - 视频帧提取（✓ 本地工具）

# 已移除的 Skills

## 移除原因
这些 skills 在中国大陆环境下无法使用或受限，已于 2026-02-01 移除。

## 备份位置
完整备份保存在：`../skills.backup.20260201_142813/`

## 移除的 Skills 列表（44个）

### 国外服务依赖
- **1password** - 1Password 密码管理器（国外服务）
- **gemini** - Google Gemini AI（国外服务）
- **github** / **clawhub** - GitHub 相关（访问受限）
- **openai-image-gen** / **openai-whisper** / **openai-whisper-api** - OpenAI 服务（访问受限）
- **oracle** - Oracle 云服务（国外服务）
- **perplexity** - Perplexity AI（国外服务）

### 即时通讯平台
- **discord** - Discord（国外服务）
- **slack** - Slack（国外服务）
- **telegram** - Telegram（访问受限）

### Apple 生态专属
- **apple-notes** - Apple Notes（仅限 Apple 设备）
- **apple-reminders** - Apple Reminders（仅限 Apple 设备）
- **bear-notes** - Bear Notes（仅限 macOS/iOS）
- **things-mac** - Things（仅限 macOS）
- **imsg** / **bluebubbles** / **blucli** - iMessage 相关（仅限 Apple 生态）

### 特定硬件/平台
- **nano-banana-pro** - Banana Pro 硬件
- **eightctl** - 智能家居控制
- **openhue** - Philips Hue 智能灯光

### 媒体娱乐
- **spotify-player** - Spotify（国外服务）
- **sonoscli** / **songsee** - Sonos 音响系统
- **gog** - GOG 游戏平台（国外服务）
- **mcporter** - Minecraft 相关

### 其他工具
- **bird** / **himalaya** - 邮件客户端（依赖国外邮件服务）
- **blogwatcher** - 博客监控
- **camsnap** - 摄像头工具
- **canvas** - 绘图工具
- **food-order** - 外卖服务
- **gifgrep** - GIF 搜索
- **goplaces** / **local-places** - 地图服务（依赖 Google Maps）
- **nano-pdf** - PDF 工具
- **ordercli** - 订单管理
- **peekaboo** - 屏幕工具
- **sag** - 未知服务
- **sherpa-onnx-tts** - TTS 服务
- **summarize** - 摘要工具
- **trello** - Trello 项目管理（国外服务）
- **voice-call** - 语音通话
- **wacli** - WhatsApp CLI（访问受限）
- **weather** - 天气服务（可能依赖国外 API）

## 恢复方法

如需恢复某个 skill，可从备份目录复制：
```bash
cp -r skills.backup.20260201_142813/<skill-name> skills/
```

## 注意事项
1. 移除这些 skills 不会影响 OpenClaw 系统的核心功能
2. Skills 系统会自动跳过不存在的 skill 目录
3. 保留的 9 个 skills 在中国大陆环境下可正常使用
4. 如果未来网络环境改善，可以从备份恢复需要的 skills
