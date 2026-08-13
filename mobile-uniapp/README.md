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

## 从 HBuilderX 打包 Android APK

1. 在 HBuilderX 中直接打开 `mobile-uniapp` 目录。
2. 打开 `src/manifest.json`，点击“重新获取”申请 DCloud AppID。
3. 在“安卓/iOS 图标配置”和“安卓/iOS 模块配置”中按需补充图标、包名和权限。
4. 确认 `.env.local` 的 `VITE_API_BASE` 是手机能够访问的地址。
5. 先启动项目根目录的 `start.bat`，再用手机浏览器访问 `http://电脑局域网IP:8000/docs` 验证网络。
6. 在 HBuilderX 选择“发行 → 原生 App-云打包”。
7. 选择 Android；测试安装可选公共测试证书，正式发布请选择自有证书并妥善备份。
8. 提交打包，等待任务完成后下载 APK，传到手机安装。

打包生成的 APK 已包含构建时的 API 地址。修改 `.env.local` 后必须重新打包，旧 APK 不会自动更新地址。

## 登录失败排查

按以下顺序检查：

1. 确认输入的是注册邮箱（例如 `1114857160@qq.com`），不是用户名。
2. 手机和电脑连接同一个 Wi-Fi，暂时关闭手机流量切换和 VPN。
3. 在电脑执行 `ipconfig`，确认 `.env.local` 使用当前无线网卡的 IPv4 地址。
4. 手机浏览器访问 `http://电脑IP:8000/docs`。打不开通常是后端只监听了 `127.0.0.1`，或 Windows 防火墙拦截了 8000 端口。
5. 后端应使用 `python run_server.py --host 0.0.0.0 --reload` 启动；根目录 `start.bat` 已使用这一配置。
6. 浏览器能打开文档但 App 仍失败时，强制停止 App 后重新打开；如果刚修改过 API 地址，则重新打包并安装。

## Java 内存不足

出现以下信息时，并不是项目代码错误，而是 Windows 可用内存或分页文件不足：

```text
There is insufficient memory for the Java Runtime Environment
Native memory allocation (mmap) failed
DOS error/errno=1455
```

关闭浏览器、模拟器等占用内存的软件。在“高级系统设置 → 性能设置 → 高级 → 虚拟内存”中勾选“自动管理所有驱动器的分页文件大小”，或为磁盘设置足够的系统管理分页文件；应用设置并重启电脑后重新云打包。
