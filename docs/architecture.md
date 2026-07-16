# 架构与职责

## 分层

| 模块 | 职责 | 不负责 |
|---|---|---|
| `input_io.py` | 读取 XLSX/CSV/TSV，统一字段并校验 ASIN 和核心数值 | 推断缺失业务数据 |
| `mtop.py` | Cookie 解析、签名、JSONP、鉴权状态和 HTTP 请求 | 绕过登录或风控 |
| `search.py` | 构造 1688 搜索请求并转为候选对象 | 把搜索页价格当正式采购价 |
| `detail_browser.py` | 打开允许的 1688 HTTPS 页面，保存正文和截图 | 自动确认阶梯价或验证码 |
| `matcher.py` | 按材质、尺寸、功能、结构和销售单元评分 | 替代人工确认缺失规格 |
| `roi.py` | 汇率、物流、成本、毛利和 ROI 计算 | 获取 Amazon 实时费用 |
| `exporter.py` | 输出结果、输入快照、来源追溯和参数说明 | 修改原始输入文件 |
| `workflow.py` | 编排采集和计算流程 | 承担模块内部解析逻辑 |
| `cli.py` / `gui.py` | 参数入口、错误呈现和桌面交互 | 保存或上传凭证 |

## 数据流

```text
输入文件 -> TargetProduct
Cookie -> MTopClient -> 1688 搜索 -> CandidateProduct
CandidateProduct -> 详情证据/人工补充 -> 匹配状态
TargetProduct + 有效 CandidateProduct + 汇率 -> RoiResult
全部对象 -> Excel 工作簿
```

## 信任边界

- 用户输入、1688 文本和链接均视为不可信数据。
- Cookie 只进入内存中的 HTTP Cookie Jar，不写入输出。
- 详情浏览器只接受 `https://1688.com` 或其子域。
- 搜索页价格只保留为展示证据，正式采购价必须另行确认。
- 缺失核心成本时，结果保持不完整状态，不用默认值掩盖缺口。

## 测试边界

单元测试使用 `httpx.MockTransport` 模拟 MTop 和汇率响应；CI 不访问真实 1688，不使用真实 Cookie。浏览器登录态和页面结构仍需本机人工验收。
