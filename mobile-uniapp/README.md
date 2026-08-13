# 一念 AI uni-app 移动端

这是与 `frontend` 并列的独立 Vue 3/Vite uni-app 工程。它复用根目录 FastAPI、数据库和登录账号，不是网页 WebView 套壳。

当前已接入：

- 登录、Token 自动刷新、退出登录
- 移动首页、服务中心、用户资料和管理员角色展示
- 专属知识库：资料列表、H5 上传、重新处理、删除；App 的 PDF/TXT 系统选择需后续配置原生文件选择插件
- 我的任务：状态、进度、错误、重试和自动刷新
- 专家服务：套餐、入驻状态、入驻申请、精批订单
- 开放平台：开发者开户注册、套餐、额度和调用统计

## HBuilderX 打开

在 HBuilderX 选择“文件 → 打开目录”，打开本目录：

```text
D:\Code\1\ai_name\mobile-uniapp
```

先在终端安装依赖：

```powershell
cd D:\Code\1\ai_name\mobile-uniapp
npm install
```

然后可使用 HBuilderX 的“运行”菜单运行到浏览器、Android 基座或小程序工具。

## 命令行运行 H5

先从项目根目录运行 `start.bat`，再运行：

```powershell
cd D:\Code\1\ai_name\mobile-uniapp
npm run dev:h5
```

默认地址为 `http://电脑局域网IP:5174`。H5 开发通过 `/api` 代理连接本机 8000 后端。

命令行编译 App 或微信小程序：

```powershell
npm run build:app
npm run build:mp-weixin
```

## Android/iOS 真机 API

复制 `.env.example` 为 `.env.local`，把地址改成手机能访问的后端：

```env
VITE_API_BASE=http://192.168.31.211:8000
```

本地真机必须与电脑处于同一 Wi-Fi；根目录 `start.bat` 已将 FastAPI 监听地址调整为 `0.0.0.0`。正式发布必须换成部署后的 HTTPS API 域名，不能使用局域网 IP。

云打包前需要在 HBuilderX 打开 `src/manifest.json`，申请并填写 DCloud AppID、应用图标、Android 包名或 iOS Bundle ID 和签名证书。
