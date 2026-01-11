# BNB Chain meme 推文极速提醒器

基于 X API v2 filtered stream 实时监听指定大佬账号推文，最快解析 BSC 合约地址（CA）并推送到 Telegram，帮助你在 Binance App Web3 Wallet 里尽快完成手动买入操作。

> 免责声明：该项目**不做自动交易/不接触私钥**，仅做监听与通知。

## 功能亮点

- X API v2 filtered stream 长连接，支持规则管理与断线重连
- 超快正则解析 BSC 合约地址（`0x` + 40 hex），并提取 ticker / 关键词
- Telegram 推送：手机端友好、一键复制 CA + 关键链接
- 可选风控：Dexscreener 秒级检查流动性与 24h 量

## 项目目录

```
.
├── accounts.json
├── README.md
├── requirements.txt
└── src
    ├── __init__.py
    ├── config.py
    ├── main.py
    ├── notifier.py
    ├── parser.py
    ├── riskcheck.py
    └── x_stream.py
```

## 准备工作

### 1) 申请 X API v2 权限

1. 申请 X Developer 账号并创建 App
2. 获取 `Bearer Token`
3. 确认应用有 `tweet.read` 权限（filtered stream 需要 Elevated 权限）

注意事项：
- filtered stream 需要稳定网络；X API 可能偶发限流，请保证重连逻辑
- 仅监听指定账号，避免规则过宽导致配额消耗

### 2) 创建 Telegram Bot

1. 在 Telegram 搜索 `@BotFather`
2. `/newbot` 创建 bot，获取 `TG_BOT_TOKEN`
3. 获取 `TG_CHAT_ID`
   - 可以用 `@userinfobot` 获取个人 chat id
   - 或将 bot 拉入群后获取群组 chat id

## 配置

创建 `.env` 文件：

```
X_BEARER_TOKEN=xxx
TG_BOT_TOKEN=xxx
TG_CHAT_ID=123456789
RISK_CHECK_ENABLED=true
LAST_SEEN_PATH=.state/last_seen.json
```

编辑 `accounts.json`：

```json
{
  "accounts": [
    "big_kol_one",
    "big_kol_two",
    "big_kol_three"
  ]
}
```

## 本地运行

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/main.py
```

## VPS 部署（systemd）

1) 拷贝项目到服务器并安装依赖
2) 创建 systemd service：

```
[Unit]
Description=BNB Chain Meme Tweet Alert
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/bnb-meme-alert
EnvironmentFile=/opt/bnb-meme-alert/.env
ExecStart=/opt/bnb-meme-alert/.venv/bin/python /opt/bnb-meme-alert/src/main.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

3) 启动与开机自启：

```bash
sudo systemctl daemon-reload
sudo systemctl enable bnb-meme-alert
sudo systemctl start bnb-meme-alert
sudo systemctl status bnb-meme-alert
```

## 推送格式（示例）

```
BNB MEME 推文提醒 | @kol | 2024-01-01T00:00:00Z
0x1234...abcd
Tweet Link
Dexscreener
风险提示：已检测到流动性 | 流动性 $12.3K | 24h量 $45.6K
```

## 安全说明

- 不包含私钥/助记词/交易签名逻辑
- 日志不输出 token
- 只做监听与通知，交易由用户在 Binance App 手动完成
