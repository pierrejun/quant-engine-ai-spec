# quant-engine-ai-spec

一个面向量化分析与投顾式输出的 MVP 项目，目标是把“数据采集 -> 特征提取 -> 证据构建 -> 决策输出 -> 风险修正 -> 报告生成 -> 机器人分发”串成一条可复现、可回放、可迁移的分析链路。

当前项目已经支持：

- 美股 `US` 分析
- A 股 `CN` 分析
- 标准 Markdown 报告与详细 Markdown 报告
- `LIVE / DEMO` 双模式
- 当天结果缓存复用
- Telegram 机器人触发与回传
- 本地结构化产物落盘，便于排查与迁移到 OpenClaw

## 项目目标

这个项目的核心思路不是“直接让模型生成一段主观观点”，而是先把分析过程拆成结构化步骤，再基于规则和证据输出结果：

1. 采集价格、基本面、新闻等原始数据
2. 计算技术面、估值、质量、情绪、事件等特征
3. 把特征转换成带方向和强度的 evidence
4. 用规则引擎生成 `buy / hold / sell`
5. 用风控逻辑对结论进行降级或修正
6. 输出面向人类阅读的中文报告
7. 通过 Telegram 等渠道把结果回传给用户

这样做的好处是：

- 每一步都能落盘和复盘
- 报告内容能追溯到具体因子
- 便于以后迁移到 OpenClaw 或接入其他渠道

## 当前数据源策略

### US 市场

- 价格：`Yahoo`
- 基本面：`Finnhub`
- 新闻：`Finnhub`

之所以没有把价格也统一到 Finnhub，是因为当前免费权限下历史价格接口不稳定，项目暂时采用更稳妥的组合。

### CN 市场

- 价格：`Tushare`
- 基本面：`Tushare`
- 新闻：当前未接入

所以 A 股目前可完成真实价格和基本面分析，但新闻维度仍可能出现缺失标记。

## 系统架构

### 1. Engine 层

`engine/` 是核心分析引擎，负责真正的量化处理流程。

- `collectors/`
  - 统一封装价格、基本面、新闻采集
- `providers/`
  - 对接具体数据源，例如 `Yahoo / Finnhub / Tushare / Demo`
- `features/`
  - 把 raw data 转成技术面、估值、质量、情绪、事件等特征
- `evidence/`
  - 把 feature 转成带方向、强度、解释的 evidence
- `decision/`
  - 规则化决策引擎，输出 `buy / hold / sell`
- `risk/`
  - 风险修正与降级
- `reporting/`
  - 渲染标准报告与详细报告
- `querying/`
  - 股票名称/代码识别、缓存命中、机器人摘要格式化

### 2. App 层

`app/` 用于承接渠道和未来集成层。

- `push/`
  - 当前已实现 Telegram bot
- `api/`
  - 为未来 HTTP/API 服务预留
- `scheduler/`
  - 为未来定时任务预留
- `workers/`
  - 为未来异步执行预留

### 3. Script 层

`scripts/` 提供本地运行入口。

- `run_single.py`
  - 跑单票分析
- `query_symbol.py`
  - 做名称/代码识别与缓存复用
- `run_telegram_bot.py`
  - 启动 Telegram 机器人
- `inspect_symbol.py`
  - 查看指定标的的原始与标准化字段
- `replay_snapshot.py`
  - 回放历史快照

## 数据流

完整链路如下：

```text
用户输入股票代码/名称
  -> Symbol Resolver 识别标准代码
  -> Query Service 检查当天是否已有缓存
  -> 若无缓存则触发 run_single
  -> CompositeCollector 采集 raw data
  -> FeaturePipeline 提取 features
  -> RuleBasedEvidenceBuilder 构建 evidences
  -> RuleBasedDecisionEngine 输出 action/confidence
  -> RuleBasedRiskEngine 做风险修正
  -> ReportRenderer 输出 md/detail.md/json
  -> Telegram Bot 回传摘要与报告入口
```

## 输出产物

每次分析都会落盘，默认放在 `data/` 下：

- `data/snapshots/`
  - 中间快照
  - `raw / features / evidence / decision`
- `data/outputs/`
  - 最终输出
  - `json / md / detail.md`
- `data/logs/`
  - 简要运行日志
- `data/runtime/`
  - Telegram 会话状态、bot offset 等运行态文件

## 运行模式

### DEMO

- 使用确定性假数据
- 适合本地开发、测试和流程验证

### LIVE

- 使用真实数据源
- 适合真实分析和 Telegram 联调

系统会在 job_id、报告标题和产物文件名中区分 `DEMO / LIVE`，避免混淆。

## 缓存复用逻辑

为了节省 API 调用和提高机器人响应速度，系统支持“同一标的同一天复用结果”：

- 识别股票后先查找当天缓存
- 如果当天已经跑过，就直接返回已有结果
- 如果要求强制刷新，可使用 `/refresh SYMBOL`

## Telegram 机器人逻辑

当前 Telegram bot 已经支持真实联调，交互流程是：

1. 用户发送股票名称或代码
2. 机器人先返回识别结果
3. 用户回复 `确认`
4. 系统执行分析或复用当天缓存
5. 机器人返回可直接阅读的中文摘要
6. 用户可继续发送：
   - `/report NVDA`
   - `/detail NVDA`

机器人目前支持的指令：

- `/start`
- `/help`
- `/run SYMBOL`
- `/refresh SYMBOL`
- `/report SYMBOL`
- `/detail SYMBOL`
- `/cancel`

## 快速开始

### 1. 安装依赖

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env`，填入你的真实 key：

```env
FINNHUB_API_KEY=your_finnhub_api_key
TUSHARE_TOKEN=your_tushare_token
TUSHARE_ENABLED=false
QUANT_ENGINE_USE_DEMO_DATA=true
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
```

### 3. 本地跑单票分析

```bash
py scripts/run_single.py --symbol NVDA --market US --as-of 2026-03-31
py scripts/run_single.py --symbol 601166.SH --market CN --as-of 2026-03-27
```

### 4. 本地做识别与缓存测试

```bash
py scripts/query_symbol.py --query NVDA --as-of 2026-03-31
py scripts/query_symbol.py --query NVDA --as-of 2026-03-31 --confirm
```

### 5. 启动 Telegram bot

```bash
py scripts/run_telegram_bot.py
```

## 当前项目状态

当前仓库已经达成一个可用的第一阶段目标：

- 核心分析引擎可用
- 报告能力可用
- Telegram 联调已完成
- 真实 T-1 数据链路已验证

尚未完全完成但已规划的能力：

- 更完整的证券主数据检索
- A 股新闻源
- API 服务化
- 调度与批量任务
- OpenClaw 适配层

## 发布注意事项

以下内容默认不应上传：

- `.env`
- 本地产生的 `data/logs/`
- 本地产生的 `data/outputs/`
- 本地产生的 `data/snapshots/`
- 本地产生的 `data/runtime/`

这些都属于本地运行态或结果产物，而不是源码本身。
