# 可选AI连接

默认不调用AI，不需要配置。显式使用`--ai`后，只发送公开项目资料、商品定义及审核初筛；不要加入买家文件、聊天、密钥或订单个人信息。

## Dify工作流

在Dify创建并发布一个Workflow：

1. 开始节点定义两个字符串输入：`evidence_json`、`instructions`。
2. LLM节点的系统提示用`instructions`，用户输入用`evidence_json`。不用工具调用、代码执行或外部浏览节点。
3. 提示模型仅输出JSON对象，字段`title`、`description`、`faq`均为字符串。
4. 结束节点输出变量命名为`draft_json`，值为LLM的完整JSON文本。
5. 使用工作流应用API密钥。API根地址通常以`/v1`结束，程序追加`/workflows/run`。

Windows PowerShell示例（自行填写真实地址与密钥，不要提交到仓库）：

```powershell
$env:DIFY_BASE_URL = "http://127.0.0.1/v1"
$env:DIFY_API_KEY = "填写应用API密钥"
py run.py --workspace work-ai generate --repo pdfcpu/pdfcpu --ai dify
```

新工作目录须先运行`py run.py --workspace work-ai init`。Dify使用blocking模式，120秒超时；模型较慢时请求可能失败，程序不自动重试以避免重复计费。

对应接口依据：[Dify Workflow API实现](https://github.com/langgenius/dify/blob/main/api/controllers/service_api/app/workflow.py)。具体输入名称须与你配置的工作流一致。本系统没有运行你的真实Dify实例。

## OpenAI兼容模型接口

```powershell
$env:AI_BASE_URL = "http://127.0.0.1:8000/v1"
$env:AI_MODEL = "你的模型名称"
$env:AI_API_KEY = "按服务要求填写；本地无鉴权服务可不设置"
py run.py --workspace work-ai generate --repo pdfcpu/pdfcpu --ai compatible
```

程序请求`/chat/completions`。不依赖服务一定支持JSON模式，收到内容后严格解析字段；格式无效则报告失败。

## 输出使用

结果保存为`ai-draft.json`和`ai-draft.md`，不会替换基础商品描述或许可证结论。人工核验功能、价格、来源、兼容性和服务承诺后才使用。API密钥只读环境变量，错误日志不输出响应体。拒绝接口重定向，避免把鉴权发送到未知地址。
