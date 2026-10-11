# GitHub → 闲鱼手动上架准备系统

Python 3.10+，核心功能只依赖标准库。不会登录闲鱼、抓取闲鱼数据、发布商品或自动联系买家。

## 已实现

- GitHub只读采集与搜索：固定发行版本/提交，记录根目录许可证正文及文件清单。
- 许可证证据初筛：缺失、识别冲突、清单截断等情况阻止发布版导出；不会把主许可判断当作完整商业授权。
- 商品生产：中文教程、文案、FAQ、SVG示意主图、逐项审核表。
- PDF批处理原创脚本：合并、拆分、优化；不覆盖现有输出，不修改输入，拒绝常见加密/签名标记。
- AI可选接口：Dify工作流或OpenAI兼容接口。默认关闭，输出单独保存为待审核草稿。
- ZIP导出：默认草稿；发布版需要审核人与逐项证据，源版本或文件变化使审核失效。
- CSV贡献利润统计：不连接平台订单。

## Windows快速开始

解压/克隆仓库后进入automation目录，安装Python 3.10或以上版本。双击`start-windows.cmd`打开初筛报告，或在PowerShell运行：

```powershell
py run.py init
py run.py audit
py run.py report
py run.py generate --repo pdfcpu/pdfcpu
py run.py export --repo pdfcpu/pdfcpu
```

Linux / WSL把`py`替换为`python3`，或执行`bash start-linux.sh`。

可选PNG生成（依赖Pillow；核心流程不需要）：

```powershell
py -m pip install Pillow
py run.py render-images --repo pdfcpu/pdfcpu --font C:/Windows/Fonts/msyh.ttc
```

生成3张1080像素的商品说明图，带草稿标识。实测截图需另行补充；说明图不会冒充软件界面。新增或修改图片后要重新生成待填写审核表。

首次生成目录：`work/bundles/pdfcpu__pdfcpu/`；导出文件：`work/exports/pdfcpu__pdfcpu-draft.zip`。
重复生成不会覆盖人工修改。需要新一批时用新的`--workspace`，或执行批处理。

## 一条命令生成整批草稿

```powershell
py daily.py
```

默认离线使用随附的5份真实来源快照。每批输出到`runs/时间戳/`，包含5个商品草稿ZIP与报告。

```powershell
py daily.py --live
py daily.py --live --ai dify
```

`--live`会更新GitHub。访问失败时明确失败，不把旧快照描述成最新。GitHub限流会停止对应请求；可在环境变量中提供最小权限`GITHUB_TOKEN`，不要写入代码。

## 扩展选品

```powershell
py run.py discover --query "topic:pdf license:apache-2.0 archived:false"
py run.py sync --repo owner/name
py run.py audit --repo owner/name
py run.py generate --repo owner/name
```

未知候选默认得分0、商品内容待定义，不能只靠Star数自动批准销售。候选目录、试验价格和主观评分在`src/g2x/catalog.py`。

## 发布版导出

1. 编辑文案，完成目标系统功能验证，补真实截图。
2. 逐项核对许可、交付范围、依赖素材、平台类目、售后承诺与AI内容。
3. 编辑完成后运行：

```powershell
py run.py prepare-review --repo pdfcpu/pdfcpu
```

4. 复制`review-template.json`为`review.json`。每项填写实际证据、审核人、带时区批准时间，确实完成后才设`approved=true`。日期格式示例`2026-10-11T13:00:00+08:00`，不能填未来时间。
5. 运行：

```powershell
py run.py export --repo pdfcpu/pdfcpu --release --review work/bundles/pdfcpu__pdfcpu/review.json
```

这是卖家自审记录，不是法律认证或闲鱼准入保证。系统不会替你勾选检查项。首期只支持自编材料交付；要重新分发上游程序、依赖、素材或模型，须扩展对应审核流程。

仓库`projects/`中的人工整理成果独立于`work/`，不要用自动生成结果覆盖它们。若调整项目成果，应同步更新项目证据和审核表。

## AI设置

见`docs/AI-SETUP.md`。没有API密钥仍可完整运行模板模式。已实现请求格式与输出校验，未使用你的真实模型服务做联网验证。

## 收益统计

```powershell
py run.py metrics --csv examples/orders.csv
```

CSV示例为虚构订单，仅演示49元收入减去成本后贡献利润22元的计算。不是实际销售证据。

## 验证与限制

```powershell
py -m unittest discover -s tests -v
```

核心回归覆盖许可缺失/冲突、审核失效、草稿导出、路径与符号链接保护、AI输出格式、输入文件保护和命令参数安全。PDF真实工具测试记录见`docs/pdf-functional-test.json`。

仅完成Linux环境运行验证；Windows启动脚本和PDF包装器仍需实机验证。自动扫描不包含完整依赖解析、漏洞扫描或人工法律审查。系统不会执行GitHub项目中的安装脚本。
