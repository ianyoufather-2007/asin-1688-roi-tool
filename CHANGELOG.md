# 更新记录

## 未发布

- 增加可选 ROI 参数 JSON、严格范围校验、配置来源和参数快照。
- 为汇率与 MTop 请求增加有限重试，为关键词采集增加原子检查点。
- CLI 增加 `--config`、`--verbose` 和可操作错误提示，GUI 支持选择参数 JSON。
- CI 仅在 `main` 推送和 PR 上执行，并取消同一 PR 的旧任务。
- 增加 Windows 一键安装脚本和发布检查清单。

## 0.1.0

- 建立 ASIN 输入、1688 候选采集、详情证据、规格匹配、ROI 和 Excel 追溯闭环。
- 增加 Cookie 校验、MTop 离线测试、搜索分页校验和跨关键词候选去重。
- 修复 TSV 读取、三维尺寸错配、非有限数值和负采购价问题。
- 阻止 Excel 公式注入和非 1688 HTTPS 详情页导航。
- 迁移至 Frankfurter v2 USD/CNY 接口并记录汇率来源。
- 增加 Windows GUI 日志捕获、CI、Dependabot、安全政策和中文维护文档。
- 将公开样例改为空白脱敏模板，不再包含真实业务 ASIN。
