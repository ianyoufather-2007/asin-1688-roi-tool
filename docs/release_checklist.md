# 发布检查清单

## 代码与版本

- [ ] `pyproject.toml` 版本号与发布标签一致。
- [ ] `CHANGELOG.md` 已记录本次用户可见变化。
- [ ] `LICENSE` 与 `THIRD_PARTY_NOTICES.md` 署名完整。
- [ ] 草稿 PR 已完成审查，未直接向 `main` 推送功能提交。

## 验证

- [ ] `python -m pytest -q` 全部通过。
- [ ] `python -m ruff check .` 全部通过。
- [ ] `python -m ruff format --check .` 全部通过。
- [ ] `python -m build` 成功生成 sdist 和 wheel。
- [ ] GitHub Actions 的 Linux、Windows 和打包任务全部通过。

## 数据与安全

- [ ] 仓库不包含真实 ASIN、Cookie、Token、邮箱、个人路径或业务输出。
- [ ] 示例 Excel、CSV 和 JSON 只包含空白或合成数据。
- [ ] 日志和错误示例不包含 Cookie 请求头。
- [ ] `.gitignore` 继续忽略 Cookie、输出、日志、缓存和构建产物。

## 产品边界

- [ ] README 明确 Alpha/MVP 状态和人工复核要求。
- [ ] 默认 ROI 参数与示例 JSON 一致。
- [ ] 自定义参数已记录来源和快照。
- [ ] 没有把搜索页最低价当作正式采购价。
- [ ] 没有绕过 1688 登录、验证码或平台风控。

## GitHub 发布

- [ ] 仓库简介、Topics 和 README 徽章有效。
- [ ] 合并 PR 后重新确认默认分支 CI。
- [ ] 创建签名或可追溯标签，例如 `v0.1.0`。
- [ ] GitHub Release 说明包含变化、验证结果、已知限制和升级方法。
- [ ] 发布后从干净目录执行一次安装与 `--help` 冒烟测试。
