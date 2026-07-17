# 贡献指南

## 适合贡献的范围

- 输入校验、候选去重、匹配准确性和来源追溯
- ROI 参数化、费用模型和缺失数据提示
- 1688 接口兼容性、离线测试和错误处理
- Windows GUI、打包、文档和无障碍改进

验证码绕过、凭证收集、伪造数据或削弱人工确认边界的变更不在项目范围内。

## 本地开发

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
```

## 提交要求

1. 行为修改先添加能复现问题的失败测试，再做最小修复。
2. 不提交真实 Cookie、ASIN 清单、供应商报价、联系方式或本机绝对路径。
3. 新增计算口径时，说明公式、单位、默认值、数据来源和缺失值行为。
4. 修改 MTop 或搜索实现时，保留上游 MIT 署名并使用离线 Mock 测试。
5. Pull Request 保持单一目的，列出验证命令、已知风险和人工确认点。

## 报告问题

使用 Issue 模板提交最小复现。日志必须脱敏；安全问题按 `SECURITY.md` 私密报告。
