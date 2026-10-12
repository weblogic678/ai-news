# 本机离线验收记录

日期：2026-10-12。本机 Windows 11 专业版 64 位（10.0.28000）。目录：D:\demo_xianyu。目标仓库：weblogic678/ai-news。

| 项目 | 已验证内容 |
| --- | --- |
| Dify 1.17.1 | 固定摘要的 12 个 amd64 镜像离线加载；独立 WSL/Engine 部署；管理员登录和 CSRF；两个草稿导入且重复导入不重复创建；中文模板工作流三步运行成功，模型用量 0；停机归档恢复后原账号与工作流保留，运行再次成功；另在新 PostgreSQL 数据目录独立恢复，应用、账号和运行记录核对通过 |
| n8n 2.42.6 | 固定镜像离线加载；独立 WSL/Engine 部署；两个流程导入且重复导入不重复创建；CLI 与浏览器执行中文无模型流程；停机备份恢复到新的独立数据卷后，原流程 ID 保留且示例再次运行成功 |
| Flowise 2.2.8 | 官方社区镜像实际版本 2.2.8，未包含 enterprise 目录；独立 WSL/Engine 离线部署；未认证 API 返回 401，认证后流程保存/读取/导出通过；真实 Custom JS Function 流程返回准确中文结果；停机备份恢复到新的独立数据卷后，原流程 ID、代码与账号保留，读取后直接运行再次通过（未重建流程） |
| 回归 | 29 项 Python 自动检查通过；Windows WSL 前置依赖另有三项隔离分支检查及真实已就绪分支运行通过，包括重复准备保留密钥与数据、错误版本/架构拒绝安装、镜像完整性、Docker 项目归属和发布目录结构 |
| 压缩包审计 | 六套 ZIP/GZ 离线包的分包校验、组合 TAR 内容检查通过；镜像、Docker Engine 29.9.0、Compose 5.6.0、Python 3.14.8、离线网络库与许可证齐全；Windows 另含 Debian 根文件系统和 WSL 3.0.1 MSI |

Windows 安装入口在本机执行；Linux 分包入口在本机 WSL2 验证，独立 Linux 实机未验收。没有做干净 Windows 硬件上的 BIOS/系统功能启用验收。真实 DeepSeek/其他模型调用按用户要求跳过，不宣称模型推理完成。

离线范围为软件安装与基础运行环境；模型权重、云 API 和第三方插件不包含在交付中。独立 Engine 不修改系统防火墙，联网功能须另外配置。

Flowise 3.1.4 因其镜像包含受商业许可限制的 enterprise 内容，已从公开交付中移除，替换为 Apache 2.0 社区版 2.2.8。Docker Desktop 安装包仅保留本机，公开包使用 Moby/Docker Engine。

账号、密码、原运行卷、恢复测试卷和备份均保留在本机私有目录或独立 WSL 的私有 Docker 存储；没有放进交付压缩包。旧 3.1.4 测试 WSL 已完整导出并校验到 temp/private，旧发布目录已移入 temp。

## 真实页面截图

- [Dify 中文运行](screenshots/dify-offline-smoke.png)
- [n8n 无模型流程运行](screenshots/n8n-offline-smoke.png)
- [Flowise 恢复后的流程](screenshots/flowise-offline-restored.png)

咸鱼封面独立放在 `发布版/images`，每个项目仅一张。发行分包完整性清单见 `RELEASE-PACKAGE-MANIFEST.json`。
