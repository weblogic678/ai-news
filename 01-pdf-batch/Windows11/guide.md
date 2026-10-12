# PDF批处理助手：中文使用材料（草稿）

上游项目：pdfcpu/pdfcpu
固定版本：v0.16.1
固定提交：2f7a89a0a69c117a5252601907ff9f31ac4c70f2
免费获取：https://github.com/pdfcpu/pdfcpu

## 安装准备

1. 安装Python 3.10或以上版本。Windows可先运行 `py --version`。
2. 从上述官方仓库发行页下载适合操作系统的pdfcpu。不要使用未知来源的安装程序。
3. 解压后运行 `pdfcpu version`；不在PATH时，用脚本的 `--pdfcpu` 参数指定完整路径。
4. 首次使用先处理随包样例，输出到新的目录。

## Windows PowerShell示例

以下命令在本教程目录运行。Windows 11 x64 基本合并、拆分、优化及一键样例已实测；买家目标环境仍需复测。

```powershell
py pdf_batch.py merge samples output\merged.pdf --pdfcpu "C:\tools\pdfcpu\pdfcpu.exe"
py pdf_batch.py split samples output\split --pdfcpu "C:\tools\pdfcpu\pdfcpu.exe"
py pdf_batch.py optimize samples output\optimized --pdfcpu "C:\tools\pdfcpu\pdfcpu.exe"
```

## Linux / WSL示例

```bash
python3 pdf_batch.py merge samples output/merged.pdf --pdfcpu /path/to/pdfcpu
python3 pdf_batch.py split samples output/split --pdfcpu /path/to/pdfcpu
python3 pdf_batch.py optimize samples output/optimized --pdfcpu /path/to/pdfcpu
```

脚本按文件名排序，建议文件用01、02等前缀。只处理当前目录的.pdf文件，不递归。已存在的输出位置会被拒绝，避免覆盖。单文件首期限制200MB。出错时可能留下部分输出，应查看日志后使用新输出路径重试。

## 验收

- 合并：两个一页样例合并后共两页，顺序与文件名一致。
- 拆分：样例应各得到一个独立页面；实际多页文件逐页核对。
- 优化：输出通过pdfcpu validate，页面数不变；不保证文件体积减小。
- 原文件：处理前后校验值相同。

## 不支持

OCR、密码破解、去水印不属于本商品。加密或签名标记会被保守拦截，但这不是完整签名鉴定；不要用此脚本处理合同签名原件。

## 收费与交付说明

原项目免费。本包提供自编材料，未附上游安装程序、模型或付费账号；请从官方渠道安装。Linux基础功能已测；Windows、macOS及买家实际环境需要复测。

## 数据与售后

先用样例或文件副本验证，再处理自己的文件。不要把买家文件、密码或访问令牌上传给AI。售后按商品约定的环境、次数和时间提供，不承诺无限支持。
