# ASIN 1688 采购与 ROI 工具

[![CI](https://github.com/ianyoufather-2007/asin-1688-roi-tool/actions/workflows/ci.yml/badge.svg)](https://github.com/ianyoufather-2007/asin-1688-roi-tool/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

把 Amazon ASIN 输入、1688 候选采集、同规格核验、采购成本和 ROI 计算串成一条可追溯工作流。

> 当前状态：Alpha。适合本地研究和人工复核，不应直接替代供应商询价、Amazon 费用预览或财务审批。

## 工作流

```text
ASIN 输入
  -> 为每个 ASIN 配置 1688 中文关键词
  -> 使用本机 1688 登录 Cookie 采集候选
  -> 补齐规格和完整销售单元采购价
  -> 自动匹配 + 人工确认/驳回
  -> 从有效同规格候选中取最高采购价
  -> 计算物流、佣金、仓储、广告、毛利和 ROI
  -> 导出 Excel 结果与来源追溯
```

## 核心边界

1. 搜索页最低展示价不会自动写入正式采购价。
2. 缺少材质、结构、销售单元、套装或配件信息时，不会自动判定候选有效。
3. 缺少有效采购价、物流参数或 FBA 时，不生成伪完整 ROI。
4. 详情采集只允许打开 `https://*.1688.com`，不会绕过验证码、登录或平台风控。
5. Excel 中的外部文本按普通字符串写入，避免公式注入。
6. Cookie 只在本机使用，禁止提交到 GitHub、Issue、日志或共享文件。

## 环境要求

- Windows 10/11；CLI 也可在 Linux/macOS 使用
- Python 3.11 至 3.14
- 本机 Chrome 仅用于可选的详情页截图

## 安装

Windows 一键安装基础依赖：

```powershell
.\scripts\setup_windows.ps1
```

同时安装 Chrome 详情采集和 GUI 依赖：

```powershell
.\scripts\setup_windows.ps1 -WithBrowser
```

手动安装方式：

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e .
```

需要详情页截图或 GUI 时安装浏览器依赖：

```powershell
python -m pip install -e ".[browser]"
```

开发环境：

```powershell
python -m pip install -e ".[dev]"
```

## 准备输入

`examples/asin_input_template.xlsx` 是空白模板，不包含真实 ASIN 或业务数据。核心字段：

- `ASIN`、`售价`、`CPC`
- `Amazon商品名称`、`1688搜索关键词`
- `材质`、`功能`、`结构`、`销售单元`
- `套装数量`、`配件数量`、产品尺寸
- 包装尺寸、包装重量、`FBA`

多个搜索关键词使用 `|` 分隔。可用以下命令重新生成脱敏空白样例：

```powershell
py -m scripts.generate_examples --output-dir examples
```

## 获取 Cookie

1. 使用自己的账号登录 1688，并打开能正常显示商品的搜索页。
2. 在浏览器开发者工具的 Network 中找到成功的 `getOfferList` 请求。
3. 复制请求头中的完整 `Cookie` 值，保存为本机 `cookies.txt`。
4. 用完后妥善保管；如果泄露，立即退出相关会话并更新凭证。

项目默认忽略 `cookie*.txt`、`.env`、输出目录和日志，但提交前仍应主动检查。

## 采集候选

```powershell
run_cli.bat collect `
  --input examples/asin_input_template.xlsx `
  --cookie-file cookies.txt `
  --pages 2 `
  --page-size 30 `
  --output outputs/1688_candidates.json
```

命令同时生成 `outputs/1688_candidates.xlsx`。在候选表中人工补齐规格、完整销售单元采购价、人工判断及原因。

采集每完成一个关键词都会原子更新 `--output` JSON。后续关键词因网络、登录态或风控失败时，已完成候选仍会保留。对传输错误、HTTP 429 和 5xx 最多请求三次；认证失败和普通 4xx 不重试。

需要查看脱敏进度日志时，在命令末尾增加 `--verbose`。日志不会主动记录 Cookie 内容。

## 可选详情采集

```powershell
run_cli.bat capture-details `
  --input examples/asin_input_template.xlsx `
  --candidates outputs/1688_candidates.xlsx `
  --output-dir outputs/screenshots `
  --output outputs/enriched_candidates.xlsx
```

此步骤打开本机 Chrome，保存页面正文和截图作为辅助证据。验证码只能人工处理。

## 计算 ROI

```powershell
run_cli.bat calculate `
  --input examples/asin_input_template.xlsx `
  --candidates outputs/enriched_candidates.xlsx `
  --fx 7.10 `
  --output outputs/asin_roi_result.xlsx
```

正式复核建议明确传入 `--fx`。省略时，程序按 [Frankfurter v2 官方接口](https://frankfurter.dev/) 获取最新工作日的 USD/CNY，并在来源追溯表记录接口地址。

## 自定义 ROI 参数

以 `examples/roi_assumptions.example.json` 为模板配置实际类目费率、仓储和物流报价：

```powershell
run_cli.bat calculate `
  --input examples/asin_input_template.xlsx `
  --candidates outputs/enriched_candidates.xlsx `
  --config examples/roi_assumptions.example.json `
  --fx 7.10 `
  --output outputs/asin_roi_result.xlsx
```

支持字段：

| 字段 | 默认值 | 约束 |
|---|---:|---|
| `commission_rate` | `0.15` | 大于等于 0 且小于 1 |
| `storage_usd` | `0.10` | 大于等于 0 |
| `conversion_rate` | `0.10` | 大于 0 且小于等于 1 |
| `ad_traffic_share` | `0.20` | 0 至 1 |
| `weight_low_cny_per_kg` | `8.50` | 大于等于 0 |
| `weight_high_cny_per_kg` | `10.60` | 大于等于 0 |
| `volume_low_cny_per_cbm` | `1360` | 大于等于 0 |
| `volume_high_cny_per_cbm` | `1900` | 大于等于 0 |

配置允许只覆盖部分字段；未知字段、布尔值、非有限数值和越界值会被拒绝。每次导出的 `ROI结果`、`来源追溯` 和 `参数说明` 都会记录配置来源和完整快照。

## 当前计算口径

- Amazon 佣金：售价人民币 x 15%
- 仓储：`$0.10/件 x USD/CNY`
- 广告：`CPC x 广告流量占比 20% / 转化率 10% x USD/CNY`
- 物流：`重量 x 8.5`、`体积 x 1360`、`重量 x 10.6`、`体积 x 1900` 四项取最大值
- ROI：`推测真实毛利 / (采购成本 + 物流成本)`

这些是项目默认预设，不代表所有 Amazon 类目、尺寸段、仓储周期或物流报价。可用 `--config` 覆盖，但商用决策前仍必须对照实际费用和报价。

## 输出

- `ROI结果`：单个 ASIN 的成本、毛利、ROI 和完整性状态
- `1688候选`：候选商品、规格、人工判断和原始证据
- `ASIN输入`：本次计算使用的输入快照
- `来源追溯`：售价、CPC、汇率、采购价、物流和 FBA 来源
- `参数说明`：本次实际参数来源、快照、公式和安全边界

## GUI

安装浏览器依赖后双击 `run_gui.bat`。界面可选择 ROI 参数 JSON；耗时任务在后台执行，标准输出和错误会显示在窗口日志中。

## 验证

```powershell
python -m ruff check .
python -m ruff format --check .
python -m pytest -q
```

CI 覆盖 Python 3.11 至 3.14，并额外在 Windows Python 3.12 验证。网络接口使用离线 Mock 测试，CI 不携带真实 Cookie，也不访问 1688。

## 文档

- [架构与职责](docs/architecture.md)
- [数据字典](docs/data_dictionary.md)
- [MVP 路线图](docs/roadmap.md)
- [发布检查清单](docs/release_checklist.md)
- [贡献指南](CONTRIBUTING.md)
- [安全政策](SECURITY.md)

## 上游与许可证

MTop 签名和 1688 搜索实现衍生自 [FengYing1314/crawler-1688](https://github.com/FengYing1314/crawler-1688)。上游和本项目均采用 MIT License；完整署名见 `LICENSE` 与 `THIRD_PARTY_NOTICES.md`。
