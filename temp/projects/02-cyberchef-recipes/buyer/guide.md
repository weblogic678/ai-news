# CyberChef中文配方教程

## 免费工具来源

上游项目：https://github.com/gchq/CyberChef 。主许可证Apache-2.0。本包仅包含原创配方、教程及演示，不含上游程序或账号。

## 已验证环境

CyberChef v11.5.0本地官方发行版、桌面Chromium、2026-10-11。测试时阻断所有外网请求，三项配方仍得到预期输出。其他浏览器、手机与上游版本需复测。

## 安装与导入

1. 从官方发行页获取CyberChef，解压后按官方方法本地打开。
2. 点击Recipe区域的文件夹图标（Load recipe）。
3. 用文本编辑器打开recipes中的JSON，把完整内容粘贴到加载窗口。
4. 点击LOAD，关闭加载窗口后在Input输入样例。
5. 启用Auto Bake，或点击BAKE；核对Output。

|配方|输入|预期输出|
|---|---|---|
|01-to-base64.json|Hello|SGVsbG8=|
|02-from-base64.json|SGVsbG8=|Hello|
|03-url-decode.json|hello%20world|hello world|

这些文件是可以免费自行编写的配方。收费价值为中文场景整理、按约定交付及答疑，不是购买软件独家授权。只处理合法且有权使用的数据，不提供破解或绕过权限服务。
