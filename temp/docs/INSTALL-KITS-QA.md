# AI 安装包验证记录

核验日期：2026-10-11。不是实机部署报告。

- 原自动化项目回归 21 项通过（含自定义/混合许可的拒绝规则）；安装辅助脚本数据保留、安全解包、版本保护、架构保护等 8 项通过。
- 官方 Docker Compose v5.6.0 在 Linux x86_64 上解析 4 项目 × 2 平台配置，8 份均通过；检查端口只绑定本机、Dify 沙箱与插件认证密钥成对一致、Redis/Celery 密码一致、AnythingLLM 配置文件持久化。配置检查不启动容器，不能证明服务健康。
- 8 份 install.sh/setup-linux.sh 的 Bash 语法检查通过；Windows PowerShell、CMD 与系统包安装流程未在实机执行。
- Dify DSL 使用固定版本源码常量 0.7.0；创建无费用模板验收流程和 DeepSeek 摘要流程，n8n 有手动验收与 DeepSeek HTTP Request 流程。8 份图结构/变量引用与 n8n JSON 表达式已检查，真实产品导入/执行未验收；不带 API Key，模型凭据由本人配置。
- 8 份 ZIP、4 份 tar.gz 及 Dify 上游 Docker 配置 ZIP 已校验 SHA256；ZIP 内容能读取，不带 runtime、账号、模型或容器镜像。Linux tar.gz 路径为相对路径。
- 镜像 Registry 元数据核验：默认启用的 15 个镜像均取得 digest（均存在 Linux amd64）并锁定；Dify 的 Weaviate 官方 Registry 返回 429，因此启用官方 Compose 支持的 Qdrant profile。未启用的其他 profile 不在本镜像锁定范围内。Registry 可访问不是镜像启动测试。
- Browser 插件不可用，以 Playwright + 官方 Chrome for Testing Chromium 151 捕获自编内容页：4 项目各 2 图，页面无运行异常、28 个下载链接均可访问。图上明确写出“不是产品运行截图”与“待实机验收”；不冒充上游应用 UI。当前只检查 1080px 桌面内容图，未检查移动页面体验。

实际无法完成的检查：Docker daemon 启动、Windows11 真机、Dify/n8n 真实导入、DeepSeek 付费请求、冷热启停、数据库恢复、完整依赖许可与闲鱼卖家类目准入。制作环境 CapEff=0、无 Docker/Powershell，无法在这里启动 Docker Engine；未取得用户的产品实例地址或模型 Key。

**新 AI 项目暂标 DO-NOT-LIST，完成真实验收及平台类目核查后再发布。** 第一批 PDF/CyberChef/Excalidraw 的真实功能记录与截图另见 QA.md。

证据：install-kit-config-qa.json、install-kit-preview-qa.json、CONTAINER-IMAGE-LOCK.json、workflow-material-qa.json、各平台 SHA256SUMS.txt、SOURCE.json、许可证正文。可执行 `python3 -m unittest discover -s tests -v` 和 `python3 -m unittest discover -s automation/tests -v`；包更新后用 tools/repackage-install-kits.py 重建。

后续若要更多浏览器交互验证，可连接 Browser 插件。无需为了本轮内容截图建立账号或共享登录凭据。

## 工作流导入辅助更新

新增 Dify/n8n 两平台 `import-demo.py` 与启动入口。模拟服务的 6 项失败/重复导入测试通过：仅回环地址、Dify 超时后拒绝重复创建、完成记录只读取、并发锁、n8n 验证失败仍恢复服务并保留不确定记录、超时仅清理本次随机 helper。合计安装及导入保护测试 14 项。此项不等于真实产品导入验收，也未执行付费模型。

新增只读 `verify-local.py`：检查 daemon、Compose 预期服务完整性（Dify 权限初始化容器允许成功退出）、容器状态与回环首页。4 项模拟检查通过，合计保护测试 18 项。报告始终不授予上架资格，不触发登录/工作流/模型请求；实机报告需在自己的测试主机生成。

本机 HTTP 测试服务进一步验证 Dify 登录密码的 Base64 编码、CSRF 会话及登出清理；模拟 n8n 验证重复调用仅复查、不再次导入。新增 2 项通过，保护测试总计 20 项，仍不代表真实上游实例验收。
