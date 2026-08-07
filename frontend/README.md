# 一念 AI 前端

基于 React + Vite 的单页应用，对接项目根目录中的 FastAPI 后端。

环境要求：Node.js 20.19+ 与 npm。

## 本地启动

先在项目根目录启动后端：

```powershell
uvicorn main:app --reload
```

然后新开终端启动前端：

```powershell
cd frontend
npm install
npm run dev
```

浏览器访问 `http://127.0.0.1:5173`。开发服务器会把 `/api/*` 代理到
`http://127.0.0.1:8000/*`，把 `/static/*` 代理到后端静态目录，因此本地开发
无需修改 FastAPI 的 CORS 配置。

## 环境配置

默认接口前缀为 `/api`。如果前后端分别部署，请创建 `.env.local`：

```env
VITE_API_BASE=https://api.example.com
```

此时后端还需要允许前端站点的 CORS Origin。若由 Nginx 将 `/api` 反向代理到
FastAPI，则建议继续保留默认配置。

## 生产构建

```powershell
npm run build
```

构建产物位于 `frontend/dist/`。

## 已接入功能

- 邮箱验证码、注册、登录与退出
- Access Token 过期后自动使用 Refresh Token 刷新
- 人名、企业名、宠物名生成及同一会话连续微调
- 起名次数余额展示与生成后自动刷新
- TXT/PDF 专属知识库上传
- 企业 Logo 生成与原图查看
- 套餐查询、创建订单并跳转支付宝收银台
- 桌面端与移动端响应式布局
