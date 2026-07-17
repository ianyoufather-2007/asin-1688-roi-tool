# 仓库第二轮优化实施计划

> **执行要求：** 使用测试驱动方式逐项实施；每个行为先写失败测试，再做最小实现并运行相关测试。

**目标：** 为现有工具增加可复现 ROI 配置、网络恢复、采集检查点，并优化 CI、安装和仓库维护。

**架构：** 新增独立的 ROI 配置与 HTTP 重试模块，现有 ROI、MTop、工作流和导出模块仅通过明确接口消费。CLI 负责编排文件配置与日志，业务模块不读取命令行状态。

**技术栈：** Python 3.11-3.14、dataclasses、JSON、httpx、pytest、Ruff、GitHub Actions、PowerShell。

## 全局约束

- 保持现有默认计算结果兼容。
- 所有配置值必须经过有限数值和业务范围校验。
- Cookie 不进入日志、输出、测试快照或 GitHub。
- MVP 不引入数据库、服务端或新的运行时依赖。
- 不合并 `main`。

---

### 任务 1：可复现 ROI 参数

**文件：**

- 新建：`src/asin_1688_roi/roi_config.py`
- 新建：`examples/roi_assumptions.example.json`
- 修改：`src/asin_1688_roi/roi.py`
- 修改：`src/asin_1688_roi/models.py`
- 修改：`src/asin_1688_roi/exporter.py`
- 修改：`src/asin_1688_roi/cli.py`
- 修改：`src/asin_1688_roi/workflow.py`
- 测试：`tests/test_roi_config.py`、`tests/test_roi.py`、`tests/test_exporter.py`

**接口：**

- `RoiAssumptions`：保存并校验八项 ROI 与物流参数。
- `load_roi_assumptions(path)`：返回参数对象和来源字符串。
- `calculate_results(..., assumptions, assumptions_source)`：使用参数并记录快照。

- [x] 写配置默认值、覆盖和无效输入的失败测试。
- [x] 运行目标测试并确认因模块或接口缺失而失败。
- [x] 实现配置对象和 JSON 加载。
- [x] 写 ROI 自定义参数与追溯输出的失败测试。
- [x] 接入 ROI、CLI、工作流和 Excel。
- [x] 运行相关测试直至通过。

### 任务 2：网络重试与采集检查点

**文件：**

- 新建：`src/asin_1688_roi/http_retry.py`
- 修改：`src/asin_1688_roi/roi.py`
- 修改：`src/asin_1688_roi/mtop.py`
- 修改：`src/asin_1688_roi/workflow.py`
- 修改：`src/asin_1688_roi/cli.py`
- 测试：`tests/test_http_retry.py`、`tests/test_roi.py`、`tests/test_mtop.py`、`tests/test_workflow.py`

**接口：**

- `RetryPolicy(max_attempts=3, backoff_seconds=0.5)`：有限重试策略。
- `request_with_retry(operation, policy, sleep, on_retry)`：仅重试传输错误、429 和 5xx。
- `collect(..., checkpoint_path)`：每个关键词完成后保存候选检查点。

- [x] 写重试成功、上限和不重试 4xx 的失败测试。
- [x] 实现通用重试并接入汇率与 MTop。
- [x] 写采集中途失败仍保留检查点的失败测试。
- [x] 实现检查点并确保 Cookie 不落盘。
- [x] 运行相关测试直至通过。

### 任务 3：CLI、CI、安装与文档

**文件：**

- 修改：`src/asin_1688_roi/cli.py`
- 修改：`.github/workflows/ci.yml`
- 新建：`scripts/setup_windows.ps1`
- 新建：`docs/release_checklist.md`
- 修改：`README.md`、`docs/architecture.md`、`docs/data_dictionary.md`、`CHANGELOG.md`
- 测试：`tests/test_cli.py`

**接口：**

- `--config`：为 `calculate` 选择 JSON 参数文件。
- `--verbose`：启用不含凭证的运行进度日志。
- CLI 错误 JSON：包含 `error`、`message` 和 `hint`。

- [x] 写 CLI 参数和错误提示的失败测试。
- [x] 实现日志、提示和检查点编排。
- [x] 限制 CI push 为 `main`，增加并发取消。
- [x] 增加 Windows 安装脚本、参数文档和发布清单。
- [x] 校验 Markdown 链接、YAML 结构和脚本语法。

### 任务 4：验证与 GitHub 更新

**文件：** 不新增生产文件。

- [x] 运行 `py -m pytest -q`。
- [x] 运行 `py -m ruff check .` 和 `py -m ruff format --check .`。
- [x] 隔离构建 sdist 和 wheel，并检查包内容。
- [x] 扫描个人标识、Cookie、Token 和真实 ASIN。
- [x] 提交并推送 `agent/initial-release`。
- [x] 更新 GitHub 仓库简介和 Topics。
- [x] 等待草稿 PR 的全部 CI 结果，不合并 PR。
