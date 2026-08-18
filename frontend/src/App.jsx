import { useEffect, useMemo, useState } from 'react'
import {
  ArrowRight, BarChart3, BookOpen, Building2, Camera, Check, ChevronRight, CircleUserRound,
  Archive, ArchiveRestore, Coins, Crown, Dog, Download, Feather, FileText,
  FolderKanban, Gem, Heart, Image, KeyRound, LoaderCircle, LogOut, Menu,
  MessageCircleMore, Monitor, MoonStar, Palette, Pencil, RefreshCw, Send,
  ShieldCheck, Sparkles, Star, UploadCloud, UserRound, Users, Vote, Flag,
  WandSparkles, X, Zap,
} from 'lucide-react'
import { api, resolveAssetUrl } from './api'
import { getPrimaryDashboardAction, USER_CENTER_MODULES } from './dashboard'
import { categoryFromPreset, normalizeCreatePreset, parseHash } from './route'
import { hasPermission, operationsRoute } from './access'

const navItems = [
  ['home', '首页'], ['create', '智能起名'], ['knowledge', '专属知识库'],
  ['logo', '品牌 Logo'], ['validation', '名称校验'], ['brand-assets', '品牌资产'], ['reports', '命名报告'], ['experts', '专家服务'], ['community', '社区投票'], ['developers', '开放平台'], ['growth', '邀请有礼'], ['projects', '我的项目'], ['orders', '我的订单'], ['tasks', '我的任务'], ['credits', '我的次数'], ['pricing', '套餐'], ['account', '用户中心'],
]

function Toast({ toast, close }) {
  if (!toast) return null
  return <div className={`toast ${toast.type || ''}`}><span>{toast.message}</span><button onClick={close}><X size={16}/></button></div>
}

function PageLoadError({ title = '页面暂时没有加载成功', message, retry, go }) {
  return <main className="page-shell wrap narrow"><div className="empty-state standalone"><Flag/><h3>{title}</h3><p>{message || '请检查服务状态后重试。'}</p><div className="order-actions">{retry && <button className="red-button" onClick={retry}>重新加载</button>}{go && <button className="outline-button" onClick={() => go('home')}>返回首页</button>}</div></div></main>
}

function AccessDeniedPage({ area, go }) {
  return <main className="page-shell wrap narrow"><div className="empty-state standalone"><ShieldCheck/><h3>当前账号没有{area}权限</h3><p>这不是页面加载失败。请使用具备对应角色或权限的账号重新登录；角色变更后旧登录会话会自动失效。</p><div className="order-actions"><button className="red-button" onClick={() => go('account')}>查看当前账号</button><button className="outline-button" onClick={() => go('home')}>返回首页</button></div></div></main>
}

function Header({ page, go, session, balance, openAuth, logout }) {
  const [mobile, setMobile] = useState(false)
  const nav = (id) => { go(id); setMobile(false) }
  const backendRoute = operationsRoute(session?.user)
  const visibleNav = backendRoute
    ? [...navItems, [backendRoute, '运营后台']]
    : session?.user?.roles?.includes('expert') ? [...navItems, ['expert-workspace', '专家工作台']] : navItems
  return <header className="topbar">
    <button className="brand" onClick={() => nav('home')}><span className="seal">念</span><span>一念</span><small>AI 起名</small></button>
    <nav className={mobile ? 'nav open' : 'nav'}>
      {visibleNav.map(([id, label]) => <button key={id} className={page === id ? 'active' : ''} onClick={() => nav(id)}>{label}</button>)}
    </nav>
    <div className="header-actions">
      {session ? <>
        <button className="credit-pill" onClick={() => go('pricing')}><Coins size={16}/><b>{balance ?? '—'}</b> 次</button>
        <div className="user-menu"><button className="user-profile-link" onClick={() => go('account')}><CircleUserRound size={20}/><span>{session.user?.username}</span></button><button title="退出登录" onClick={logout}><LogOut size={16}/></button></div>
      </> : <button className="ink-button small" onClick={() => openAuth('login')}>登录 / 注册</button>}
      <button className="menu-button" onClick={() => setMobile(!mobile)}>{mobile ? <X/> : <Menu/>}</button>
    </div>
  </header>
}

function Home({ go }) {
  return <main>
    <section className="hero wrap">
      <div className="hero-copy reveal">
        <div className="eyebrow"><Sparkles size={14}/> AI × 东方文化</div>
        <h1>一字一世界<br/><em>一念一生名</em></h1>
        <p>融合传统文化意蕴与现代 AI 推演，为新生、品牌与陪伴，找到那个恰如其分的名字。</p>
        <div className="hero-actions"><button className="red-button" onClick={() => go('create')}>开始起名 <ArrowRight size={18}/></button><button className="text-button" onClick={() => go('knowledge')}>了解专属知识库 <ChevronRight size={17}/></button></div>
        <div className="hero-proof"><div><b>3</b><span>注册即赠次数</span></div><i/><div><b>5</b><span>每轮精选名字</span></div><i/><div><b>∞</b><span>支持连续微调</span></div></div>
      </div>
      <div className="hero-art reveal delay">
        <div className="sun"/><div className="mountain mountain-a"/><div className="mountain mountain-b"/>
        <div className="name-card card-one"><span>出处</span><h3>清和</h3><p>“首夏犹清和，芳草亦未歇”</p></div>
        <div className="name-card card-two"><span>寓意</span><h3>既明</h3><p>光明通达 · 坚定清醒</p></div>
        <div className="floating-seal">名<br/>有<br/>所<br/>归</div>
      </div>
    </section>
    <section className="scene-section wrap">
      <div className="section-head"><span>为每一种珍贵的开始</span><h2>不止起名，更是在讲述故事</h2></div>
      <div className="scene-grid">
        <button className="scene-card" onClick={() => go('create', '人名')}><div className="scene-icon coral"><UserRound/></div><small>新生 · 人名</small><h3>赠予一生的祝福</h3><p>融合姓氏、性别与文化偏好，寻得音形义俱佳的名字。</p><span>开始构思 <ArrowRight size={15}/></span></button>
        <button className="scene-card featured" onClick={() => go('create', '企业名')}><div className="scene-icon blue"><Building2/></div><small>创业 · 品牌</small><h3>让品牌自带光芒</h3><p>结合行业定位与私有资料，并同步探索可用 .com 域名。</p><span>开始构思 <ArrowRight size={15}/></span></button>
        <button className="scene-card" onClick={() => go('create', '宠物名')}><div className="scene-icon gold"><Dog/></div><small>陪伴 · 宠物</small><h3>呼唤心中的欢喜</h3><p>根据品种、性格与相处故事，创造亲昵又独特的称呼。</p><span>开始构思 <ArrowRight size={15}/></span></button>
      </div>
    </section>
    <section className="how-section"><div className="wrap how-inner"><div><span className="kicker">简单，却不简单</span><h2>三步，遇见理想之名</h2><p>把你的期待告诉我们，其余的交给一念。</p></div><div className="steps"><div><b>01</b><h4>说出期待</h4><p>选择场景，填写你的故事</p></div><div><b>02</b><h4>AI 深度推演</h4><p>文化语义与现代审美融合</p></div><div><b>03</b><h4>持续打磨</h4><p>用自然语言反馈，直到满意</p></div></div></div></section>
  </main>
}

const categoryMeta = {
  '人名': { icon: UserRound, text: '为新生命寻一份隽永的祝福' },
  '企业名': { icon: Building2, text: '为你的事业创造独特品牌印记' },
  '宠物名': { icon: Dog, text: '为亲密伙伴取一个可爱的称呼' },
}

function NameCard({ item, index, selected, selecting, onSelect }) {
  return <article className={`result-card ${selected ? 'is-selected' : ''}`}>
    <div className="result-index">0{index + 1}</div><div className="result-main"><h3>{item.name}</h3><div className="result-detail"><span>灵感出处</span><p>{item.reference || '源于 AI 创意推演'}</p></div><div className="result-detail"><span>名字寓意</span><p>{item.moral}</p></div>
    {item.domain && <div className="domain-row"><code>{item.domain}</code><span className={item.domain_status?.includes('未注册') ? 'available' : ''}>{item.domain_status}</span></div>}</div>
    <button className={`select-name-button ${selected ? 'selected' : ''}`} disabled={selecting} onClick={() => onSelect(item)}>{selected ? <><Check size={15}/> 已选定</> : selecting ? <LoaderCircle className="spin" size={15}/> : '选为最终名称'}</button>
  </article>
}

function CreatePage({ session, openAuth, refreshBalance, preset, go, notify }) {
  const [category, setCategory] = useState(() => categoryFromPreset(preset))
  const [form, setForm] = useState({ surname: '', gender: '不限', length: '不限', other: '', exclude: '' })
  const [loading, setLoading] = useState(false), [results, setResults] = useState([])
  const [thread, setThread] = useState(''), [feedback, setFeedback] = useState(''), [refining, setRefining] = useState(false)
  const [selected, setSelected] = useState(null), [selectingName, setSelectingName] = useState('')
  const [projectId, setProjectId] = useState(null)
  const [projectTitle, setProjectTitle] = useState('')
  useEffect(() => {
    setResults([]); setThread(''); setSelected(null); setProjectId(null)
    const normalizedPreset = normalizeCreatePreset(preset)
    if (!normalizedPreset) { setCategory('人名'); return }
    if (!normalizedPreset.startsWith('project:')) { setCategory(normalizedPreset); return }
    const id = Number(normalizedPreset.slice(8))
    api.project(id).then((project) => {
      const conditions = project.conditions || {}
      setProjectId(project.id); setProjectTitle(project.title); setCategory(project.category)
      setForm({
        surname: conditions.surname || '', gender: conditions.gender || '不限',
        length: conditions.length || '不限', other: conditions.other || '',
        exclude: (conditions.exclude || []).join('、'),
      })
      notify(`已载入项目“${project.title}”。`, 'success')
    }).catch((e) => notify(e.message, 'error'))
  }, [preset])
  const update = (key, value) => setForm((old) => ({ ...old, [key]: value }))
  const projectConditions = () => ({ category, surname: form.surname.trim(), gender: form.gender, length: form.length, other: form.other.trim(), exclude: form.exclude.split(/[，,、\s]+/).filter(Boolean) })
  const saveDraft = async () => {
    if (category === '人名' && !form.surname.trim()) return notify('请先填写姓氏。', 'error')
    setLoading(true)
    try {
      const payload = { title: projectTitle.trim() || `${category}命名项目`, conditions: projectConditions() }
      const project = projectId ? await api.updateProject(projectId, payload) : await api.createProject(payload)
      setProjectId(project.id); setProjectTitle(project.title); notify('命名条件已保存为草稿。', 'success')
    } catch(e) { notify(e.message, 'error') } finally { setLoading(false) }
  }
  const generate = async (e) => {
    e.preventDefault(); if (!session) return openAuth('login')
    setLoading(true); setResults([]); setSelected(null)
    try {
      const conditions = projectConditions()
      let activeProjectId = projectId
      if (activeProjectId) {
        await api.updateProject(activeProjectId, { title: projectTitle.trim() || `${category}命名项目`, conditions })
      } else if (projectTitle.trim()) {
        const draft = await api.createProject({ title: projectTitle.trim(), conditions })
        activeProjectId = draft.id; setProjectId(draft.id)
      }
      const data = await api.generateNames({ project_id: activeProjectId || undefined, ...conditions })
      setResults(data.names || []); setThread(data.thread_id); setProjectId(data.project_id); refreshBalance(); notify('名字已为你准备好，并已保存到项目。', 'success')
    } catch (e) { notify(e.message, 'error') } finally { setLoading(false) }
  }
  const refine = async () => {
    if (!feedback.trim()) return
    setRefining(true)
    try { const data = await api.feedbackNames({ thread_id: thread, category, feedback: feedback.trim() }); setResults(data.names || []); setSelected(null); setFeedback(''); notify('已根据你的想法重新推演，请重新确认最终名称。', 'success') }
    catch (e) { notify(e.message, 'error') } finally { setRefining(false) }
  }
  const selectName = async (item) => {
    setSelectingName(item.name)
    try {
      const data = await api.selectName({ thread_id: thread, name: item.name })
      setSelected(data)
      notify(`已将“${data.name}”设为最终名称。`, 'success')
    } catch (e) { notify(e.message, 'error') } finally { setSelectingName('') }
  }
  return <main className="page-shell wrap">
    <div className="page-title"><span className="eyebrow"><WandSparkles size={14}/> 智能命名工坊</span><h1>把你的期待，写进名字里</h1><p>{categoryMeta[category].text}</p></div>
    <div className="creator-layout">
      <form className="form-panel" onSubmit={generate}>
        <label className="field"><span>项目名称 <small>可选，方便历史查找</small></span><input value={projectTitle} onChange={(e) => setProjectTitle(e.target.value)} maxLength="120" placeholder={`${category}命名项目`}/></label>
        <div className="category-tabs">{Object.entries(categoryMeta).map(([key, meta]) => { const Icon = meta.icon; return <button type="button" className={category === key ? 'active' : ''} key={key} onClick={() => { setCategory(key); setProjectTitle(''); setResults([]); setThread(''); setSelected(null); setProjectId(null) }}><Icon size={18}/>{key}</button> })}</div>
        {category === '人名' && <div className="field-row"><label className="field"><span>姓氏 <i>*</i></span><input required value={form.surname} onChange={(e) => update('surname', e.target.value)} placeholder="例如：陈" maxLength={4}/></label><label className="field"><span>性别偏好</span><select value={form.gender} onChange={(e) => update('gender', e.target.value)}><option>不限</option><option>男</option><option>女</option></select></label></div>}
        <div className="field"><span>名字长度</span><div className="choice-row">{['不限','单字','两字','多字'].map((v) => <button type="button" key={v} className={form.length === v ? 'selected' : ''} onClick={() => update('length', v)}>{v}</button>)}</div></div>
        <label className="field"><span>{category === '企业名' ? '品牌故事与行业定位' : category === '宠物名' ? '它的品种、性格和故事' : '你对名字的期待'}</span><textarea value={form.other} onChange={(e) => update('other', e.target.value)} placeholder={category === '企业名' ? '例如：面向年轻人的 AI 智能硬件品牌，希望简洁、有未来感…' : category === '宠物名' ? '例如：一只活泼的金毛，毛色像暖阳…' : '例如：希望名字清朗大方，寄托坚韧与自由的期望…'} rows="5"/></label>
        <label className="field"><span>不希望出现的字 <small>选填，用逗号分隔</small></span><input value={form.exclude} onChange={(e) => update('exclude', e.target.value)} placeholder="例如：伟，强，轩"/></label>
        <div className="create-actions">{!results.length && <button type="button" className="outline-button" disabled={loading} onClick={saveDraft}><FolderKanban size={16}/> 保存草稿</button>}<button className="red-button" disabled={loading}>{loading ? <><LoaderCircle className="spin" size={18}/> 正在翻阅典籍与灵感…</> : <><Sparkles size={18}/> 为我起名</>}</button></div>
        <p className="cost-note"><Coins size={14}/> 每次首次生成消耗 1 次额度，微调不额外消耗</p>
      </form>
      <section className="results-panel">
        {!results.length && !loading && <div className="empty-state"><div className="empty-orbit"><Feather/></div><h3>好名字，值得等待</h3><p>完善左侧信息，AI 将为你精选 5 个名字<br/>并逐一解读出处与寓意。</p></div>}
        {loading && <div className="thinking-state"><div className="ink-loader"><span/><span/><span/></div><h3>正在推演名字</h3><p>从音韵、字形、寓意与文化出处多维筛选</p></div>}
        {!!results.length && <><div className="results-head"><div><small>本轮灵感</small><h2>为你精选的名字</h2></div><div className="results-head-actions"><button onClick={() => go('projects', projectId)}><FolderKanban size={15}/> 查看项目</button><button onClick={() => { setResults([]); setThread(''); setSelected(null); setProjectId(null) }}><RefreshCw size={15}/> 新建命名</button></div></div><p className="selection-hint">请选择一个名字作为最终选择。确认后仍可重新选择。</p><div className="results-list">{results.map((item, i) => <NameCard key={`${item.name}-${i}`} item={item} index={i} selected={selected?.name === item.name} selecting={selectingName === item.name} onSelect={selectName}/>)}</div>{selected && <div className="final-selection"><div><span><Check size={15}/> 最终选择</span><h3>{selected.name}</h3><p>{selected.category === '企业名' ? '名称已保存，可以继续生成 Logo 或进行综合风险校验。' : '名称已保存为你的最终选择。'}</p></div>{selected.can_generate_logo && <div className="order-actions"><button className="outline-button" onClick={() => go('validation', selected.id)}><ShieldCheck size={17}/> 名称校验</button><button className="red-button" onClick={() => go('logo', selected.id)}><Palette size={17}/> 生成 Logo</button></div>}</div>}<div className="feedback-box"><div><MessageCircleMore size={19}/><span><b>还差一点感觉？</b> 直接告诉 AI 如何调整</span></div><div className="feedback-input"><input value={feedback} onChange={(e) => setFeedback(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && refine()} placeholder="例如：更古典一些，保留第二个名字的感觉…"/><button onClick={refine} disabled={refining || !feedback.trim()}>{refining ? <LoaderCircle className="spin"/> : <Send/>}</button></div></div></>}
      </section>
    </div>
  </main>
}

function KnowledgePage({ session, openAuth, notify }) {
  const [file, setFile] = useState(null), [dragging, setDragging] = useState(false), [loading, setLoading] = useState(false)
  const choose = (candidate) => { if (candidate && ['text/plain','application/pdf'].includes(candidate.type)) setFile(candidate); else notify('仅支持 TXT 或 PDF 文件。', 'error') }
  const upload = async () => { if (!session) return openAuth('login'); if (!file) return; setLoading(true); try { const data = await api.uploadKnowledge(file); notify(data.message, 'success'); setFile(null) } catch (e) { notify(e.message, 'error') } finally { setLoading(false) } }
  return <main className="page-shell wrap narrow"><div className="page-title"><span className="eyebrow"><BookOpen size={14}/> 专属知识库</span><h1>让 AI 真正理解你的品牌</h1><p>上传品牌规范、创始故事或文化资料，企业起名时会优先参考你的专属内容。</p></div><div className="knowledge-layout"><section className="upload-panel"><div className={`dropzone ${dragging ? 'dragging' : ''}`} onDragOver={(e) => {e.preventDefault();setDragging(true)}} onDragLeave={() => setDragging(false)} onDrop={(e) => {e.preventDefault();setDragging(false);choose(e.dataTransfer.files[0])}}><input id="file-input" type="file" accept=".txt,.pdf" onChange={(e) => choose(e.target.files[0])}/>{file ? <><FileText size={42}/><h3>{file.name}</h3><p>{(file.size / 1024).toFixed(1)} KB · 已准备上传</p><button className="text-button" onClick={() => setFile(null)}>重新选择</button></> : <><UploadCloud size={44}/><h3>拖放文件到这里</h3><p>或点击选择本地文件</p><label htmlFor="file-input" className="outline-button">选择文件</label><small>支持 TXT、PDF 格式</small></>}</div><button className="red-button wide" disabled={!file || loading} onClick={upload}>{loading ? <><LoaderCircle className="spin"/> 正在上传…</> : <><UploadCloud size={18}/> 构建我的知识库</>}</button></section><aside className="knowledge-info"><span className="kicker">它如何工作</span><div><b>01</b><p><strong>资料解析</strong>系统将文档安全切分和向量化。</p></div><div><b>02</b><p><strong>用户隔离</strong>每位用户的数据独立存储，互不混用。</p></div><div><b>03</b><p><strong>智能检索</strong>企业起名时自动寻找最相关的品牌信息。</p></div><div className="privacy-note"><MoonStar/><p>建议上传清晰、结构化的文字资料。后台 Worker 处理完成后即可用于起名。</p></div></aside></div></main>
}

const knowledgeStatusText = { queued: '排队中', processing: '处理中', completed: '已完成', failed: '处理失败', deleting: '删除中' }

function ManagedKnowledgePage({ session, openAuth, notify }) {
  const [file, setFile] = useState(null), [dragging, setDragging] = useState(false), [uploading, setUploading] = useState(false)
  const [files, setFiles] = useState([]), [loading, setLoading] = useState(true), [busy, setBusy] = useState(null)
  const load = () => api.knowledgeFiles().then(setFiles).catch((e) => notify(e.message, 'error')).finally(() => setLoading(false))
  useEffect(() => { load() }, [])
  useEffect(() => { if (!files.some((item) => ['queued','processing'].includes(item.status))) return; const timer = setInterval(load, 4000); return () => clearInterval(timer) }, [files.map((item) => item.status).join(',')])
  const choose = (candidate) => { if (candidate && (/\.(txt|pdf)$/i.test(candidate.name))) setFile(candidate); else notify('仅支持 TXT 或 PDF 文件。', 'error') }
  const upload = async () => { if (!session) return openAuth('login'); if (!file) return; setUploading(true); try { const data = await api.uploadKnowledge(file); setFiles((old) => [data.file, ...old]); setFile(null); notify(data.message, 'success') } catch(e) { notify(e.message, 'error'); load() } finally { setUploading(false) } }
  const retry = async (item) => { setBusy(item.id); try { const next = await api.reprocessKnowledge(item.id); setFiles((old) => old.map((v) => v.id === item.id ? next : v)); notify('文件已重新进入处理队列', 'success') } catch(e) { notify(e.message, 'error') } finally { setBusy(null) } }
  const remove = async (item) => { if (!confirm(`确定删除“${item.original_name}”及其向量数据吗？`)) return; setBusy(item.id); try { await api.deleteKnowledge(item.id); setFiles((old) => old.filter((v) => v.id !== item.id)); notify('文件已删除', 'success') } catch(e) { notify(e.message, 'error') } finally { setBusy(null) } }
  return <main className="page-shell wrap narrow"><div className="page-title"><span className="eyebrow"><BookOpen size={14}/> 专属知识库</span><h1>让 AI 真正理解你的品牌</h1><p>上传品牌规范、创始故事或文化资料，处理完成后企业起名会优先参考这些内容。</p></div><div className="knowledge-layout"><section className="upload-panel"><div className={`dropzone ${dragging ? 'dragging' : ''}`} onDragOver={(e) => { e.preventDefault(); setDragging(true) }} onDragLeave={() => setDragging(false)} onDrop={(e) => { e.preventDefault(); setDragging(false); choose(e.dataTransfer.files[0]) }}><input id="managed-file-input" type="file" accept=".txt,.pdf" onChange={(e) => choose(e.target.files[0])}/>{file ? <><FileText size={42}/><h3>{file.name}</h3><p>{(file.size / 1024).toFixed(1)} KB · 已准备上传</p><button className="text-button" onClick={() => setFile(null)}>重新选择</button></> : <><UploadCloud size={44}/><h3>拖放文件到这里</h3><p>或点击选择本地文件</p><label htmlFor="managed-file-input" className="outline-button">选择文件</label><small>支持 TXT、PDF，单个不超过 10MB</small></>}</div><button className="red-button wide" disabled={!file || uploading} onClick={upload}>{uploading ? <><LoaderCircle className="spin"/> 正在上传…</> : <><UploadCloud size={18}/> 构建我的知识库</>}</button></section><aside className="knowledge-info"><span className="kicker">处理流程</span><div><b>01</b><p><strong>资料解析</strong>后台 Worker 安全切分文档。</p></div><div><b>02</b><p><strong>向量化</strong>每位用户的数据独立存储。</p></div><div><b>03</b><p><strong>智能检索</strong>命名时引用相关品牌资料。</p></div><div className="privacy-note"><MoonStar/><p>下方会自动刷新状态；失败任务可以重新处理。</p></div></aside></div><section className="knowledge-files"><div className="account-card-title"><FileText/><div><h3>我的资料</h3><p>查看状态、文本块数量和失败原因</p></div></div>{loading ? <div className="center-loading"><LoaderCircle className="spin"/> 正在读取…</div> : files.length ? <div className="knowledge-file-list">{files.map((item) => <article className="account-card" key={item.id}><FileText/><div><h3>{item.original_name}</h3><p>{(item.size_bytes / 1024).toFixed(1)} KB · {new Date(item.created_at).toLocaleString()}</p>{item.error_message && <small>{item.error_message}</small>}</div><span className={`knowledge-status ${item.status}`}>{knowledgeStatusText[item.status] || item.status}{item.status === 'completed' ? ` · ${item.chunk_count} 块` : ''}</span><div className="order-actions">{['failed','completed'].includes(item.status) && <button className="outline-button" onClick={() => retry(item)} disabled={busy === item.id}><RefreshCw size={14}/> 重新处理</button>}<button className="danger-link" onClick={() => remove(item)} disabled={busy === item.id}>删除</button></div></article>)}</div> : <div className="empty-state standalone"><BookOpen/><h3>还没有资料</h3><p>上传第一份企业资料来建立专属知识库。</p></div>}</section></main>
}

function LogoPage({ selectionId, session, openAuth, notify, go }) {
  const [selection, setSelection] = useState(null), [loadingSelection, setLoadingSelection] = useState(false)
  const [stylePreset, setStylePreset] = useState(''), [styleFeedback, setStyleFeedback] = useState('')
  const [loading, setLoading] = useState(false), [result, setResult] = useState(null)
  const styles = ['极简现代','东方雅韵','未来科技','自然清新','高端奢华']
  useEffect(() => {
    setSelection(null); setResult(null)
    if (!selectionId || !session) return
    setLoadingSelection(true)
    api.selectedName(selectionId).then((data) => {
      if (!data.can_generate_logo) throw new Error('只有已选定的企业名称可以生成 Logo。')
      setSelection(data)
      if (data.logo_url) setResult({ selection_id: data.id, company_name: data.name, logo_prompt: data.logo_prompt, logo_url: data.logo_url, logo_status: data.logo_status })
    }).catch((e) => notify(e.message, 'error')).finally(() => setLoadingSelection(false))
  }, [selectionId, session?.access_token])
  const generate = async (e) => {
    e.preventDefault()
    if (!session) return openAuth('login')
    if (!selection) return notify('请先从企业候选名中选定一个最终名称。', 'error')
    const style = [stylePreset, styleFeedback.trim()].filter(Boolean).join('；')
    setLoading(true); setResult(null)
    try { setResult(await api.generateLogo({ selection_id: selection.id, style_feedback: style })) }
    catch(e) { notify(e.message, 'error') } finally { setLoading(false) }
  }
  if (!session) return <main className="page-shell wrap narrow"><div className="page-title"><span className="eyebrow"><Palette size={14}/> AI 品牌视觉</span><h1>先登录，再延续品牌灵感</h1><p>Logo 只会基于你已选定的企业名称生成。</p></div><div className="logo-prerequisite"><Palette/><h3>需要登录账户</h3><p>登录后先生成企业候选名，并确认一个最终名称。</p><button className="red-button" onClick={() => openAuth('login')}>登录 / 注册</button></div></main>
  if (!selectionId) return <main className="page-shell wrap narrow"><div className="page-title"><span className="eyebrow"><Palette size={14}/> AI 品牌视觉</span><h1>从选定名称开始设计 Logo</h1><p>先生成企业候选名并选定其中一个，Logo 入口随后自动出现。</p></div><div className="logo-prerequisite"><Building2/><h3>尚未选定企业名称</h3><p>Logo 不能使用任意输入名称，它会与最终选择记录关联保存。</p><button className="red-button" onClick={() => go('create', '企业名')}>去生成企业名</button></div></main>
  if (loadingSelection) return <main className="page-shell wrap"><div className="center-loading"><LoaderCircle className="spin"/> 正在读取最终名称…</div></main>
  if (!selection) return <main className="page-shell wrap narrow"><div className="logo-prerequisite"><Building2/><h3>无法读取这个最终名称</h3><p>请返回企业起名页面重新选择。</p><button className="red-button" onClick={() => go('create', '企业名')}>返回企业起名</button></div></main>
  return <main className="page-shell wrap"><div className="page-title"><span className="eyebrow"><Palette size={14}/> AI 品牌视觉</span><h1>从名字，到第一眼心动</h1><p>基于你最终选定的企业名称生成专属 Logo 概念。</p></div><div className="logo-layout"><form className="form-panel" onSubmit={generate}><div className="selected-company"><span><Check size={15}/> 已选企业名称</span><h2>{selection.name}</h2><p>{selection.moral}</p></div><div className="field"><span>选择风格</span><div className="style-chips">{styles.map((v) => <button type="button" className={stylePreset === v ? 'selected' : ''} key={v} onClick={() => setStylePreset(v)}>{v}</button>)}</div></div><label className="field"><span>补充你的想法</span><textarea rows="5" value={styleFeedback} onChange={(e) => setStyleFeedback(e.target.value)} placeholder="例如：主色使用青绿色，图形融入山水意象，避免复杂细节…" maxLength="500"/></label><button className="red-button wide" disabled={loading}>{loading ? <><LoaderCircle className="spin"/> AI 正在绘制…</> : <><WandSparkles size={18}/> 生成 Logo</>}</button></form><section className="logo-canvas">{!result && !loading && <div className="empty-state"><div className="logo-placeholder"><span>{selection.name?.[0] || '念'}</span></div><h3>{selection.name}的品牌印记</h3><p>选择视觉风格，开启第一次 Logo 探索</p></div>}{loading && <div className="thinking-state"><div className="brush-loader"/><h3>正在描绘品牌气质</h3><p>图像生成通常需要一些时间，请耐心等待</p></div>}{result && result.logo_url && <div className="logo-result"><div className="logo-image-wrap"><img src={resolveAssetUrl(result.logo_url)} alt={`${result.company_name} Logo`}/></div><div><span className="status-dot">{result.logo_status}</span><h2>{result.company_name}</h2><p>{result.logo_prompt}</p><a className="outline-button" href={resolveAssetUrl(result.logo_url)} download target="_blank" rel="noreferrer"><Download size={16}/> 查看原图</a></div></div>}{result && !result.logo_url && !loading && <div className="empty-state"><Palette/><h3>Logo 暂未生成</h3><p>{result.logo_status}</p></div>}</section></div></main>
}

const projectStatus = {
  draft: '草稿', generated: '候选已生成', selected: '已最终选名', archived: '已归档',
}

function ProjectsPage({ projectId, notify, go }) {
  const [projects, setProjects] = useState([]), [detail, setDetail] = useState(null)
  const [filter, setFilter] = useState(''), [loading, setLoading] = useState(true)
  const [title, setTitle] = useState(''), [saving, setSaving] = useState(false)
  const loadList = () => {
    setLoading(true)
    api.projects(filter).then(setProjects).catch((e) => notify(e.message, 'error')).finally(() => setLoading(false))
  }
  const loadDetail = (id) => {
    setLoading(true); setDetail(null)
    return api.project(id).then((data) => { setDetail(data); setTitle(data.title) }).catch((e) => { notify(e.message, 'error'); go('projects') }).finally(() => setLoading(false))
  }
  useEffect(() => { if (projectId) loadDetail(projectId); else { setDetail(null); loadList() } }, [projectId, filter])
  const rename = async (e) => {
    e.preventDefault(); if (!title.trim()) return
    setSaving(true)
    try { await api.updateProject(detail.id, { title: title.trim() }); await loadDetail(detail.id); notify('项目名称已更新。', 'success') }
    catch(e) { notify(e.message, 'error') } finally { setSaving(false) }
  }
  const toggleArchive = async () => {
    setSaving(true)
    try {
      if (detail.status === 'archived') await api.restoreProject(detail.id)
      else await api.archiveProject(detail.id)
      await loadDetail(detail.id); notify(detail.status === 'archived' ? '项目已恢复。' : '项目已归档。', 'success')
    } catch(e) { notify(e.message, 'error') } finally { setSaving(false) }
  }
  const selectFromHistory = async (candidate) => {
    setSaving(true)
    try { await api.selectName({ thread_id: detail.thread_id, name: candidate.name }); await loadDetail(detail.id); notify(`已将“${candidate.name}”设为最终名称。`, 'success') }
    catch(e) { notify(e.message, 'error') } finally { setSaving(false) }
  }
  if (!projectId) return <main className="page-shell wrap"><div className="page-title project-title-row"><div><span className="eyebrow"><FolderKanban size={14}/> 命名项目</span><h1>我的命名项目</h1><p>每次生成、反馈修改和最终选择都会按项目完整保存。</p></div><button className="red-button" onClick={() => go('create')}><WandSparkles size={17}/> 新建命名项目</button></div><div className="project-filters">{[['','全部'],['draft','草稿'],['generated','生成中'],['selected','已选名'],['archived','已归档']].map(([value,label]) => <button key={value} className={filter === value ? 'active' : ''} onClick={() => setFilter(value)}>{label}</button>)}</div>{loading ? <div className="thinking-state"><LoaderCircle className="spin"/><p>正在读取项目…</p></div> : projects.length ? <div className="project-grid">{projects.map((project) => <button className="project-card" key={project.id} onClick={() => go('projects', project.id)}><div><span className={`project-status ${project.status}`}>{projectStatus[project.status]}</span><small>{new Date(project.updated_at).toLocaleDateString()}</small></div><h3>{project.title}</h3><p>{project.category} · {project.current_round ? `${project.current_round} 轮候选` : '尚未生成'}</p>{project.final_name && <strong><Check size={14}/> {project.final_name}</strong>}</button>)}</div> : <div className="empty-state project-empty"><FolderKanban/><h3>还没有命名项目</h3><p>完成第一次 AI 起名后，项目会自动保存在这里。</p><button className="red-button" onClick={() => go('create')}>开始第一次命名</button></div>}</main>
  if (loading && !detail) return <main className="page-shell wrap"><div className="thinking-state"><LoaderCircle className="spin"/><p>正在读取项目详情…</p></div></main>
  if (!detail) return null
  const latestRound = detail.rounds?.[detail.rounds.length - 1]
  return <main className="page-shell wrap"><button className="project-back" onClick={() => go('projects')}><ChevronRight/> 返回项目列表</button><div className="project-detail-head"><div><span className={`project-status ${detail.status}`}>{projectStatus[detail.status]}</span><h1>{detail.title}</h1><p>{detail.category} · 共 {detail.current_round} 轮候选 · 创建于 {new Date(detail.created_at).toLocaleDateString()}</p></div><div className="project-actions">{detail.status === 'draft' && <button className="red-button" onClick={() => go('create', `project:${detail.id}`)}><WandSparkles size={16}/> 继续填写并生成</button>}<button className="outline-button" disabled={saving} onClick={toggleArchive}>{detail.status === 'archived' ? <><ArchiveRestore size={16}/> 恢复项目</> : <><Archive size={16}/> 归档项目</>}</button></div></div><div className="project-detail-layout"><section><div className="project-section"><div className="account-card-title"><Pencil/><div><h3>项目名称</h3><p>用于在历史列表中快速识别</p></div></div><form className="project-rename" onSubmit={rename}><input value={title} maxLength="120" onChange={(e) => setTitle(e.target.value)}/><button className="outline-button" disabled={saving}>保存</button></form></div>{detail.final_selection && <div className="project-section project-final"><span><Check size={15}/> 最终选择</span><h2>{detail.final_selection.name}</h2><p>{detail.final_selection.moral}</p>{detail.final_selection.can_generate_logo && <div className="order-actions"><button className="outline-button" onClick={() => go('validation', detail.final_selection.id)}><ShieldCheck size={16}/> 名称校验</button><button className="red-button" onClick={() => go('logo', detail.final_selection.id)}><Palette size={16}/> {detail.final_selection.logo_url ? '查看 Logo' : '生成 Logo'}</button></div>}</div>}<div className="project-section"><h3>命名条件</h3><div className="condition-grid">{Object.entries(detail.conditions || {}).filter(([,v]) => v && (!Array.isArray(v) || v.length)).map(([key,value]) => <div key={key}><span>{{surname:'姓氏',gender:'性别',length:'长度',other:'补充诉求',exclude:'排除内容',category:'类型'}[key] || key}</span><b>{Array.isArray(value) ? value.join('、') : value}</b></div>)}</div></div></section><section className="project-history"><h2>候选历史</h2>{[...(detail.rounds || [])].reverse().map((round) => <article key={round.id} className="project-round"><header><div><b>第 {round.round_no} 轮</b>{round.feedback && <p>修改意见：{round.feedback}</p>}</div><small>{new Date(round.created_at).toLocaleString()}</small></header><div>{round.candidates.map((candidate) => <div className={`history-candidate ${detail.final_selection?.name === candidate.name ? 'chosen' : ''}`} key={candidate.id}><div><h3>{candidate.name}</h3><p>{candidate.moral}</p><small>{candidate.reference}</small></div>{round.id === latestRound?.id && detail.status !== 'archived' && <button disabled={saving || detail.final_selection?.name === candidate.name} onClick={() => selectFromHistory(candidate)}>{detail.final_selection?.name === candidate.name ? '已选定' : '选为最终名'}</button>}</div>)}</div></article>)}</section></div></main>
}

function AccountPage({ session, notify, onSessionUpdate, go }) {
  const [profile, setProfile] = useState(session.user), [devices, setDevices] = useState([]), [records, setRecords] = useState([])
  const [dashboard, setDashboard] = useState(null), [dashboardLoading, setDashboardLoading] = useState(true), [downloading, setDownloading] = useState(null)
  const [loading, setLoading] = useState(true), [saving, setSaving] = useState(false), [username, setUsername] = useState(session.user?.username || '')
  const [passwords, setPasswords] = useState({ current_password: '', new_password: '', confirm_password: '' })
  const load = () => {
    setLoading(true)
    Promise.all([api.me(), api.devices(), api.loginRecords()])
      .then(([me, deviceList, loginList]) => { setProfile(me); setUsername(me.username); setDevices(deviceList); setRecords(loginList); onSessionUpdate(me) })
      .catch((e) => notify(e.message, 'error')).finally(() => setLoading(false))
    setDashboardLoading(true)
    api.dashboard().then(setDashboard).catch((e) => notify(`工作台加载失败：${e.message}`, 'error')).finally(() => setDashboardLoading(false))
  }
  useEffect(() => { load() }, [])
  const saveProfile = async (e) => { e.preventDefault(); setSaving(true); try { const data = await api.updateProfile({ username: username.trim() }); setProfile(data); onSessionUpdate(data); notify('个人资料已更新。', 'success') } catch(e) { notify(e.message, 'error') } finally { setSaving(false) } }
  const uploadAvatar = async (file) => { if (!file) return; setSaving(true); try { const data = await api.uploadAvatar(file); setProfile(data); onSessionUpdate(data); notify('头像已更新。', 'success') } catch(e) { notify(e.message, 'error') } finally { setSaving(false) } }
  const changePassword = async (e) => { e.preventDefault(); setSaving(true); try { const data = await api.changePassword(passwords); notify(data.message, 'success'); api.saveSession(null) } catch(e) { notify(e.message, 'error') } finally { setSaving(false) } }
  const revoke = async (id) => { try { await api.revokeDevice(id); setDevices((old) => old.map((item) => item.id === id ? { ...item, revoked_at: new Date().toISOString() } : item)); notify('设备登录已撤销。', 'success') } catch(e) { notify(e.message, 'error') } }
  const download = async (report) => { setDownloading(report.id); try { await api.downloadReport(report.id, `${report.name}-命名报告.pdf`); notify('报告已开始下载。', 'success') } catch(e) { notify(e.message, 'error') } finally { setDownloading(null) } }
  if (loading) return <main className="page-shell wrap"><div className="center-loading"><LoaderCircle className="spin"/> 正在读取账户资料…</div></main>
  const primaryAction = getPrimaryDashboardAction(dashboard || {})
  const moduleIcons = { account: <UserRound/>, credits: <Coins/>, projects: <FolderKanban/>, orders: <Crown/>, knowledge: <BookOpen/>, reports: <FileText/> }
  const moduleUnit = { credit_balance: '次可用', credit_logs: '条流水', projects_total: '个项目', orders_total: '笔订单', knowledge_files: '份资料', reports_total: '份报告' }
  const openModule = (item) => item.id === 'account' ? document.getElementById('account-settings')?.scrollIntoView({ behavior: 'smooth' }) : go(item.id)
  return <main className="page-shell wrap narrow">
    <div className="page-title"><span className="eyebrow"><CircleUserRound size={14}/> 用户中心</span><h1>我的一念工作台</h1><p>资料、次数、项目、订单、知识库和命名报告，都从这里统一进入。</p></div>
    <section className="user-dashboard">
      <div className="dashboard-hero"><div><small>PERSONAL WORKSPACE</small><h2>{profile.username}，欢迎回来</h2><p>从灵感生成到报告沉淀，继续推进你的命名项目。</p></div><button className="red-button" onClick={() => go(primaryAction.page)}>{primaryAction.label}<ArrowRight size={16}/></button></div>
      {dashboardLoading ? <div className="center-loading"><LoaderCircle className="spin"/> 正在汇总个人数据…</div> : dashboard && <>
        <div className="dashboard-stat-grid">
          <button onClick={() => go('credits')}><Coins/><div><b>{dashboard.credit_balance}</b><span>剩余次数 · 已使用 {dashboard.credit_total_used}</span></div><ChevronRight/></button>
          <button onClick={() => go('projects')}><FolderKanban/><div><b>{dashboard.projects_total}</b><span>命名项目 · {dashboard.projects_selected} 个已选名</span></div><ChevronRight/></button>
          <button onClick={() => go('orders')}><Crown/><div><b>{dashboard.orders_total}</b><span>我的订单 · {dashboard.orders_pending} 笔待支付</span></div><ChevronRight/></button>
          <button onClick={() => go('reports')}><FileText/><div><b>{dashboard.reports_total}</b><span>PDF 报告 · 安全鉴权下载</span></div><ChevronRight/></button>
        </div>
        <div className="dashboard-module-grid">{USER_CENTER_MODULES.map((item) => <button key={item.label} onClick={() => openModule(item)}>{moduleIcons[item.id]}<b>{item.label}</b><span>{item.countKey ? `${dashboard[item.countKey] ?? 0} ${moduleUnit[item.countKey]}` : '账户与安全'}</span></button>)}</div>
        <section className="account-card"><div className="dashboard-section-head"><h3>最近报告</h3><button onClick={() => go('reports')}>查看全部报告 →</button></div>{dashboard.recent_reports.length ? <div className="dashboard-report-list">{dashboard.recent_reports.map((report) => <article key={report.id}><FileText/><div><h4>{report.title}</h4><p>最终选名：{report.name}</p><small>{report.page_count} 页 · {(report.file_size / 1024).toFixed(1)} KB · {new Date(report.created_at).toLocaleString()}</small></div><button className="outline-button" disabled={downloading === report.id} onClick={() => download(report)}>{downloading === report.id ? <LoaderCircle className="spin"/> : <Download size={14}/>} 下载</button></article>)}</div> : <div className="empty-state standalone"><FileText/><h3>还没有命名报告</h3><p>完成最终选名后，可以生成包含完整命名依据的 PDF。</p><button className="outline-button" onClick={() => go('reports')}>前往报告中心</button></div>}</section>
      </>}
    </section>
    <div id="account-settings" className="account-settings-title"><h2>账户与安全</h2><p>管理个人资料、密码、登录设备与登录记录。</p></div>
    <div className="account-grid"><section className="account-card profile-card"><div className="avatar-editor"><div className="avatar-preview">{profile.avatar_url ? <img src={resolveAssetUrl(profile.avatar_url)} alt="头像"/> : <span>{profile.username?.[0]}</span>}</div><label title="更换头像"><Camera/><input type="file" accept="image/jpeg,image/png,image/webp" onChange={(e) => uploadAvatar(e.target.files[0])}/></label></div><div><h2>{profile.username}</h2><p>{profile.email}</p><div className="role-tags">{profile.roles?.map((role) => <span key={role}>{role === 'admin' ? '管理员' : role === 'member' ? '普通用户' : role}</span>)}</div></div></section><section className="account-card"><div className="account-card-title"><UserRound/><div><h3>个人资料</h3><p>修改展示用户名和头像</p></div></div><form onSubmit={saveProfile}><label className="field"><span>邮箱</span><input value={profile.email} disabled/></label><label className="field"><span>用户名</span><input minLength="4" maxLength="20" required value={username} onChange={(e) => setUsername(e.target.value)}/></label><button className="red-button" disabled={saving}>{saving ? <LoaderCircle className="spin"/> : '保存资料'}</button></form></section><section className="account-card"><div className="account-card-title"><KeyRound/><div><h3>修改密码</h3><p>修改后所有设备需要重新登录</p></div></div><form onSubmit={changePassword}><label className="field"><span>当前密码</span><input type="password" required minLength="6" value={passwords.current_password} onChange={(e) => setPasswords({ ...passwords, current_password: e.target.value })}/></label><label className="field"><span>新密码</span><input type="password" required minLength="6" value={passwords.new_password} onChange={(e) => setPasswords({ ...passwords, new_password: e.target.value })}/></label><label className="field"><span>确认新密码</span><input type="password" required minLength="6" value={passwords.confirm_password} onChange={(e) => setPasswords({ ...passwords, confirm_password: e.target.value })}/></label><button className="outline-button" disabled={saving}>修改密码</button></form></section><section className="account-card account-wide"><div className="account-card-title"><Monitor/><div><h3>登录设备</h3><p>撤销不认识或不再使用的设备</p></div></div><div className="security-list">{devices.map((device) => <div key={device.id}><Monitor/><div><b>{device.device_name}</b><span>{device.ip_address || '未知 IP'} · 最近活动 {new Date(device.last_seen_at).toLocaleString()}</span></div>{device.revoked_at ? <em>已撤销</em> : <button onClick={() => revoke(device.id)}>撤销</button>}</div>)}</div></section><section className="account-card account-wide"><div className="account-card-title"><ShieldCheck/><div><h3>最近登录记录</h3><p>最多展示最近 50 条</p></div></div><div className="security-list login-list">{records.map((record) => <div key={record.id}><span className={`login-state ${record.success ? 'success' : 'failed'}`}/><div><b>{record.success ? '登录成功' : `登录失败：${record.failure_reason}`}</b><span>{record.ip_address || '未知 IP'} · {new Date(record.created_at).toLocaleString()}</span></div></div>)}</div></section></div>
  </main>
}

function CreditsPage({ notify }) {
  const [account, setAccount] = useState(null), [logs, setLogs] = useState([]), [loading, setLoading] = useState(true)
  useEffect(() => { Promise.all([api.creditAccount(), api.creditLogs()]).then(([value, items]) => { setAccount(value); setLogs(items) }).catch((e) => notify(e.message, 'error')).finally(() => setLoading(false)) }, [])
  if (loading) return <main className="page-shell wrap"><div className="center-loading"><LoaderCircle className="spin"/> 正在读取次数权益…</div></main>
  return <main className="page-shell wrap narrow"><div className="page-title"><span className="eyebrow"><Coins size={14}/> 用户中心</span><h1>我的次数权益</h1><p>查看剩余次数、累计使用情况以及每一笔变动记录。</p></div><section className="credit-overview"><div><b>{account?.balance ?? 0}</b><span>剩余次数</span></div><div><b>{account?.total_used ?? 0}</b><span>累计使用</span></div><div><b>{account?.total_recharge ?? 0}</b><span>累计充值</span></div></section><section className="account-card account-wide"><div className="account-card-title"><Coins/><div><h3>次数流水</h3><p>最近 50 条赠送、消耗、返还、充值和后台调整记录</p></div></div><div className="security-list credit-log-list">{logs.map((log) => <div key={log.id}><strong className={log.change_count > 0 ? 'credit-plus' : 'credit-minus'}>{log.change_count > 0 ? `+${log.change_count}` : log.change_count}</strong><div><b>{log.remark}</b><span>{new Date(log.created_at).toLocaleString()} · 余额 {log.balance_after}</span></div></div>)}</div></section></main>
}

const operationsModules = [
  ['admin-users', '用户管理', '账号状态与用户列表', Users, 'users.read'],
  ['admin-security', '角色与审计', '权限配置、角色分配与操作留痕', ShieldCheck, 'roles.manage'],
  ['admin-credits', '次数管理', '余额、流水与人工调整', Coins, 'credits.manage'],
  ['admin-packages', '套餐管理', '价格、次数与上下架', Crown, 'packages.manage'],
  ['admin-orders', '订单管理', '支付、关闭与退款', FileText, 'orders.manage'],
  ['admin-projects', '项目管理', '命名进度与最终选名', FolderKanban, 'projects.manage'],
  ['admin-validations', '名称校验管理', '风险结果与数据覆盖率', ShieldCheck, 'validations.manage'],
  ['admin-brand-assets', '品牌资产管理', '定位与创意资产记录', Gem, 'brand_assets.manage'],
  ['admin-reports', '报告管理', '报告记录与安全下载', Download, 'reports.manage'],
  ['admin-knowledge', '知识库管理', '文件状态与重新处理', BookOpen, 'knowledge.manage'],
  ['admin-tasks', '异步任务管理', '进度、重试与取消', RefreshCw, 'tasks.manage'],
  ['admin-experts', '专家服务管理', '入驻审核、订单与结算', Star, 'experts.manage'],
  ['admin-community', '社区内容管理', '精选投票与举报处理', Vote, 'community.moderate'],
  ['admin-developers', '开放平台管理', '开发者、API 套餐与额度', KeyRound, 'developers.manage'],
  ['admin-growth', '增长活动管理', '邀请奖励、推广与佣金', Zap, 'growth.manage'],
]

function AdminDashboardPage({ notify, go, session }) {
  const [data, setData] = useState(null), [loading, setLoading] = useState(true)
  useEffect(() => { api.adminDashboard().then(setData).catch((e) => notify(e.message, 'error')).finally(() => setLoading(false)) }, [])
  if (loading) return <main className="page-shell wrap"><div className="center-loading"><LoaderCircle className="spin"/> 正在汇总运营数据…</div></main>
  return <main className="page-shell wrap"><div className="page-title"><span className="eyebrow"><BarChart3 size={14}/> 运营后台</span><h1>平台运营工作台</h1><p>统一查看核心数据，并进入用户、交易、内容和任务管理。</p></div><section className="operations-kpis"><article><Users/><b>{data?.users_total || 0}</b><span>注册用户 · {data?.users_active || 0} 个正常</span></article><article><FolderKanban/><b>{data?.projects_total || 0}</b><span>命名项目 · {data?.projects_selected || 0} 个已选名</span></article><article><Coins/><b>¥{Number(data?.paid_revenue || 0).toFixed(2)}</b><span>{data?.orders_total || 0} 笔订单 · {data?.orders_pending || 0} 笔待支付</span></article><article><FileText/><b>{data?.reports_total || 0}</b><span>PDF 报告 · {data?.knowledge_files || 0} 份知识文件</span></article></section><section className="operations-module-grid">{operationsModules.filter((item)=>hasPermission(session?.user,item[4])).map(([id,title,description,Icon]) => <button className="account-card" key={id} onClick={() => go(id)}><Icon/><div><h3>{title}</h3><p>{description}</p></div><ChevronRight/></button>)}</section>{data?.tasks_running > 0 && hasPermission(session?.user,'tasks.manage') && <div className="operations-alert"><RefreshCw className="spin"/><span>当前有 {data.tasks_running} 个异步任务正在排队或执行。</span><button onClick={() => go('admin-tasks')}>查看任务</button></div>}</main>
}

function AdminUsersPage({ notify, session }) {
  const [users, setUsers] = useState([]), [roles, setRoles] = useState([]), [loading, setLoading] = useState(true), [busy, setBusy] = useState(null)
  const canEditRoles=hasPermission(session?.user,'users.roles')&&hasPermission(session?.user,'roles.manage'), canFreeze=hasPermission(session?.user,'users.freeze')
  const load = () => Promise.all([api.adminUsers(), canEditRoles ? api.adminRoles() : Promise.resolve([])]).then(([items, roleItems]) => { setUsers(items); setRoles(roleItems) }).catch((e) => notify(e.message, 'error')).finally(() => setLoading(false))
  useEffect(() => { load() }, [])
  const toggle = async (user) => { setBusy(user.id); try { const next = await api.adminUpdateUserStatus(user.id, user.status === 'active' ? 'frozen' : 'active'); setUsers((old) => old.map((item) => item.id === user.id ? next : item)); notify(next.status === 'active' ? '用户已解冻。' : '用户已冻结。', 'success') } catch(e) { notify(e.message, 'error') } finally { setBusy(null) } }
  const setUserRoles = async (user, selected) => { if (!selected.length) return notify('用户至少需要保留一个角色。', 'error'); setBusy(user.id); try { const next = await api.adminUpdateUserRoles(user.id, selected); setUsers((old) => old.map((item) => item.id === user.id ? next : item)); notify('用户角色已更新，原登录会话已失效。', 'success') } catch(e) { notify(e.message, 'error') } finally { setBusy(null) } }
  const switchRole = (user, code) => { const selected = user.roles.includes(code) ? user.roles.filter((value) => value !== code) : [...user.roles, code]; setUserRoles(user, selected) }
  return <main className="page-shell wrap"><div className="page-title"><span className="eyebrow"><Users size={14}/> 运营后台</span><h1>用户管理</h1><p>查看账号状态，并按当前账号权限执行角色分配或冻结操作。</p></div>{loading ? <div className="center-loading"><LoaderCircle className="spin"/> 正在读取用户…</div> : <div className="operations-user-list">{users.map((user) => <article className="account-card" key={user.id}><div className="avatar-preview"><span>{user.username?.[0]}</span></div><div><h3>{user.username}</h3><p>{user.email}</p><small>{user.roles.join('、')} · 注册于 {new Date(user.created_at).toLocaleDateString()}</small>{canEditRoles&&<div className="role-editor">{roles.map((role) => <label key={role.code}><input type="checkbox" checked={user.roles.includes(role.code)} disabled={busy === user.id} onChange={() => switchRole(user, role.code)}/><span>{role.name}</span></label>)}</div>}</div><span className={`knowledge-status ${user.status === 'active' ? 'completed' : 'failed'}`}>{user.status === 'active' ? '正常' : '已冻结'}</span>{canFreeze&&<button className="outline-button" disabled={busy === user.id} onClick={() => toggle(user)}>{user.status === 'active' ? '冻结' : '解冻'}</button>}</article>)}</div>}</main>
}

function AdminSecurityPage({ notify, session }) {
  const [roles,setRoles]=useState([]),[permissions,setPermissions]=useState([]),[logs,setLogs]=useState([]),[busy,setBusy]=useState(''),[draft,setDraft]=useState({code:'',name:'',description:''})
  const canManage=hasPermission(session?.user,'roles.manage'), canAudit=hasPermission(session?.user,'audit.read')
  const load=()=>Promise.all([canManage?api.adminRoles():Promise.resolve([]),canManage?api.adminPermissions():Promise.resolve([]),canAudit?api.adminAuditLogs():Promise.resolve([])]).then(([r,p,l])=>{setRoles(r);setPermissions(p);setLogs(l)}).catch((e)=>notify(e.message,'error'))
  useEffect(() => { load() },[])
  const create=async(e)=>{e.preventDefault();setBusy('create');try{await api.adminCreateRole({...draft,permissions:[]});setDraft({code:'',name:'',description:''});await load();notify('自定义角色已创建。','success')}catch(e){notify(e.message,'error')}finally{setBusy('')}}
  const switchPermission=async(role,code)=>{const next=role.permissions.includes(code)?role.permissions.filter((value)=>value!==code):[...role.permissions,code];setBusy(role.code);try{await api.adminUpdateRolePermissions(role.code,next);await load();notify('角色权限已更新。','success')}catch(e){notify(e.message,'error')}finally{setBusy('')}}
  return <main className="page-shell wrap"><div className="page-title"><span className="eyebrow"><ShieldCheck size={14}/> 运营后台</span><h1>角色权限与审计日志</h1><p>创建业务角色、配置最小权限，并追溯后台敏感操作。</p></div><section className="security-admin-layout">{canManage&&<div><form className="account-card security-role-create" onSubmit={create}><h2>创建自定义角色</h2><div className="field-row"><input required pattern="[a-z][a-z0-9_-]+" minLength="2" maxLength="50" placeholder="角色代码，如 operator" value={draft.code} onChange={(e)=>setDraft({...draft,code:e.target.value})}/><input required minLength="2" placeholder="角色名称" value={draft.name} onChange={(e)=>setDraft({...draft,name:e.target.value})}/></div><input maxLength="255" placeholder="角色说明" value={draft.description} onChange={(e)=>setDraft({...draft,description:e.target.value})}/><button className="red-button" disabled={busy==='create'}>创建角色</button></form><div className="security-role-list">{roles.map((role)=><article className="account-card" key={role.code}><div><h3>{role.name} <code>{role.code}</code></h3><p>{role.description||'暂无说明'} · {role.is_system?'系统角色（不可修改）':'自定义角色'}</p></div><div className="permission-grid">{permissions.map((permission)=><label title={permission.description} key={permission.code}><input type="checkbox" checked={role.permissions.includes(permission.code)} disabled={role.is_system||busy===role.code} onChange={()=>switchPermission(role,permission.code)}/><span>{permission.name}</span><small>{permission.code}</small></label>)}</div></article>)}</div></div>}{canAudit&&<aside className="account-card audit-panel"><h2>最近审计日志</h2>{logs.map((log)=><article key={log.id}><span>{log.action}</span><b>{log.target_type} · {log.target_id||'—'}</b><small>管理员 #{log.admin_user_id} · {log.ip_address} · {new Date(log.created_at).toLocaleString()}</small><code>{log.detail||'{}'}</code></article>)}</aside>}</section></main>
}

function AdminProjectsPage({ notify }) {
  const [projects, setProjects] = useState([]), [status, setStatus] = useState(''), [loading, setLoading] = useState(true)
  useEffect(() => { setLoading(true); api.adminProjects(status).then(setProjects).catch((e) => notify(e.message, 'error')).finally(() => setLoading(false)) }, [status])
  return <main className="page-shell wrap"><div className="page-title"><span className="eyebrow"><FolderKanban size={14}/> 运营后台</span><h1>命名项目管理</h1><p>查看全平台项目类型、生成轮次、最终选名和用户归属。</p></div><div className="project-filters">{[['','全部'],['draft','草稿'],['generated','生成中'],['selected','已选名'],['archived','已归档']].map(([key,label]) => <button key={key} className={status === key ? 'active' : ''} onClick={() => setStatus(key)}>{label}</button>)}</div>{loading ? <div className="center-loading"><LoaderCircle className="spin"/> 正在读取项目…</div> : <div className="operations-project-list">{projects.map((project) => <article className="account-card" key={project.id}><span className={`project-status ${project.status}`}>{projectStatus[project.status]}</span><div><h3>{project.title}</h3><p>{project.username} · {project.user_email}</p><small>{project.category} · {project.current_round} 轮 · 更新于 {new Date(project.updated_at).toLocaleString()}</small></div><strong>{project.final_name || '尚未选名'}</strong></article>)}</div>}</main>
}

const expertOrderStatus = { submitted: '待接单', accepted: '服务中', delivered: '已交付', completed: '已完成' }

function ExpertsPage({ session, notify, go }) {
  const [packages, setPackages] = useState([]), [orders, setOrders] = useState([]), [profile, setProfile] = useState(null), [projects, setProjects] = useState([]), [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState(null), [projectId, setProjectId] = useState(''), [requirement, setRequirement] = useState(''), [reviewing, setReviewing] = useState(null), [rating, setRating] = useState(5), [comment, setComment] = useState('')
  const [application, setApplication] = useState({ display_name:'', title:'', specialties:'', bio:'', experience_years:0, portfolio:'' })
  const load = () => Promise.all([api.expertPackages(), api.expertProfile(), api.expertCustomerOrders(), api.projects()]).then(([p,pr,o,ps]) => { setPackages(p); setProfile(pr); setOrders(o); setProjects(ps) }).catch((e) => notify(e.message,'error')).finally(() => setLoading(false))
  useEffect(() => { load() }, [])
  const apply = async (e) => { e.preventDefault(); try { const next = await api.applyExpert({...application,experience_years:Number(application.experience_years)}); setProfile(next); notify('专家申请已提交，等待平台审核。','success') } catch(e){ notify(e.message,'error') } }
  const order = async (e) => { e.preventDefault(); try { const item = await api.createExpertOrder({ package_id:selected.id, project_id:projectId?Number(projectId):null, requirement, client_request_id:`expert:${crypto.randomUUID()}` }); setOrders((old)=>[item,...old]); setSelected(null); setRequirement(''); notify('精批订单已提交，等待专家接单。','success') } catch(e){ notify(e.message,'error') } }
  const review = async (e) => { e.preventDefault(); try { const item=await api.reviewExpertOrder(reviewing.id,{rating:Number(rating),content:comment}); setOrders((old)=>old.map((v)=>v.id===item.id?item:v)); setReviewing(null); setComment(''); notify('评价已提交，订单完成。','success') } catch(e){ notify(e.message,'error') } }
  if (loading) return <main className="page-shell wrap"><div className="center-loading"><LoaderCircle className="spin"/> 正在读取专家服务…</div></main>
  return <main className="page-shell wrap"><div className="page-title"><span className="eyebrow"><Star size={14}/> 专家服务</span><h1>让专业命名师，再为你精批一遍</h1><p>选择认证专家套餐，关联命名项目，获得一对一文字交付与专业建议。</p></div><section className="expert-market-grid">{packages.map((item)=><article className="account-card" key={item.id}><div className="expert-card-head"><Star/><div><h3>{item.expert_name}</h3><p>{item.expert_title}</p></div><span>{Number(item.expert_rating).toFixed(1)} ★ · {item.expert_rating_count} 评</span></div><h2>{item.name}</h2><p>{item.description}</p><div className="expert-package-meta"><span>{item.delivery_days} 天交付</span><span>{item.revision_count} 次修改</span><b>¥{Number(item.price).toFixed(2)}</b></div><button className="red-button wide" onClick={()=>setSelected(item)}>选择专家</button></article>)}</section>{!packages.length&&<div className="empty-state standalone"><Star/><h3>专家套餐正在准备中</h3><p>你也可以先提交专家入驻申请。</p></div>}<section className="expert-columns"><div className="account-card"><div className="account-card-title"><Star/><div><h3>专家入驻</h3><p>提交专业背景，由平台审核认证</p></div></div>{profile ? <div className="expert-application-state"><span className={`knowledge-status ${profile.status==='approved'?'completed':profile.status==='rejected'?'failed':'queued'}`}>{profile.status==='approved'?'已认证':profile.status==='rejected'?'未通过':'审核中'}</span><h3>{profile.display_name} · {profile.title}</h3><p>{profile.bio}</p>{profile.review_note&&<small>审核意见：{profile.review_note}</small>}{profile.status==='approved'&&<button className="outline-button" onClick={()=>go('expert-workspace')}>进入专家工作台</button>}{profile.status==='rejected'&&<button className="outline-button" onClick={()=>{setApplication({display_name:profile.display_name,title:profile.title,specialties:profile.specialties,bio:profile.bio,experience_years:profile.experience_years,portfolio:profile.portfolio});setProfile(null)}}>修改资料并重新申请</button>}</div> : <form onSubmit={apply}><input required placeholder="专家展示名" value={application.display_name} onChange={(e)=>setApplication({...application,display_name:e.target.value})}/><input required placeholder="专业头衔" value={application.title} onChange={(e)=>setApplication({...application,title:e.target.value})}/><input placeholder="擅长领域，如企业命名、诗词人名" value={application.specialties} onChange={(e)=>setApplication({...application,specialties:e.target.value})}/><input type="number" min="0" max="80" placeholder="从业年限" value={application.experience_years} onChange={(e)=>setApplication({...application,experience_years:e.target.value})}/><textarea required minLength="20" rows="5" placeholder="专业经历与服务理念" value={application.bio} onChange={(e)=>setApplication({...application,bio:e.target.value})}/><textarea rows="3" placeholder="代表案例（可选）" value={application.portfolio} onChange={(e)=>setApplication({...application,portfolio:e.target.value})}/><button className="outline-button">提交入驻申请</button></form>}</div><div className="account-card"><div className="account-card-title"><FileText/><div><h3>我的精批订单</h3><p>查看接单、交付和评价状态</p></div></div><div className="expert-order-list">{orders.map((item)=><article key={item.id}><span className={`knowledge-status ${item.status}`}>{expertOrderStatus[item.status]}</span><h3>{item.package_name} · {item.expert_name}</h3><p>{item.requirement}</p><small>{item.order_no} · ¥{Number(item.amount).toFixed(2)}</small>{item.delivery&&<div className="expert-delivery"><b>{item.delivery.title}</b><p>{item.delivery.content}</p></div>}{item.status==='delivered'&&<button className="red-button" onClick={()=>setReviewing(item)}>确认并评价</button>}{item.review&&<small>我的评分：{item.review.rating} ★ · {item.review.content}</small>}</article>)}</div></div></section>{selected&&<div className="modal-backdrop"><form className="order-detail-modal" onSubmit={order}><button type="button" className="modal-close" onClick={()=>setSelected(null)}><X/></button><h2>提交专家精批订单</h2><p>{selected.expert_name} · {selected.name} · ¥{Number(selected.price).toFixed(2)}</p><label className="field"><span>关联命名项目 <small>可选</small></span><select value={projectId} onChange={(e)=>setProjectId(e.target.value)}><option value="">不关联项目</option>{projects.map((p)=><option value={p.id} key={p.id}>{p.title}</option>)}</select></label><label className="field"><span>精批需求</span><textarea required minLength="20" rows="7" value={requirement} onChange={(e)=>setRequirement(e.target.value)} placeholder="说明使用场景、偏好、顾虑和希望专家重点分析的内容…"/></label><button className="red-button wide">确认提交</button></form></div>}{reviewing&&<div className="modal-backdrop"><form className="order-detail-modal" onSubmit={review}><button type="button" className="modal-close" onClick={()=>setReviewing(null)}><X/></button><h2>确认交付并评价</h2><label className="field"><span>评分</span><select value={rating} onChange={(e)=>setRating(e.target.value)}>{[5,4,3,2,1].map((v)=><option value={v} key={v}>{v} 星</option>)}</select></label><label className="field"><span>评价内容</span><textarea rows="5" maxLength="1000" value={comment} onChange={(e)=>setComment(e.target.value)}/></label><button className="red-button wide">提交评价并完成订单</button></form></div>}</main>
}

function ExpertWorkspacePage({ notify }) {
  const [packages,setPackages]=useState([]),[orders,setOrders]=useState([]),[settlements,setSettlements]=useState([]),[draft,setDraft]=useState({name:'',description:'',price:'',delivery_days:7,revision_count:1}),[delivery,setDelivery]=useState(null)
  const load=()=>Promise.all([api.ownExpertPackages(),api.expertWorkOrders(),api.expertSettlements()]).then(([p,o,s])=>{setPackages(p);setOrders(o);setSettlements(s)}).catch((e)=>notify(e.message,'error'))
  useEffect(() => { load() },[])
  const create=async(e)=>{e.preventDefault();try{await api.createExpertPackage({...draft,price:Number(draft.price),delivery_days:Number(draft.delivery_days),revision_count:Number(draft.revision_count)});setDraft({name:'',description:'',price:'',delivery_days:7,revision_count:1});await load();notify('专家套餐已发布。','success')}catch(e){notify(e.message,'error')}}
  const accept=async(id)=>{try{await api.acceptExpertOrder(id);await load()}catch(e){notify(e.message,'error')}}
  const deliver=async(e)=>{e.preventDefault();try{await api.deliverExpertOrder(delivery.id,{title:delivery.title,content:delivery.content,attachment_url:delivery.attachment_url||''});setDelivery(null);await load();notify('专家交付报告已提交。','success')}catch(e){notify(e.message,'error')}}
  return <main className="page-shell wrap"><div className="page-title"><span className="eyebrow"><Star size={14}/> 专家工作台</span><h1>服务、交付与结算</h1><p>发布服务套餐，处理用户精批订单，并跟踪每笔收入结算。</p></div><section className="expert-columns"><form className="account-card" onSubmit={create}><h2>发布服务套餐</h2><input required placeholder="套餐名称" value={draft.name} onChange={(e)=>setDraft({...draft,name:e.target.value})}/><textarea required minLength="10" rows="5" placeholder="服务内容与交付范围" value={draft.description} onChange={(e)=>setDraft({...draft,description:e.target.value})}/><div className="field-row"><input required type="number" min="0.01" step="0.01" placeholder="价格" value={draft.price} onChange={(e)=>setDraft({...draft,price:e.target.value})}/><input required type="number" min="1" placeholder="交付天数" value={draft.delivery_days} onChange={(e)=>setDraft({...draft,delivery_days:e.target.value})}/></div><input required type="number" min="0" placeholder="修改次数" value={draft.revision_count} onChange={(e)=>setDraft({...draft,revision_count:e.target.value})}/><button className="red-button">发布套餐</button><div className="expert-package-list">{packages.map((p)=><div key={p.id}><b>{p.name}</b><span>¥{Number(p.price).toFixed(2)}</span><button type="button" onClick={async()=>{await api.setExpertPackageStatus(p.id,!p.is_active);load()}}>{p.is_active?'下架':'上架'}</button></div>)}</div></form><section className="account-card"><h2>服务订单</h2><div className="expert-order-list">{orders.map((o)=><article key={o.id}><span className={`knowledge-status ${o.status}`}>{expertOrderStatus[o.status]}</span><h3>{o.customer_name} · {o.package_name}</h3><p>{o.requirement}</p>{o.status==='submitted'&&<button className="outline-button" onClick={()=>accept(o.id)}>确认接单</button>}{['accepted','delivered'].includes(o.status)&&<button className="red-button" onClick={()=>setDelivery({id:o.id,title:o.delivery?.title||`${o.package_name}交付报告`,content:o.delivery?.content||'',attachment_url:o.delivery?.attachment_url||''})}>{o.status==='delivered'?'更新交付':'提交交付'}</button>}</article>)}</div></section></section><section className="account-card expert-settlements"><h2>结算记录</h2>{settlements.map((s)=><article key={s.id}><span className={`knowledge-status ${s.status==='settled'?'completed':'queued'}`}>{s.status==='settled'?'已结算':'待结算'}</span><b>{s.order_no}</b><span>订单 ¥{Number(s.gross_amount).toFixed(2)} - 服务费 ¥{Number(s.platform_fee).toFixed(2)}</span><strong>应结 ¥{Number(s.net_amount).toFixed(2)}</strong></article>)}</section>{delivery&&<div className="modal-backdrop"><form className="order-detail-modal" onSubmit={deliver}><button type="button" className="modal-close" onClick={()=>setDelivery(null)}><X/></button><h2>提交专家交付报告</h2><input required value={delivery.title} onChange={(e)=>setDelivery({...delivery,title:e.target.value})}/><textarea required minLength="50" rows="12" value={delivery.content} onChange={(e)=>setDelivery({...delivery,content:e.target.value})} placeholder="完整说明名称分析、判断依据、使用建议和风险提示…"/><input value={delivery.attachment_url} onChange={(e)=>setDelivery({...delivery,attachment_url:e.target.value})} placeholder="附件地址（可选）"/><button className="red-button wide">确认交付</button></form></div>}</main>
}

function AdminExpertsPage({ notify }) {
  const [applications,setApplications]=useState([]),[orders,setOrders]=useState([]),[settlements,setSettlements]=useState([]),[status,setStatus]=useState('')
  const load=()=>Promise.all([api.adminExpertApplications(status),api.adminExpertOrders(),api.adminExpertSettlements()]).then(([a,o,s])=>{setApplications(a);setOrders(o);setSettlements(s)}).catch((e)=>notify(e.message,'error'))
  useEffect(() => { load() },[status])
  const decide=async(id,next)=>{try{await api.adminReviewExpert(id,{status:next,review_note:next==='approved'?'资质审核通过':'资料暂不符合平台要求'});await load();notify('专家申请已处理。','success')}catch(e){notify(e.message,'error')}}
  const settle=async(id)=>{try{await api.adminSettleExpert(id);await load();notify('结算已确认。','success')}catch(e){notify(e.message,'error')}}
  return <main className="page-shell wrap"><div className="page-title"><span className="eyebrow"><Star size={14}/> 运营后台</span><h1>专家服务管理</h1><p>审核专家资质、查看精批订单并确认专家结算。</p></div><div className="project-filters">{[['','全部申请'],['pending','待审核'],['approved','已通过'],['rejected','未通过']].map(([k,l])=><button key={k} className={status===k?'active':''} onClick={()=>setStatus(k)}>{l}</button>)}</div><section className="expert-admin-list">{applications.map((a)=><article className="account-card" key={a.id}><span className={`knowledge-status ${a.status==='approved'?'completed':a.status==='rejected'?'failed':'queued'}`}>{a.status}</span><div><h3>{a.display_name} · {a.title}</h3><p>{a.username} · {a.user_email}</p><small>{a.experience_years} 年经验 · {a.specialties}</small></div><p>{a.bio}</p>{a.status==='pending'&&<div className="order-actions"><button className="red-button" onClick={()=>decide(a.id,'approved')}>通过</button><button className="outline-button" onClick={()=>decide(a.id,'rejected')}>拒绝</button></div>}</article>)}</section><section className="expert-columns"><div className="account-card"><h2>全部精批订单</h2><div className="expert-order-list">{orders.map((o)=><article key={o.id}><span>{expertOrderStatus[o.status]}</span><b>{o.order_no}</b><p>{o.customer_name} → {o.expert_name} · ¥{Number(o.amount).toFixed(2)}</p></article>)}</div></div><div className="account-card"><h2>专家结算</h2><div className="expert-order-list">{settlements.map((s)=><article key={s.id}><span>{s.status==='settled'?'已结算':'待结算'}</span><b>{s.expert_name} · ¥{Number(s.net_amount).toFixed(2)}</b><p>{s.order_no} · 平台服务费 ¥{Number(s.platform_fee).toFixed(2)}</p>{s.status==='pending'&&<button className="red-button" onClick={()=>settle(s.id)}>确认结算</button>}</article>)}</div></div></section></main>
}

function CommunityPage({ notify, go }) {
  const [polls,setPolls]=useState([]),[filter,setFilter]=useState(''),[loading,setLoading]=useState(true)
  const load=()=>api.communityPolls(filter).then(setPolls).catch((e)=>notify(e.message,'error')).finally(()=>setLoading(false))
  useEffect(() => { load() },[filter])
  return <main className="page-shell wrap"><div className="page-title"><span className="eyebrow"><Vote size={14}/> 社区众包</span><h1>让更多人，帮你选出好名字</h1><p>浏览真实命名候选，投出你的判断，也可以发布自己的项目邀请社区参与。</p></div><div className="community-toolbar"><div className="project-filters"><button className={!filter?'active':''} onClick={()=>setFilter('')}>全部投票</button><button className={filter==='featured=true'?'active':''} onClick={()=>setFilter('featured=true')}>社区精选</button><button className={filter==='mine=true'?'active':''} onClick={()=>setFilter('mine=true')}>我的发布</button></div><button className="red-button" onClick={()=>go('community-publish')}>发布命名投票</button></div>{loading?<div className="center-loading"><LoaderCircle className="spin"/> 正在读取社区投票…</div>:<section className="community-grid">{polls.map((poll)=><button className="account-card community-poll-card" key={poll.id} onClick={()=>go('community-detail',poll.id)}>{poll.is_featured&&<span className="featured-tag"><Star size={12}/> 社区精选</span>}<span className={`knowledge-status ${poll.status==='open'?'completed':'queued'}`}>{poll.status==='open'?'投票中':'已结束'}</span><h2>{poll.title}</h2><p>{poll.description||'发布者正在邀请大家从这些候选名称中做出选择。'}</p><div className="community-name-preview">{poll.candidates.slice(0,4).map((c)=><span key={c.id}>{c.name}</span>)}</div><footer><span>{poll.publisher} · {poll.category}</span><b>{poll.vote_count} 票 · {poll.comment_count} 条讨论</b></footer></button>)}</section>}{!loading&&!polls.length&&<div className="empty-state standalone"><Vote/><h3>还没有符合条件的投票</h3><p>从你的命名项目发布第一场社区共创。</p></div>}</main>
}

function CommunityPublishPage({ notify, go }) {
  const [projects,setProjects]=useState([]),[projectId,setProjectId]=useState(''),[detail,setDetail]=useState(null),[selected,setSelected]=useState([]),[title,setTitle]=useState(''),[description,setDescription]=useState('')
  useEffect(()=>{api.projects().then((items)=>setProjects(items.filter((p)=>p.current_round>0))).catch((e)=>notify(e.message,'error'))},[])
  useEffect(()=>{if(!projectId){setDetail(null);setSelected([]);return} api.project(projectId).then((item)=>{setDetail(item);const values=item.rounds.at(-1)?.candidates||[];setSelected(values.slice(0,Math.min(4,values.length)).map((v)=>v.id));setTitle(`${item.title} · 候选名称投票`)}).catch((e)=>notify(e.message,'error'))},[projectId])
  const submit=async(e)=>{e.preventDefault();try{const poll=await api.createCommunityPoll({project_id:Number(projectId),title,description,candidate_ids:selected});notify('社区投票已发布。','success');go('community-detail',poll.id)}catch(e){notify(e.message,'error')}}
  const candidates=detail?.rounds?.at(-1)?.candidates||[]
  return <main className="page-shell wrap narrow"><div className="page-title"><span className="eyebrow"><Send size={14}/> 发布投票</span><h1>邀请社区参与你的命名选择</h1><p>只会公开所选候选名称、出处和寓意，不会公开项目条件或会话记录。</p></div><form className="account-card community-publish-form" onSubmit={submit}><label className="field"><span>选择已有命名项目</span><select required value={projectId} onChange={(e)=>setProjectId(e.target.value)}><option value="">请选择已生成候选的项目</option>{projects.map((p)=><option value={p.id} key={p.id}>{p.title} · {p.category}</option>)}</select></label>{detail&&<><label className="field"><span>投票标题</span><input required minLength="4" maxLength="160" value={title} onChange={(e)=>setTitle(e.target.value)}/></label><label className="field"><span>补充说明</span><textarea rows="5" maxLength="3000" value={description} onChange={(e)=>setDescription(e.target.value)} placeholder="介绍使用场景，以及你最希望大家关注的判断维度…"/></label><div><b>选择候选名称 <small>至少 2 个，最多 12 个</small></b><div className="community-candidate-picker">{candidates.map((c)=><label className={selected.includes(c.id)?'selected':''} key={c.id}><input type="checkbox" checked={selected.includes(c.id)} onChange={()=>setSelected((old)=>old.includes(c.id)?old.filter((id)=>id!==c.id):old.length<12?[...old,c.id]:old)}/><strong>{c.name}</strong><span>{c.moral}</span></label>)}</div></div><button className="red-button wide" disabled={selected.length<2}>确认发布社区投票</button></>}</form></main>
}

function CommunityDetailPage({ notify, pollId, go }) {
  const [poll,setPoll]=useState(null),[comment,setComment]=useState('')
  const load=()=>api.communityPoll(pollId).then(setPoll).catch((e)=>{notify(e.message,'error');go('community')})
  useEffect(() => { load() },[pollId])
  const vote=async(id)=>{try{setPoll(await api.voteCommunityPoll(poll.id,id));notify('你的选择已计入投票。','success')}catch(e){notify(e.message,'error')}}
  const addComment=async(e)=>{e.preventDefault();try{setPoll(await api.commentCommunityPoll(poll.id,comment));setComment('')}catch(e){notify(e.message,'error')}}
  const report=async(type,id)=>{const reason=prompt('请简要说明举报原因（至少 5 个字）');if(!reason)return;try{await api.reportCommunityContent({target_type:type,target_id:id,reason});notify('举报已提交，运营人员会尽快处理。','success')}catch(e){notify(e.message,'error')}}
  const close=async()=>{if(!confirm('结束后将不能继续投票或评论，确定结束吗？'))return;try{setPoll(await api.closeCommunityPoll(poll.id));notify('投票已结束。','success')}catch(e){notify(e.message,'error')}}
  if(!poll)return <main className="page-shell wrap"><div className="center-loading"><LoaderCircle className="spin"/> 正在读取投票…</div></main>
  return <main className="page-shell wrap narrow"><button className="auth-back" onClick={()=>go('community')}><ChevronRight/> 返回社区</button><section className="community-detail-head"><div>{poll.is_featured&&<span className="featured-tag"><Star size={12}/> 社区精选</span>}<h1>{poll.title}</h1><p>{poll.description}</p><small>{poll.publisher} · {poll.category} · {new Date(poll.created_at).toLocaleString()}</small></div><div className="order-actions">{poll.can_manage&&poll.status==='open'&&<button className="outline-button" onClick={close}>结束投票</button>}{!poll.can_manage&&<button className="danger-link" onClick={()=>report('poll',poll.id)}><Flag size={13}/> 举报</button>}</div></section><section className="community-vote-list">{poll.candidates.map((c)=><article className={`account-card ${poll.my_candidate_id===c.id?'chosen':''}`} key={c.id}><div><h2>{c.name}</h2><p>{c.reference}</p><span>{c.moral}</span></div><div className="vote-meter"><span style={{width:`${c.vote_percent}%`}}/><b>{c.vote_count} 票 · {c.vote_percent}%</b></div>{poll.status==='open'&&<button className={poll.my_candidate_id===c.id?'outline-button':'red-button'} onClick={()=>vote(c.id)}>{poll.my_candidate_id===c.id?'已选择':'投给它'}</button>}</article>)}</section><section className="account-card community-comments"><h2>评论讨论 · {poll.comment_count}</h2>{poll.status==='open'&&<form onSubmit={addComment}><textarea required minLength="2" maxLength="1000" value={comment} onChange={(e)=>setComment(e.target.value)} placeholder="说说你更喜欢哪个名字，以及判断理由…"/><button className="red-button">发表评论</button></form>}<div>{poll.comments.map((c)=><article key={c.id}><div><b>{c.username}</b><small>{new Date(c.created_at).toLocaleString()}</small></div><p>{c.content}</p><button onClick={()=>report('comment',c.id)}>举报</button></article>)}</div></section></main>
}

function AdminCommunityPage({ notify }) {
  const [reports,setReports]=useState([]),[polls,setPolls]=useState([]),[status,setStatus]=useState('pending')
  const load=()=>Promise.all([api.adminCommunityReports(status),api.communityPolls()]).then(([r,p])=>{setReports(r);setPolls(p)}).catch((e)=>notify(e.message,'error'))
  useEffect(() => { load() },[status])
  const moderate=async(id,action)=>{try{await api.moderateCommunityReport(id,{action,resolution:action==='hide'?'核查后确认违规，内容已隐藏':'核查后未发现违规，举报已驳回'});await load();notify('举报已处理。','success')}catch(e){notify(e.message,'error')}}
  const feature=async(poll)=>{try{await api.featureCommunityPoll(poll.id,!poll.is_featured);await load()}catch(e){notify(e.message,'error')}}
  return <main className="page-shell wrap"><div className="page-title"><span className="eyebrow"><ShieldCheck size={14}/> 运营后台</span><h1>社区内容管理</h1><p>维护社区精选，核查用户举报并隐藏违规投票或评论。</p></div><section className="expert-columns"><div><h2>社区投票与精选</h2><div className="community-admin-polls">{polls.map((p)=><article className="account-card" key={p.id}><div><b>{p.title}</b><p>{p.publisher} · {p.vote_count} 票 · {p.comment_count} 评论</p></div><button className={p.is_featured?'outline-button':'red-button'} onClick={()=>feature(p)}>{p.is_featured?'取消精选':'设为精选'}</button></article>)}</div></div><div><h2>内容举报</h2><div className="project-filters">{[['pending','待处理'],['resolved','已处理'],['dismissed','已驳回']].map(([k,l])=><button className={status===k?'active':''} onClick={()=>setStatus(k)} key={k}>{l}</button>)}</div><div className="community-report-list">{reports.map((r)=><article className="account-card" key={r.id}><span>{r.target_type==='poll'?'投票':'评论'} #{r.target_id}</span><h3>{r.reason}</h3><p>举报人：{r.reporter}</p>{r.status==='pending'?<div className="order-actions"><button className="red-button" onClick={()=>moderate(r.id,'hide')}>确认违规并隐藏</button><button className="outline-button" onClick={()=>moderate(r.id,'dismiss')}>驳回举报</button></div>:<small>{r.resolution}</small>}</article>)}</div></div></section></main>
}

function DevelopersPage({ notify }) {
  const [account,setAccount]=useState(undefined),[keys,setKeys]=useState([]),[plans,setPlans]=useState([]),[subs,setSubs]=useState([]),[usage,setUsage]=useState([]),[summary,setSummary]=useState(null),[loadError,setLoadError]=useState(''),[revealed,setRevealed]=useState(null),[keyName,setKeyName]=useState('生产环境 Key')
  const [form,setForm]=useState({company_name:'',contact_name:'',use_case:''})
  const load=()=>{setLoadError('');return Promise.all([api.developerAccount(),api.apiPlans(),api.apiSubscriptions(),api.apiUsage(),api.apiUsageSummary()]).then(async([a,p,s,u,m])=>{setAccount(a);setPlans(p);setSubs(s);setUsage(u);setSummary(m);setKeys(a?await api.developerKeys():[])}).catch((e)=>{setLoadError(e.message);notify(e.message,'error')})}
  useEffect(() => { load() },[])
  const createAccount=async(e)=>{e.preventDefault();try{await api.createDeveloperAccount(form);await load();notify('开发者账号已开通。','success')}catch(e){notify(e.message,'error')}}
  const createKey=async(e)=>{e.preventDefault();try{const item=await api.createDeveloperKey(keyName);setRevealed(item.api_key);await load()}catch(e){notify(e.message,'error')}}
  const revoke=async(id)=>{if(!confirm('撤销后使用该 Key 的系统会立即无法调用，确定吗？'))return;try{await api.revokeDeveloperKey(id);await load()}catch(e){notify(e.message,'error')}}
  const subscribe=async(id)=>{try{await api.subscribeApiPlan(id);await load();notify('体验额度已到账。','success')}catch(e){notify(e.message,'error')}}
  if(account===undefined&&loadError)return <PageLoadError title="开放平台加载失败" message={loadError} retry={load}/>
  if(account===undefined)return <main className="page-shell wrap"><div className="center-loading"><LoaderCircle className="spin"/> 正在读取开放平台…</div></main>
  if(!account)return <main className="page-shell wrap narrow"><div className="page-title"><span className="eyebrow"><KeyRound size={14}/> B 端开放平台</span><h1>把智能命名能力，接入你的产品</h1><p>开通开发者账号后，可以创建 API Key、领取体验额度并调用单次或批量命名接口。</p></div><form className="account-card developer-onboarding" onSubmit={createAccount}><input required placeholder="公司或团队名称" value={form.company_name} onChange={(e)=>setForm({...form,company_name:e.target.value})}/><input required placeholder="联系人" value={form.contact_name} onChange={(e)=>setForm({...form,contact_name:e.target.value})}/><textarea required minLength="10" rows="6" placeholder="说明接入场景和预计用途" value={form.use_case} onChange={(e)=>setForm({...form,use_case:e.target.value})}/><button className="red-button">开通开发者账号</button></form></main>
  return <main className="page-shell wrap"><div className="page-title"><span className="eyebrow"><KeyRound size={14}/> B 端开放平台</span><h1>{account.company_name} · 开发者控制台</h1><p>管理调用凭证、套餐额度和 API 使用记录。</p></div><section className="developer-summary"><article><BarChart3/><b>{summary?.calls_total||0}</b><span>请求总数</span></article><article><Coins/><b>{summary?.units_total||0}</b><span>计费单位</span></article><article><Check/><b>{summary?.success_total||0}</b><span>成功调用</span></article><article><Flag/><b>{summary?.failed_total||0}</b><span>失败调用</span></article></section>{revealed&&<div className="developer-secret"><ShieldCheck/><div><b>请立即复制并安全保存，关闭后无法再次查看</b><code>{revealed}</code></div><button onClick={()=>navigator.clipboard.writeText(revealed)}>复制 Key</button><button onClick={()=>setRevealed(null)}>我已保存</button></div>}<section className="developer-grid"><div className="account-card"><h2>API Key</h2><form className="developer-key-form" onSubmit={createKey}><input required value={keyName} onChange={(e)=>setKeyName(e.target.value)}/><button className="red-button">创建 Key</button></form>{keys.map((k)=><article className="developer-key" key={k.id}><div><b>{k.name}</b><code>{k.key_prefix}••••••••</code><small>{k.last_used_at?`最后调用 ${new Date(k.last_used_at).toLocaleString()}`:'尚未调用'}</small></div><span>{k.status==='active'?'有效':'已撤销'}</span>{k.status==='active'&&<button className="danger-link" onClick={()=>revoke(k.id)}>撤销</button>}</article>)}</div><div className="account-card"><h2>API 套餐与余额</h2>{subs.map((s)=><article className="developer-subscription" key={s.id}><b>{s.plan_name}</b><strong>{s.quota_remaining}</strong><span>剩余额度 / {s.quota_total}</span><div><i style={{width:`${Math.min(100,s.quota_used*100/s.quota_total)}%`}}/></div><small>有效期至 {new Date(s.expires_at).toLocaleDateString()}</small></article>)}{plans.map((p)=><article className="developer-plan" key={p.id}><div><b>{p.name}</b><p>{p.description}</p></div><strong>{Number(p.price)===0?'免费':`¥${Number(p.price).toFixed(2)}`}</strong>{Number(p.price)===0?<button className="outline-button" onClick={()=>subscribe(p.id)}>领取</button>:<span>联系管理员开通</span>}</article>)}</div></section><section className="account-card developer-docs"><h2>快速接入</h2><pre>{`curl -X POST /api/openapi/v1/names/generate \\\n  -H "X-API-Key: qmk_live_xxx" \\\n  -H "Content-Type: application/json" \\\n  -d '{"request_id":"your-unique-id","category":"企业名","surname":"","gender":"不限","length":"两字","other":"科技品牌","exclude":[]}'`}</pre><p>批量接口：<code>POST /api/openapi/v1/names/batch</code>，每批最多 10 个任务，按任务数扣减额度。相同 Key 与 request_id 会返回原响应且不重复计费。</p></section><section className="account-card"><h2>调用记录</h2><div className="developer-usage">{usage.map((u)=><article key={u.id}><span className={`knowledge-status ${u.status==='success'?'completed':'failed'}`}>{u.status==='success'?'成功':'失败'}</span><code>{u.endpoint}</code><b>{u.units} 单位</b><span>{u.latency_ms} ms</span><small>{new Date(u.created_at).toLocaleString()} · {u.request_id}</small></article>)}</div></section></main>
}

function AdminDevelopersPage({ notify }) {
  const [developers,setDevelopers]=useState([]),[plans,setPlans]=useState([]),[draft,setDraft]=useState({name:'',description:'',price:'',quota_calls:1000,validity_days:365}),[grant,setGrant]=useState({})
  const load=()=>Promise.all([api.adminDevelopers(),api.apiPlans()]).then(([d,p])=>{setDevelopers(d);setPlans(p)}).catch((e)=>notify(e.message,'error'))
  useEffect(() => { load() },[])
  const create=async(e)=>{e.preventDefault();try{await api.createApiPlan({...draft,price:Number(draft.price),quota_calls:Number(draft.quota_calls),validity_days:Number(draft.validity_days)});setDraft({name:'',description:'',price:'',quota_calls:1000,validity_days:365});await load();notify('API 套餐已创建。','success')}catch(e){notify(e.message,'error')}}
  const grantPlan=async(id)=>{if(!grant[id])return;try{await api.grantApiPlan(id,Number(grant[id]));notify('API 额度已授予。','success')}catch(e){notify(e.message,'error')}}
  const toggle=async(item)=>{try{await api.setDeveloperStatus(item.id,item.status==='active'?'suspended':'active');await load();notify(item.status==='active'?'开发者账号已停用，所有有效 Key 已撤销。':'开发者账号已恢复。','success')}catch(e){notify(e.message,'error')}}
  return <main className="page-shell wrap"><div className="page-title"><span className="eyebrow"><KeyRound size={14}/> 运营后台</span><h1>开放平台管理</h1><p>管理开发者账号、合同套餐和 API 调用额度。</p></div><section className="expert-columns"><form className="account-card" onSubmit={create}><h2>创建 API 套餐</h2><input required placeholder="套餐名称" value={draft.name} onChange={(e)=>setDraft({...draft,name:e.target.value})}/><textarea maxLength="500" placeholder="套餐说明" value={draft.description} onChange={(e)=>setDraft({...draft,description:e.target.value})}/><div className="field-row"><input required type="number" min="0" step="0.01" placeholder="价格" value={draft.price} onChange={(e)=>setDraft({...draft,price:e.target.value})}/><input required type="number" min="1" placeholder="调用额度" value={draft.quota_calls} onChange={(e)=>setDraft({...draft,quota_calls:e.target.value})}/></div><input required type="number" min="1" placeholder="有效天数" value={draft.validity_days} onChange={(e)=>setDraft({...draft,validity_days:e.target.value})}/><button className="red-button">创建套餐</button></form><section><h2>开发者账号</h2><div className="developer-admin-list">{developers.map((d)=><article className="account-card" key={d.id}><div><b>{d.company_name}</b><p>{d.username} · {d.email}</p><small>{d.contact_name} · {d.use_case}</small></div><select value={grant[d.id]||''} onChange={(e)=>setGrant({...grant,[d.id]:e.target.value})}><option value="">选择授予套餐</option>{plans.map((p)=><option value={p.id} key={p.id}>{p.name} · {p.quota_calls} 次</option>)}</select><div className="order-actions"><button className="outline-button" onClick={()=>grantPlan(d.id)}>授予额度</button><button className="danger-link" onClick={()=>toggle(d)}>{d.status==='active'?'停用':'恢复'}</button></div></article>)}</div></section></section></main>
}

function GrowthPage({ notify }) {
  const [promotion,setPromotion]=useState(null),[referrals,setReferrals]=useState([]),[rewards,setRewards]=useState([]),[commissions,setCommissions]=useState([]),[loadError,setLoadError]=useState('')
  const load=()=>{setLoadError('');return Promise.all([api.growthPromotion(),api.growthReferrals(),api.growthRewards(),api.growthCommissions()]).then(([p,r,w,c])=>{setPromotion(p);setReferrals(r);setRewards(w);setCommissions(c)}).catch((e)=>{setLoadError(e.message);notify(e.message,'error')})}
  useEffect(() => { load() },[])
  const copy=async(value)=>{try{await navigator.clipboard.writeText(value);notify('邀请信息已复制。','success')}catch{notify('复制失败，请手动复制。','error')}}
  if(!promotion&&loadError)return <PageLoadError title="邀请权益加载失败" message={loadError} retry={load}/>
  if(!promotion)return <main className="page-shell wrap"><div className="center-loading"><LoaderCircle className="spin"/> 正在读取邀请权益…</div></main>
  return <main className="page-shell wrap"><div className="page-title"><span className="eyebrow"><Zap size={14}/> 增长与分销</span><h1>邀请好友，一起创造好名字</h1><p>好友通过你的专属链接注册后，双方可获得活动奖励；好友成功购买套餐时会形成佣金记录。</p></div><section className="growth-hero"><div><span>我的推广码</span><strong>{promotion.code}</strong><button onClick={()=>copy(promotion.code)}>复制推广码</button></div><div><span>邀请链接</span><code>{promotion.invite_url}</code><button onClick={()=>copy(promotion.invite_url)}>复制链接</button></div></section><section className="growth-stats"><article><Users/><b>{promotion.invited_count}</b><span>成功邀请</span></article><article><Coins/><b>{promotion.reward_credits}</b><span>奖励次数</span></article><article><Crown/><b>¥{Number(promotion.commission_available).toFixed(2)}</b><span>可用佣金记录</span></article></section><section className="expert-columns"><div className="account-card"><h2>邀请好友</h2><div className="growth-list">{referrals.map((r)=><article key={r.id}><UserRound/><div><b>{r.username}</b><small>{new Date(r.created_at).toLocaleString()}</small></div></article>)}</div>{!referrals.length&&<p className="muted-copy">还没有好友通过你的推广码注册。</p>}</div><div className="account-card"><h2>次数奖励</h2><div className="growth-list">{rewards.map((r)=><article key={r.id}><Coins/><div><b>+{r.credit_count} 次</b><small>{r.beneficiary_type==='inviter'?'邀请好友奖励':'受邀注册奖励'} · {new Date(r.created_at).toLocaleString()}</small></div></article>)}</div></div></section><section className="account-card growth-commission"><h2>佣金记录</h2>{commissions.map((c)=><article key={c.id}><span className={`knowledge-status ${c.status==='available'?'completed':'failed'}`}>{c.status==='available'?'可结算':'已冲销'}</span><div><b>{c.invitee_name} · {c.order_no}</b><small>订单 ¥{Number(c.order_amount).toFixed(2)} · 比例 {(Number(c.commission_rate)*100).toFixed(1)}%</small></div><strong>¥{Number(c.commission_amount).toFixed(2)}</strong></article>)}</section><p className="growth-note">佣金仅形成平台内部核算记录，实际提现与税务结算将在合规结算能力接入后开放；退款订单会自动冲销对应佣金。</p></main>
}

function AdminGrowthPage({ notify }) {
  const [campaigns,setCampaigns]=useState([]),[commissions,setCommissions]=useState([]),[draft,setDraft]=useState({name:'',description:'',inviter_reward:1,invitee_reward:1,commission_rate:0.1,starts_at:'',ends_at:''})
  const load=()=>Promise.all([api.growthCampaigns(),api.adminGrowthCommissions()]).then(([a,c])=>{setCampaigns(a);setCommissions(c)}).catch((e)=>notify(e.message,'error'))
  useEffect(() => { load() },[])
  const create=async(e)=>{e.preventDefault();try{await api.createGrowthCampaign({...draft,inviter_reward:Number(draft.inviter_reward),invitee_reward:Number(draft.invitee_reward),commission_rate:Number(draft.commission_rate),starts_at:new Date(draft.starts_at).toISOString(),ends_at:new Date(draft.ends_at).toISOString()});await load();notify('增长活动已创建。','success')}catch(e){notify(e.message,'error')}}
  const toggle=async(c)=>{try{await api.setGrowthCampaignStatus(c.id,!c.is_active);await load()}catch(e){notify(e.message,'error')}}
  return <main className="page-shell wrap"><div className="page-title"><span className="eyebrow"><Zap size={14}/> 运营后台</span><h1>增长活动管理</h1><p>配置邀请双方奖励与一层推广佣金，查看支付和退款产生的佣金状态。</p></div><section className="expert-columns"><form className="account-card" onSubmit={create}><h2>创建邀请活动</h2><input required placeholder="活动名称" value={draft.name} onChange={(e)=>setDraft({...draft,name:e.target.value})}/><textarea maxLength="500" placeholder="活动说明" value={draft.description} onChange={(e)=>setDraft({...draft,description:e.target.value})}/><div className="field-row"><input required type="number" min="0" placeholder="邀请人奖励次数" value={draft.inviter_reward} onChange={(e)=>setDraft({...draft,inviter_reward:e.target.value})}/><input required type="number" min="0" placeholder="受邀人奖励次数" value={draft.invitee_reward} onChange={(e)=>setDraft({...draft,invitee_reward:e.target.value})}/></div><input required type="number" min="0" max="0.5" step="0.0001" placeholder="佣金比例，如 0.1" value={draft.commission_rate} onChange={(e)=>setDraft({...draft,commission_rate:e.target.value})}/><div className="field-row"><input required type="datetime-local" value={draft.starts_at} onChange={(e)=>setDraft({...draft,starts_at:e.target.value})}/><input required type="datetime-local" value={draft.ends_at} onChange={(e)=>setDraft({...draft,ends_at:e.target.value})}/></div><button className="red-button">创建活动</button></form><section><h2>活动列表</h2><div className="growth-campaign-list">{campaigns.map((c)=><article className="account-card" key={c.id}><div><b>{c.name}</b><p>双方奖励 {c.inviter_reward}/{c.invitee_reward} 次 · 佣金 {(Number(c.commission_rate)*100).toFixed(1)}%</p><small>{new Date(c.starts_at).toLocaleString()} — {new Date(c.ends_at).toLocaleString()}</small></div><button className={c.is_active?'outline-button':'red-button'} onClick={()=>toggle(c)}>{c.is_active?'停用':'启用'}</button></article>)}</div></section></section><section className="account-card growth-commission"><h2>全平台佣金记录</h2>{commissions.map((c)=><article key={c.id}><span className={`knowledge-status ${c.status==='available'?'completed':'failed'}`}>{c.status}</span><div><b>{c.invitee_name} · {c.order_no}</b><small>订单 ¥{Number(c.order_amount).toFixed(2)} · {(Number(c.commission_rate)*100).toFixed(1)}%</small></div><strong>¥{Number(c.commission_amount).toFixed(2)}</strong></article>)}</section></main>
}

function AdminCreditsPage({ notify }) {
  const [accounts, setAccounts] = useState([]), [loading, setLoading] = useState(true), [saving, setSaving] = useState(null)
  const [forms, setForms] = useState({})
  const load = () => { setLoading(true); api.adminCreditAccounts().then(setAccounts).catch((e) => notify(e.message, 'error')).finally(() => setLoading(false)) }
  useEffect(() => { load() }, [])
  const update = (id, key, value) => setForms((old) => ({ ...old, [id]: { change_count: '', remark: '', ...(old[id] || {}), [key]: value } }))
  const submit = async (account) => {
    const form = forms[account.user_id] || {}; const count = Number(form.change_count)
    if (!Number.isInteger(count) || count === 0 || !form.remark?.trim()) return notify('请填写非零整数和调整原因。', 'error')
    setSaving(account.user_id)
    try {
      const next = await api.adjustCredit(account.user_id, { change_count: count, remark: form.remark.trim(), operation_id: `admin:${crypto.randomUUID()}` })
      setAccounts((old) => old.map((item) => item.user_id === next.user_id ? next : item)); setForms((old) => ({ ...old, [account.user_id]: { change_count: '', remark: '' } })); notify('次数调整已完成并记录审计日志。', 'success')
    } catch(e) { notify(e.message, 'error') } finally { setSaving(null) }
  }
  if (loading) return <main className="page-shell wrap"><div className="center-loading"><LoaderCircle className="spin"/> 正在读取次数账户…</div></main>
  return <main className="page-shell wrap narrow"><div className="page-title"><span className="eyebrow"><Coins size={14}/> 运营后台</span><h1>次数权益管理</h1><p>手工增加或扣减用户次数；操作会同时进入次数流水和管理员审计日志。</p></div><section className="account-card account-wide"><div className="admin-credit-list">{accounts.map((account) => <article key={account.user_id}><div><h3>{account.username}</h3><p>{account.email}</p><span>余额 <b>{account.balance}</b> · 已使用 {account.total_used} · 已充值 {account.total_recharge}</span></div><div className="admin-credit-form"><input type="number" placeholder="如 5 或 -2" value={forms[account.user_id]?.change_count || ''} onChange={(e) => update(account.user_id, 'change_count', e.target.value)}/><input placeholder="调整原因" maxLength="200" value={forms[account.user_id]?.remark || ''} onChange={(e) => update(account.user_id, 'remark', e.target.value)}/><button className="red-button" disabled={saving === account.user_id} onClick={() => submit(account)}>{saving === account.user_id ? <LoaderCircle className="spin"/> : '确认调整'}</button></div></article>)}</div></section></main>
}

function PricingPage({ session, openAuth, notify }) {
  const [packages, setPackages] = useState([]), [loading, setLoading] = useState(true), [buying, setBuying] = useState(null)
  useEffect(() => { api.packages().then(setPackages).catch((e) => notify(e.message, 'error')).finally(() => setLoading(false)) }, [])
  const buy = async (pkg) => { if (!session) return openAuth('login'); setBuying(pkg.id); try { const order = await api.createOrder(pkg.id, `order:${crypto.randomUUID()}`); window.location.href = order.pay_url } catch(e) { notify(e.message, 'error'); setBuying(null) } }
  return <main className="page-shell wrap narrow"><div className="page-title"><span className="eyebrow"><Crown size={14}/> 灵感补给</span><h1>为下一次好名字续上灵感</h1><p>每次首次生成消耗 1 次额度，连续反馈与精细调整不另收费。</p></div>{loading ? <div className="center-loading"><LoaderCircle className="spin"/> 正在加载套餐…</div> : packages.length ? <div className="pricing-grid">{packages.map((pkg, i) => <article className={`price-card ${i === 1 ? 'popular' : ''}`} key={pkg.id}>{i === 1 && <span className="popular-tag">更多人的选择</span>}<div className="price-icon">{i === 0 ? <Feather/> : i === 1 ? <Sparkles/> : <Crown/>}</div><h3>{pkg.name}</h3><p className="credits"><b>{pkg.credit_count}</b> 次起名额度</p>{pkg.description && <p className="package-description">{pkg.description}</p>}<div className="price"><small>¥</small><strong>{Number(pkg.price).toFixed(2)}</strong></div><ul><li><Check/>完整名字释义</li><li><Check/>支持多轮免费微调</li><li><Check/>企业名域名查询</li></ul><button className={i === 1 ? 'red-button wide' : 'outline-button wide'} onClick={() => buy(pkg)} disabled={buying === pkg.id}>{buying === pkg.id ? <LoaderCircle className="spin"/> : '选择此套餐'}</button></article>)}</div> : <div className="empty-state standalone"><Coins/><h3>暂时没有上架套餐</h3><p>请先在套餐后台创建并上架套餐。</p></div>}<div className="pricing-note"><Zap/><span>新用户注册即赠 <b>3 次</b> 免费起名额度</span></div></main>
}

function AdminPackagesPage({ notify }) {
  const empty = { name: '', description: '', price: '', credit_count: '', is_active: true, sort_order: 0 }
  const [packages, setPackages] = useState([]), [draft, setDraft] = useState(empty), [loading, setLoading] = useState(true), [saving, setSaving] = useState(null)
  const load = () => { setLoading(true); api.adminPackages().then(setPackages).catch((e) => notify(e.message, 'error')).finally(() => setLoading(false)) }
  useEffect(() => { load() }, [])
  const change = (id, key, value) => setPackages((old) => old.map((item) => item.id === id ? { ...item, [key]: value } : item))
  const create = async (e) => { e.preventDefault(); setSaving('create'); try { const item = await api.createPackage({ ...draft, price: Number(draft.price), credit_count: Number(draft.credit_count), sort_order: Number(draft.sort_order) }); setPackages((old) => [...old, item].sort((a,b) => a.sort_order-b.sort_order || a.id-b.id)); setDraft(empty); notify('套餐已创建。', 'success') } catch(e) { notify(e.message, 'error') } finally { setSaving(null) } }
  const save = async (item) => { setSaving(item.id); try { const next = await api.updatePackage(item.id, { name: item.name, description: item.description, price: Number(item.price), credit_count: Number(item.credit_count), sort_order: Number(item.sort_order) }); change(item.id, 'updated_at', next.updated_at); notify('套餐资料已保存。', 'success') } catch(e) { notify(e.message, 'error') } finally { setSaving(null) } }
  const toggle = async (item) => { setSaving(item.id); try { const next = await api.setPackageStatus(item.id, !item.is_active); setPackages((old) => old.map((value) => value.id === item.id ? next : value)); notify(next.is_active ? '套餐已上架。' : '套餐已下架。', 'success') } catch(e) { notify(e.message, 'error') } finally { setSaving(null) } }
  const remove = async (item) => { if (!confirm(`确定删除套餐“${item.name}”吗？已有订单的套餐只能下架。`)) return; setSaving(item.id); try { await api.deletePackage(item.id); setPackages((old) => old.filter((value) => value.id !== item.id)); notify('套餐已删除。', 'success') } catch(e) { notify(e.message, 'error') } finally { setSaving(null) } }
  const move = async (index, offset) => { const target = index + offset; if (target < 0 || target >= packages.length) return; const next = [...packages]; [next[index], next[target]] = [next[target], next[index]]; const ordered = next.map((item, i) => ({ ...item, sort_order: (i + 1) * 10 })); setPackages(ordered); try { await api.sortPackages(ordered.map((item) => ({ id: item.id, sort_order: item.sort_order }))) } catch(e) { notify(e.message, 'error'); load() } }
  if (loading) return <main className="page-shell wrap"><div className="center-loading"><LoaderCircle className="spin"/> 正在读取套餐…</div></main>
  return <main className="page-shell wrap"><div className="page-title"><span className="eyebrow"><Crown size={14}/> 运营后台</span><h1>套餐管理</h1><p>管理套餐价格、包含次数、展示顺序和上下架状态。</p></div><form className="package-create-form account-card" onSubmit={create}><input required maxLength="100" placeholder="套餐名称" value={draft.name} onChange={(e) => setDraft({ ...draft, name: e.target.value })}/><input maxLength="255" placeholder="套餐说明" value={draft.description} onChange={(e) => setDraft({ ...draft, description: e.target.value })}/><input required type="number" min="0.01" step="0.01" placeholder="价格" value={draft.price} onChange={(e) => setDraft({ ...draft, price: e.target.value })}/><input required type="number" min="1" placeholder="次数" value={draft.credit_count} onChange={(e) => setDraft({ ...draft, credit_count: e.target.value })}/><input type="number" min="0" placeholder="排序" value={draft.sort_order} onChange={(e) => setDraft({ ...draft, sort_order: e.target.value })}/><button className="red-button" disabled={saving === 'create'}>新增套餐</button></form><div className="package-admin-list">{packages.map((item, index) => <article className={`account-card ${item.is_active ? '' : 'package-offline'}`} key={item.id}><div className="package-order-buttons"><button onClick={() => move(index,-1)} disabled={!index}>↑</button><button onClick={() => move(index,1)} disabled={index === packages.length-1}>↓</button></div><div className="package-edit-grid"><input value={item.name} maxLength="100" onChange={(e) => change(item.id,'name',e.target.value)}/><input value={item.description} maxLength="255" placeholder="套餐说明" onChange={(e) => change(item.id,'description',e.target.value)}/><label>¥ <input type="number" min="0.01" step="0.01" value={item.price} onChange={(e) => change(item.id,'price',e.target.value)}/></label><label>次数 <input type="number" min="1" value={item.credit_count} onChange={(e) => change(item.id,'credit_count',e.target.value)}/></label><label>排序 <input type="number" min="0" value={item.sort_order} onChange={(e) => change(item.id,'sort_order',e.target.value)}/></label></div><div className="package-admin-actions"><span className={item.is_active ? 'available' : ''}>{item.is_active ? '已上架' : '已下架'}</span><button className="outline-button" onClick={() => save(item)} disabled={saving === item.id}>保存</button><button className="outline-button" onClick={() => toggle(item)} disabled={saving === item.id}>{item.is_active ? '下架' : '上架'}</button><button className="danger-link" onClick={() => remove(item)} disabled={saving === item.id}>删除</button></div></article>)}</div></main>
}

const orderStatusText = { pending: '待支付', paid: '已支付', closed: '已关闭', refunding: '退款中', refunded: '已退款' }

function OrdersPage({ notify }) {
  const [orders, setOrders] = useState([]), [loading, setLoading] = useState(true), [busy, setBusy] = useState(''), [detail, setDetail] = useState(null)
  const load = () => { setLoading(true); api.orders().then(setOrders).catch((e) => notify(e.message, 'error')).finally(() => setLoading(false)) }
  useEffect(() => { load() }, [])
  const replace = (next) => setOrders((old) => old.map((item) => item.order_no === next.order_no ? next : item))
  const sync = async (item) => { setBusy(item.order_no); try { const next = await api.syncOrder(item.order_no); replace(next); notify('订单状态已同步。', 'success') } catch(e) { notify(e.message, 'error') } finally { setBusy('') } }
  const close = async (item) => { if (!confirm('确定关闭这个待支付订单吗？')) return; setBusy(item.order_no); try { const next = await api.closeOrder(item.order_no); replace(next); notify('订单已关闭。', 'success') } catch(e) { notify(e.message, 'error') } finally { setBusy('') } }
  const pay = async (item) => { setBusy(item.order_no); try { const result = await api.continueOrderPayment(item.order_no); window.location.href = result.pay_url } catch(e) { notify(e.message, 'error'); setBusy('') } }
  const showDetail = async (item) => { setBusy(item.order_no); try { setDetail(await api.orderDetail(item.order_no)) } catch(e) { notify(e.message, 'error') } finally { setBusy('') } }
  if (loading) return <main className="page-shell wrap"><div className="center-loading"><LoaderCircle className="spin"/> 正在读取订单…</div></main>
  return <main className="page-shell wrap narrow"><div className="page-title"><span className="eyebrow"><FileText size={14}/> 用户中心</span><h1>我的订单</h1><p>查询订单状态、同步支付宝支付结果、关闭待支付订单并查看交易流水。</p></div><div className="order-list">{orders.map((item) => <article className="account-card" key={item.order_no}><div><span className={`order-status ${item.status}`}>{orderStatusText[item.status] || item.status}</span><h3>{item.package_name}</h3><p>订单号：{item.order_no}</p><small>{new Date(item.created_at).toLocaleString()}</small></div><div className="order-amount"><b>¥{Number(item.amount).toFixed(2)}</b><span>{item.credit_count} 次</span></div><div className="order-actions"><button className="outline-button" onClick={() => showDetail(item)} disabled={busy === item.order_no}>详情</button>{item.status === 'pending' && <><button className="red-button" onClick={() => pay(item)} disabled={busy === item.order_no}>继续支付</button><button className="outline-button" onClick={() => sync(item)} disabled={busy === item.order_no}>同步支付</button><button className="danger-link" onClick={() => close(item)} disabled={busy === item.order_no}>关闭</button></>}</div></article>)}</div>{detail && <div className="modal-backdrop" onMouseDown={(e) => e.target === e.currentTarget && setDetail(null)}><section className="order-detail-modal"><button className="modal-close" onClick={() => setDetail(null)}><X/></button><h2>{detail.package_name}</h2><p>订单号：{detail.order_no}</p><div className="credit-overview"><div><b>¥{Number(detail.amount).toFixed(2)}</b><span>订单金额</span></div><div><b>{detail.credit_count}</b><span>购买次数</span></div><div><b>{orderStatusText[detail.status]}</b><span>当前状态</span></div></div><h3>交易流水</h3><div className="security-list">{detail.transactions.map((tx) => <div key={tx.id}><span className={`order-status ${tx.status}`}>{tx.transaction_type === 'refund' ? '退款' : '支付'}</span><div><b>{tx.status} · ¥{Number(tx.amount).toFixed(2)}</b><span>{tx.request_no} · {new Date(tx.created_at).toLocaleString()}</span></div></div>)}</div></section></div>}</main>
}

function AdminOrdersPage({ notify }) {
  const [orders, setOrders] = useState([]), [status, setStatus] = useState(''), [loading, setLoading] = useState(true), [busy, setBusy] = useState(''), [detail, setDetail] = useState(null)
  const load = () => { setLoading(true); api.adminOrders(status).then(setOrders).catch((e) => notify(e.message, 'error')).finally(() => setLoading(false)) }
  useEffect(() => { load() }, [status])
  const refund = async (item) => { const reason = prompt('请输入退款原因'); if (!reason?.trim()) return; if (!confirm(`确认退款 ¥${Number(item.amount).toFixed(2)} 并回收 ${item.credit_count} 次权益吗？`)) return; setBusy(item.order_no); try { const next = await api.refundOrder(item.order_no, { request_no: `refund:${crypto.randomUUID()}`, reason: reason.trim() }); setOrders((old) => old.map((value) => value.order_no === next.order_no ? { ...value, ...next } : value)); notify('退款已完成。', 'success') } catch(e) { notify(e.message, 'error') } finally { setBusy('') } }
  const close = async (item) => { if (!confirm('确定由管理员关闭此订单吗？')) return; setBusy(item.order_no); try { const next = await api.adminCloseOrder(item.order_no); setOrders((old) => old.map((value) => value.order_no === next.order_no ? { ...value, ...next } : value)); notify('订单已关闭。', 'success') } catch(e) { notify(e.message, 'error') } finally { setBusy('') } }
  const showDetail = async (item) => { setBusy(item.order_no); try { setDetail(await api.adminOrderDetail(item.order_no)) } catch(e) { notify(e.message, 'error') } finally { setBusy('') } }
  return <main className="page-shell wrap"><div className="page-title"><span className="eyebrow"><FileText size={14}/> 运营后台</span><h1>订单与支付管理</h1><p>查询平台订单、支付状态、交易流水和退款结果。</p></div><div className="project-filters">{[['','全部'],['pending','待支付'],['paid','已支付'],['closed','已关闭'],['refunding','退款中'],['refunded','已退款']].map(([key,label]) => <button className={status===key?'active':''} key={key} onClick={() => setStatus(key)}>{label}</button>)}</div>{loading ? <div className="center-loading"><LoaderCircle className="spin"/> 正在读取订单…</div> : <div className="order-list admin-order-list">{orders.map((item) => <article className="account-card" key={item.order_no}><div><span className={`order-status ${item.status}`}>{orderStatusText[item.status] || item.status}</span><h3>{item.package_name}</h3><p>{item.username} · {item.email}</p><small>{item.order_no} · {new Date(item.created_at).toLocaleString()}</small></div><div className="order-amount"><b>¥{Number(item.amount).toFixed(2)}</b><span>{item.credit_count} 次</span></div><div className="order-actions"><button className="outline-button" onClick={() => showDetail(item)} disabled={busy === item.order_no}>详情</button>{item.status === 'pending' && <button className="outline-button" onClick={() => close(item)} disabled={busy === item.order_no}>关闭</button>}{item.status === 'paid' && <button className="red-button" onClick={() => refund(item)} disabled={busy === item.order_no}>{busy === item.order_no ? <LoaderCircle className="spin"/> : '退款'}</button>}</div></article>)}</div>}{detail && <div className="modal-backdrop" onMouseDown={(e) => e.target === e.currentTarget && setDetail(null)}><section className="order-detail-modal"><button className="modal-close" onClick={() => setDetail(null)}><X/></button><h2>{detail.package_name}</h2><p>{detail.username} · {detail.email}</p><p>订单号：{detail.order_no}</p><div className="credit-overview"><div><b>¥{Number(detail.amount).toFixed(2)}</b><span>订单金额</span></div><div><b>{detail.credit_count}</b><span>购买次数</span></div><div><b>{orderStatusText[detail.status] || detail.status}</b><span>当前状态</span></div></div><h3>支付与退款流水</h3><div className="security-list">{detail.transactions.map((tx) => <div key={tx.id}><span className={`order-status ${tx.status}`}>{tx.transaction_type === 'refund' ? '退款' : '支付'}</span><div><b>{tx.status} · ¥{Number(tx.amount).toFixed(2)}</b><span>{tx.request_no} · {new Date(tx.created_at).toLocaleString()}</span></div></div>)}</div></section></div>}</main>
}

function AdminKnowledgePage({ notify }) {
  const [files, setFiles] = useState([]), [status, setStatus] = useState(''), [loading, setLoading] = useState(true), [busy, setBusy] = useState(null)
  const load = () => { setLoading(true); api.adminKnowledgeFiles(status).then(setFiles).catch((e) => notify(e.message, 'error')).finally(() => setLoading(false)) }
  useEffect(() => { load() }, [status])
  const retry = async (item) => { setBusy(item.id); try { const next = await api.adminReprocessKnowledge(item.id); setFiles((old) => old.map((v) => v.id === item.id ? { ...v, ...next } : v)); notify('文件已重新入队', 'success') } catch(e) { notify(e.message, 'error') } finally { setBusy(null) } }
  const remove = async (item) => { if (!confirm(`确定删除 ${item.user_email} 的“${item.original_name}”吗？`)) return; setBusy(item.id); try { await api.adminDeleteKnowledge(item.id); setFiles((old) => old.filter((v) => v.id !== item.id)); notify('文件已删除并记录审计日志', 'success') } catch(e) { notify(e.message, 'error') } finally { setBusy(null) } }
  return <main className="page-shell wrap"><div className="page-title"><span className="eyebrow"><BookOpen size={14}/> 运营后台</span><h1>知识库文件管理</h1><p>查看全站文件状态，重新处理失败任务并清理资料。</p></div><div className="project-filters">{[['','全部'],['queued','排队中'],['processing','处理中'],['completed','已完成'],['failed','失败']].map(([key,label]) => <button key={key} className={status === key ? 'active' : ''} onClick={() => setStatus(key)}>{label}</button>)}</div>{loading ? <div className="center-loading"><LoaderCircle className="spin"/> 正在读取…</div> : <div className="knowledge-file-list admin-knowledge-list">{files.map((item) => <article className="account-card" key={item.id}><FileText/><div><h3>{item.original_name}</h3><p>{item.username} · {item.user_email}</p><small>{(item.size_bytes / 1024).toFixed(1)} KB · 尝试 {item.attempt_count} 次</small>{item.error_message && <small>{item.error_message}</small>}</div><span className={`knowledge-status ${item.status}`}>{knowledgeStatusText[item.status] || item.status}</span><div className="order-actions">{['failed','completed'].includes(item.status) && <button className="outline-button" onClick={() => retry(item)} disabled={busy === item.id}>重新处理</button>}<button className="danger-link" onClick={() => remove(item)} disabled={busy === item.id}>删除</button></div></article>)}</div>}</main>
}

const riskText = { low: '较低风险', medium: '中等风险', high: '较高风险', unknown: '数据不足' }

function ReportsPage({ notify }) {
  const [projects, setProjects] = useState([]), [projectId, setProjectId] = useState('')
  const [reports, setReports] = useState([]), [loading, setLoading] = useState(true), [generating, setGenerating] = useState(false), [downloading, setDownloading] = useState('')
  useEffect(() => { Promise.all([api.projects(), api.reports()]).then(([projectRows, reportRows]) => { const eligible = projectRows.filter((item) => item.final_name); setProjects(eligible); setProjectId(String(eligible[0]?.id || '')); setReports(reportRows) }).catch((e) => notify(e.message, 'error')).finally(() => setLoading(false)) }, [])
  const generate = async (e) => { e.preventDefault(); if (!projectId) return; setGenerating(true); try { const item = await api.createReport({ project_id: Number(projectId), client_request_id: `report:${crypto.randomUUID()}` }); setReports((old) => [item, ...old]); notify('PDF 命名报告已生成', 'success') } catch(e) { notify(e.message, 'error') } finally { setGenerating(false) } }
  const download = async (item) => { setDownloading(item.id); try { await api.downloadReport(item.id, `${item.name}-命名价值报告.pdf`); notify('报告下载已开始', 'success') } catch(e) { notify(e.message, 'error') } finally { setDownloading('') } }
  if (loading) return <div className="center-loading"><LoaderCircle className="spin"/> 正在读取报告…</div>
  return <main className="page-shell wrap"><div className="page-title"><span className="eyebrow"><FileText size={14}/> PDF 命名报告</span><h1>把每一次认真推演，沉淀成报告</h1><p>汇总项目条件、候选历史、最终选名、名称校验与品牌价值资产，可随时鉴权下载。</p></div><div className="report-create-panel account-card"><div><h2>生成新报告</h2><p>系统会自动选取该项目最新的名称校验和品牌资产版本。</p></div>{projects.length ? <form onSubmit={generate}><select value={projectId} onChange={(e) => setProjectId(e.target.value)}>{projects.map((project) => <option key={project.id} value={project.id}>{project.title} · 最终名称：{project.final_name}</option>)}</select><button className="red-button" disabled={generating}>{generating ? <><LoaderCircle className="spin"/> 生成中…</> : <><FileText size={17}/> 生成 PDF 报告</>}</button></form> : <p className="asset-empty-note">暂无已选定最终名称的项目。请先完成命名并选定一个候选名称。</p>}</div><section className="report-library"><div className="results-head"><div><small>REPORT LIBRARY</small><h2>我的报告</h2></div><span>{reports.length} 份</span></div>{reports.length ? <div className="report-grid">{reports.map((item) => <article className="account-card" key={item.id}><div className="report-file-icon"><FileText/></div><div><span>PDF · {item.page_count} 页 · {(item.file_size / 1024).toFixed(1)} KB</span><h3>{item.title}</h3><p>最终选名：{item.name}</p><small>{new Date(item.created_at).toLocaleString()} · {item.validation_id ? '含名称校验' : '未含校验'} · {item.brand_asset_id ? '含品牌资产' : '未含品牌资产'}</small></div><button className="outline-button" disabled={downloading === item.id} onClick={() => download(item)}>{downloading === item.id ? <LoaderCircle className="spin"/> : <Download size={16}/>} 下载报告</button></article>)}</div> : <div className="empty-state standalone"><FileText/><h3>还没有报告</h3><p>选择一个已有最终名称的项目生成第一份报告。</p></div>}</section></main>
}

function AdminReportsPage({ notify }) {
  const [items, setItems] = useState([]), [loading, setLoading] = useState(true), [downloading, setDownloading] = useState('')
  useEffect(() => { api.adminReports().then(setItems).catch((e) => notify(e.message, 'error')).finally(() => setLoading(false)) }, [])
  const download = async (item) => { setDownloading(item.id); try { await api.adminDownloadReport(item.id); notify('报告下载已开始', 'success') } catch(e) { notify(e.message, 'error') } finally { setDownloading('') } }
  return <main className="page-shell wrap"><div className="page-title"><span className="eyebrow"><FileText size={14}/> 运营后台</span><h1>PDF 命名报告</h1><p>查看并下载平台用户生成的命名报告。</p></div>{loading ? <div className="center-loading"><LoaderCircle className="spin"/> 正在读取…</div> : <div className="report-admin-list">{items.map((item) => <article className="account-card" key={item.id}><FileText/><div><h3>{item.title}</h3><p>{item.username} · {item.user_email}</p></div><span>{item.page_count} 页 · {(item.file_size / 1024).toFixed(1)} KB</span><small>{new Date(item.created_at).toLocaleString()}</small><button className="outline-button" disabled={downloading === item.id} onClick={() => download(item)}>{downloading === item.id ? <LoaderCircle className="spin"/> : <Download size={15}/>} 下载</button></article>)}</div>}</main>
}

function BrandAssetReport({ item }) {
  const position = item.positioning || {}, visual = item.visual_guidelines || {}
  return <div className="brand-asset-report">
    <header><div><span>品牌价值资产包</span><h2>{item.name}</h2></div><small>{new Date(item.created_at).toLocaleString()}</small></header>
    <section><h3>品牌定位说明</h3><blockquote>{position.positioning_statement}</blockquote><div className="asset-position-grid"><div><span>目标受众</span><p>{position.target_audience}</p></div><div><span>市场品类</span><p>{position.market_category}</p></div><div><span>核心价值</span><p>{position.core_value}</p></div><div><span>差异化</span><p>{position.differentiation}</p></div></div><div className="style-chips">{position.brand_personality?.map((tag) => <span key={tag}>{tag}</span>)}</div></section>
    <section><h3>Slogan 方案</h3><div className="slogan-list">{item.slogans.map((slogan, index) => <article key={`${slogan.text}-${index}`}><b>{slogan.text}</b><span>{slogan.tone}</span><p>{slogan.rationale}</p></article>)}</div></section>
    <section><h3>Logo 概念方向</h3><div className="logo-concept-grid">{item.logo_concepts.map((concept) => <article key={concept.title}><h4>{concept.title}</h4><p><b>图形：</b>{concept.symbol}</p><p><b>构图：</b>{concept.composition}</p><p><b>字体：</b>{concept.typography}</p><div className="style-chips">{concept.colors.map((color) => <span key={color}>{color}</span>)}</div><small>{concept.rationale}</small></article>)}</div></section>
    <section><h3>品牌视觉建议</h3><div className="asset-colors">{visual.colors?.map((color) => <div key={color.hex}><i style={{background: color.hex}}/><b>{color.name}</b><code>{color.hex}</code><small>{color.usage}</small></div>)}</div><div className="visual-copy"><p><b>字体：</b>{visual.typography}</p><p><b>图像：</b>{visual.imagery}</p><p><b>版式：</b>{visual.layout}</p><p><b>避免：</b>{visual.avoid?.join('；')}</p></div></section>
    <section><h3>域名矩阵</h3>{item.domain_matrix.length ? <div className="domain-asset-list">{item.domain_matrix.map((domain) => <article key={domain.domain}><code>{domain.domain}</code><span className={domain.status}>{domain.status === 'available' ? '可能可注册' : domain.status === 'registered' ? '已注册' : '待复核'}</span><b>{domain.role}</b><p>{domain.recommendation}</p></article>)}</div> : <p className="asset-empty-note">尚未关联名称校验。先完成名称校验，重新生成时即可获得基于查询结果的域名矩阵。</p>}</section>
    <section><h3>风险提示</h3><div className="asset-risks">{item.risk_notes.map((risk, index) => <article key={`${risk.category}-${index}`}><span className={`risk-badge ${risk.level}`}>{risk.category} · {{low:'较低',medium:'中等',high:'较高',unknown:'未知'}[risk.level]}</span><p>{risk.note}</p><small>建议：{risk.action}</small></article>)}</div><p className="risk-disclaimer">本内容是品牌策略辅助建议，不构成法律意见、商标核准结论或域名注册保证。</p></section>
  </div>
}

function BrandAssetsPage({ selectionId, notify, go }) {
  const [selections, setSelections] = useState([]), [selectedId, setSelectedId] = useState(selectionId || '')
  const [validations, setValidations] = useState([]), [validationId, setValidationId] = useState('')
  const [brief, setBrief] = useState(''), [history, setHistory] = useState([]), [result, setResult] = useState(null), [loading, setLoading] = useState(true), [generating, setGenerating] = useState(false)
  useEffect(() => { Promise.all([api.selectedNames(), api.brandAssets()]).then(([names, assets]) => { const enterprise = names.filter((item) => item.category === '企业名'); setSelections(enterprise); const initial = String(selectionId || enterprise[0]?.id || ''); setSelectedId(initial); setHistory(assets); setResult(assets.find((item) => String(item.selected_name_id) === initial) || assets[0] || null) }).catch((e) => notify(e.message, 'error')).finally(() => setLoading(false)) }, [selectionId])
  useEffect(() => { if (!selectedId) { setValidations([]); setValidationId(''); return } api.validations(selectedId).then((items) => { setValidations(items); setValidationId(items[0]?.id ? String(items[0].id) : '') }).catch((e) => notify(e.message, 'error')) }, [selectedId])
  const generate = async (e) => { e.preventDefault(); if (!selectedId) return; setGenerating(true); try { const item = await api.createBrandAsset({ selected_name_id: Number(selectedId), validation_id: validationId ? Number(validationId) : null, client_request_id: `brand-asset:${crypto.randomUUID()}`, brief }); setResult(item); setHistory((old) => [item, ...old]); notify('品牌价值资产包已生成', 'success') } catch(e) { notify(e.message, 'error') } finally { setGenerating(false) } }
  if (loading) return <div className="center-loading"><LoaderCircle className="spin"/> 正在读取品牌资产…</div>
  if (!selections.length) return <main className="page-shell wrap narrow"><div className="empty-state standalone"><Gem/><h3>请先选定企业名称</h3><p>品牌价值资产以最终企业名称为起点。</p><button className="red-button" onClick={() => go('create', '企业名')}>开始企业起名</button></div></main>
  return <main className="page-shell wrap"><div className="page-title"><span className="eyebrow"><Gem size={14}/> 品牌价值资产</span><h1>从一个名字，走向完整品牌</h1><p>一次生成定位、Slogan、Logo 概念、视觉建议、域名矩阵与风险行动清单。</p></div><div className="brand-asset-layout"><form className="account-card brand-asset-form" onSubmit={generate}><label className="field"><span>最终企业名称</span><select value={selectedId} onChange={(e) => setSelectedId(e.target.value)}>{selections.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label><label className="field"><span>关联名称校验 <small>建议选择最新记录</small></span><select value={validationId} onChange={(e) => setValidationId(e.target.value)}><option value="">暂不关联</option>{validations.map((item) => <option key={item.id} value={item.id}>{new Date(item.created_at).toLocaleDateString()} · 风险 {item.risk_score} 分 · 覆盖 {item.coverage}%</option>)}</select></label>{!validations.length && <button type="button" className="text-button" onClick={() => go('validation', selectedId)}>先进行名称校验 →</button>}<label className="field"><span>品牌补充简报 <small>可选</small></span><textarea rows="7" maxLength="1200" value={brief} onChange={(e) => setBrief(e.target.value)} placeholder="例如：目标客户、价格带、竞争品牌、希望传达的气质、应用场景…"/></label><button className="red-button wide" disabled={generating}>{generating ? <><LoaderCircle className="spin"/> 正在构建品牌体系…</> : <><Gem size={17}/> 生成品牌资产包</>}</button><small className="asset-form-note">每次生成都会保存为独立版本，便于比较不同策略方向。</small></form><section className="brand-asset-output">{result ? <BrandAssetReport item={result}/> : <div className="empty-state"><Gem/><h3>等待生成</h3><p>补充越具体的业务背景，资产方案越具可执行性。</p></div>}</section></div>{history.length > 1 && <section className="asset-history"><h2>历史版本</h2>{history.map((item) => <button key={item.id} onClick={() => setResult(item)}><Gem size={17}/><b>{item.name}</b><span>{item.positioning?.core_value}</span><small>{new Date(item.created_at).toLocaleString()}</small></button>)}</section>}</main>
}

function AdminBrandAssetsPage({ notify }) {
  const [items, setItems] = useState([]), [loading, setLoading] = useState(true)
  useEffect(() => { api.adminBrandAssets().then(setItems).catch((e) => notify(e.message, 'error')).finally(() => setLoading(false)) }, [])
  return <main className="page-shell wrap"><div className="page-title"><span className="eyebrow"><Gem size={14}/> 运营后台</span><h1>品牌价值资产记录</h1><p>审阅平台生成的定位、创意资产版本及其校验关联情况。</p></div>{loading ? <div className="center-loading"><LoaderCircle className="spin"/> 正在读取…</div> : <div className="brand-asset-admin-list">{items.map((item) => <article className="account-card" key={item.id}><Gem/><div><h3>{item.name}</h3><p>{item.username} · {item.user_email}</p></div><span>{item.slogans.length} 条 Slogan · {item.logo_concepts.length} 个 Logo 方向</span><small>{item.validation_id ? `已关联校验 #${item.validation_id}` : '未关联校验'} · {new Date(item.created_at).toLocaleString()}</small></article>)}</div>}</main>
}

function ValidationPage({ selectionId, notify, go }) {
  const [selections, setSelections] = useState([]), [selectedId, setSelectedId] = useState(selectionId || '')
  const [stem, setStem] = useState(''), [suffixes, setSuffixes] = useState(['com','cn','net','io'])
  const [history, setHistory] = useState([]), [result, setResult] = useState(null), [loading, setLoading] = useState(true), [checking, setChecking] = useState(false)
  useEffect(() => { api.selectedNames().then((items) => { const enterprise = items.filter((item) => item.category === '企业名'); setSelections(enterprise); const initial = selectionId || enterprise[0]?.id || ''; setSelectedId(initial) }).catch((e) => notify(e.message, 'error')).finally(() => setLoading(false)) }, [selectionId])
  useEffect(() => { if (!selectedId) { setHistory([]); setResult(null); return } api.validations(selectedId).then((items) => { setHistory(items); setResult(items[0] || null) }).catch((e) => notify(e.message, 'error')) }, [selectedId])
  const toggleSuffix = (value) => setSuffixes((old) => old.includes(value) ? old.filter((item) => item !== value) : [...old, value])
  const submit = async (e) => { e.preventDefault(); if (!selectedId || !stem.trim() || !suffixes.length) return notify('请选择企业名称、填写域名前缀并至少选择一个后缀。', 'error'); setChecking(true); try { const item = await api.createValidation({ selected_name_id: Number(selectedId), client_request_id: `validation:${crypto.randomUUID()}`, domain_stem: stem.trim().toLowerCase(), suffixes }); setResult(item); setHistory((old) => [item, ...old]); notify('名称综合校验已完成', 'success') } catch(e) { notify(e.message, 'error') } finally { setChecking(false) } }
  if (loading) return <main className="page-shell wrap"><div className="center-loading"><LoaderCircle className="spin"/> 正在读取最终选名…</div></main>
  if (!selections.length) return <main className="page-shell wrap narrow"><div className="empty-state standalone"><ShieldCheck/><h3>请先选定企业名称</h3><p>从企业命名候选中确认最终名称后，才能进行综合校验。</p><button className="red-button" onClick={() => go('create', '企业名')}>开始企业起名</button></div></main>
  return <main className="page-shell wrap"><div className="page-title"><span className="eyebrow"><ShieldCheck size={14}/> 名称风险校验</span><h1>在投入品牌之前，多查一步</h1><p>综合检查多后缀域名、商标近似、企业重名和社交平台占用情况。数据不足会明确标注，不作为法律意见。</p></div><div className="validation-layout"><form className="account-card validation-form" onSubmit={submit}><label className="field"><span>最终企业名称</span><select value={selectedId} onChange={(e) => setSelectedId(e.target.value)}>{selections.map((item) => <option value={item.id} key={item.id}>{item.name}</option>)}</select></label><label className="field"><span>英文或拼音域名前缀</span><input required pattern="[A-Za-z0-9-]+" maxLength="63" value={stem} onChange={(e) => setStem(e.target.value)} placeholder="例如 yinian"/></label><div className="field"><span>域名后缀</span><div className="style-chips">{['com','cn','net','io','ai','co'].map((item) => <button type="button" key={item} className={suffixes.includes(item) ? 'selected' : ''} onClick={() => toggleSuffix(item)}>.{item}</button>)}</div></div><button className="red-button wide" disabled={checking}>{checking ? <><LoaderCircle className="spin"/> 正在查询多个数据源…</> : <><ShieldCheck size={17}/> 开始综合校验</>}</button><small>商标、企业和社交查询需要在后端配置相应数据提供商；未配置时报告会显示数据不足。</small></form><section className="validation-result">{result ? <ValidationResult item={result}/> : <div className="empty-state"><ShieldCheck/><h3>等待校验</h3><p>选择名称并填写域名前缀后开始查询。</p></div>}</section></div>{history.length > 1 && <section className="validation-history"><h2>历史报告</h2>{history.map((item) => <button key={item.id} onClick={() => setResult(item)}><span className={`risk-badge ${item.risk_level}`}>{riskText[item.risk_level]}</span><b>{item.name}</b><small>{new Date(item.created_at).toLocaleString()} · 覆盖 {item.coverage}%</small></button>)}</section>}</main>
}

function ValidationResult({ item }) {
  const sources = [
    ['商标近似', item.trademark, item.trademark?.matches?.length || 0],
    ['企业重名', item.company, item.company?.matches?.length || 0],
    ['社交平台', item.social, item.social?.profiles?.filter((v) => v.status === 'occupied').length || 0],
  ]
  return <div className="validation-report"><header><div className={`risk-score ${item.risk_level}`}><b>{item.risk_score}</b><span>风险分</span></div><div><span className={`risk-badge ${item.risk_level}`}>{riskText[item.risk_level]}</span><h2>{item.name}</h2><p>数据覆盖率 {item.coverage}% · {item.status === 'completed' ? '全部数据源完成' : '部分数据源未完成'}</p></div></header><p className="risk-summary">{item.risk_summary}</p><div className="domain-validation-grid">{item.domains.map((domain) => <div key={domain.domain}><code>{domain.domain}</code><span className={domain.status}>{domain.status === 'available' ? '可注册' : domain.status === 'registered' ? '已注册' : '未知'}</span><small>{domain.message}</small></div>)}</div><div className="validation-sources">{sources.map(([label, source, count]) => <div key={label}><b>{label}</b><span>{source?.status === 'completed' ? `${count} 条匹配` : source?.status === 'unavailable' ? '未配置数据源' : '查询异常'}</span><small>{source?.message}</small></div>)}</div><div className="risk-disclaimer">结果仅用于品牌筛查参考，不构成商标注册、企业登记或法律意见；正式投入前请向专业机构复核。</div></div>
}

function AdminValidationsPage({ notify }) {
  const [items, setItems] = useState([]), [risk, setRisk] = useState(''), [loading, setLoading] = useState(true)
  useEffect(() => { setLoading(true); api.adminValidations(risk).then(setItems).catch((e) => notify(e.message, 'error')).finally(() => setLoading(false)) }, [risk])
  return <main className="page-shell wrap"><div className="page-title"><span className="eyebrow"><ShieldCheck size={14}/> 运营后台</span><h1>名称校验记录</h1><p>查看平台名称风险结果、数据覆盖率和用户校验历史。</p></div><div className="project-filters">{[['','全部'],['low','较低'],['medium','中等'],['high','较高'],['unknown','数据不足']].map(([key,label]) => <button key={key} className={risk === key ? 'active' : ''} onClick={() => setRisk(key)}>{label}</button>)}</div>{loading ? <div className="center-loading"><LoaderCircle className="spin"/> 正在读取…</div> : <div className="validation-admin-list">{items.map((item) => <article className="account-card" key={item.id}><span className={`risk-badge ${item.risk_level}`}>{riskText[item.risk_level]}</span><div><h3>{item.name}</h3><p>{item.username} · {item.user_email}</p><small>{item.domain_stem} · 覆盖 {item.coverage}% · {new Date(item.created_at).toLocaleString()}</small></div><b>{item.risk_score} 分</b><p>{item.risk_summary}</p></article>)}</div>}</main>
}

const taskStatusText = { queued: '排队中', running: '执行中', completed: '已完成', failed: '失败', canceled: '已取消' }

function TasksPage({ notify }) {
  const [tasks, setTasks] = useState([]), [loading, setLoading] = useState(true), [busy, setBusy] = useState(null)
  const load = () => api.tasks().then(setTasks).catch((e) => notify(e.message, 'error')).finally(() => setLoading(false))
  useEffect(() => { load() }, [])
  useEffect(() => { if (!tasks.some((item) => ['queued','running'].includes(item.status))) return; const timer = setInterval(load, 3000); return () => clearInterval(timer) }, [tasks.map((item) => `${item.id}:${item.status}`).join(',')])
  const retry = async (item) => { setBusy(item.id); try { const next = await api.retryTask(item.id); setTasks((old) => old.map((v) => v.id === item.id ? next : v)); notify('任务已重新进入队列', 'success') } catch(e) { notify(e.message, 'error') } finally { setBusy(null) } }
  return <main className="page-shell wrap narrow"><div className="page-title"><span className="eyebrow"><RefreshCw size={14}/> 用户中心</span><h1>我的异步任务</h1><p>查看知识库解析等后台任务的执行进度、重试次数和失败原因。</p></div>{loading ? <div className="center-loading"><LoaderCircle className="spin"/> 正在读取任务…</div> : tasks.length ? <div className="task-list">{tasks.map((item) => <article className="account-card" key={item.id}><div><span className={`knowledge-status ${item.status}`}>{taskStatusText[item.status] || item.status}</span><h3>{item.task_type === 'knowledge.process' ? '知识库文件处理' : item.task_type}</h3><p>任务 ID：{item.id}</p><small>{new Date(item.created_at).toLocaleString()} · 第 {item.attempt_count}/{item.max_attempts} 次尝试</small>{item.error_message && <em>{item.error_message}</em>}</div><div className="task-progress"><span style={{ width: `${item.progress}%` }}/></div><b>{item.progress}%</b>{['failed','canceled'].includes(item.status) && <button className="outline-button" disabled={busy === item.id} onClick={() => retry(item)}>重新执行</button>}</article>)}</div> : <div className="empty-state standalone"><RefreshCw/><h3>暂无后台任务</h3><p>上传知识库资料后，任务会显示在这里。</p></div>}</main>
}

function AdminTasksPage({ notify }) {
  const [tasks, setTasks] = useState([]), [status, setStatus] = useState(''), [loading, setLoading] = useState(true), [busy, setBusy] = useState(null)
  const load = () => { setLoading(true); api.adminTasks(status).then(setTasks).catch((e) => notify(e.message, 'error')).finally(() => setLoading(false)) }
  useEffect(() => { load() }, [status])
  const replace = (next) => setTasks((old) => old.map((v) => v.id === next.id ? { ...v, ...next } : v))
  const retry = async (item) => { setBusy(item.id); try { replace(await api.adminRetryTask(item.id)); notify('任务已重新入队并记录审计日志', 'success') } catch(e) { notify(e.message, 'error') } finally { setBusy(null) } }
  const cancel = async (item) => { if (!confirm('确定取消这个排队任务吗？')) return; setBusy(item.id); try { replace(await api.adminCancelTask(item.id)); notify('任务已取消', 'success') } catch(e) { notify(e.message, 'error') } finally { setBusy(null) } }
  return <main className="page-shell wrap"><div className="page-title"><span className="eyebrow"><RefreshCw size={14}/> 运营后台</span><h1>异步任务管理</h1><p>跟踪任务进度、失败原因、自动重试次数，并人工重试或取消任务。</p></div><div className="project-filters">{[['','全部'],['queued','排队中'],['running','执行中'],['completed','已完成'],['failed','失败'],['canceled','已取消']].map(([key,label]) => <button key={key} className={status === key ? 'active' : ''} onClick={() => setStatus(key)}>{label}</button>)}</div>{loading ? <div className="center-loading"><LoaderCircle className="spin"/> 正在读取任务…</div> : <div className="task-list admin-task-list">{tasks.map((item) => <article className="account-card" key={item.id}><div><span className={`knowledge-status ${item.status}`}>{taskStatusText[item.status] || item.status}</span><h3>{item.task_type}</h3><p>{item.username} · {item.user_email}</p><small>{item.id} · {item.attempt_count}/{item.max_attempts} 次</small>{item.error_message && <em>{item.error_message}</em>}</div><div className="task-progress"><span style={{ width: `${item.progress}%` }}/></div><b>{item.progress}%</b><div className="order-actions">{['failed','canceled'].includes(item.status) && <button className="outline-button" disabled={busy === item.id} onClick={() => retry(item)}>重试</button>}{item.status === 'queued' && <button className="danger-link" disabled={busy === item.id} onClick={() => cancel(item)}>取消</button>}</div></article>)}</div>}</main>
}

function AuthModal({ mode: initial, close, onLogin, notify, required = false, inviteCode = '' }) {
  const [mode, setMode] = useState(initial), [loading, setLoading] = useState(false), [countdown, setCountdown] = useState(0)
  const [form, setForm] = useState({ email: '', username: '', password: '', new_password: '', confirm_password: '', code: '', invite_code: inviteCode })
  useEffect(() => { if (!countdown) return; const timer = setTimeout(() => setCountdown(countdown - 1), 1000); return () => clearTimeout(timer) }, [countdown])
  const update = (key, value) => setForm((old) => ({ ...old, [key]: value }))
  const sendCode = async () => { if (!form.email) return notify('请先填写邮箱。', 'error'); try { await api.sendCode(form.email); setCountdown(60); notify('验证码已发送，请查看邮箱。', 'success') } catch(e) { notify(e.message, 'error') } }
  const sendResetCode = async () => { if (!form.email) return notify('请先填写邮箱。', 'error'); try { const data = await api.sendPasswordResetCode(form.email); setCountdown(60); notify(data.message, 'success') } catch(e) { notify(e.message, 'error') } }
  const submit = async (e) => {
    e.preventDefault(); setLoading(true)
    try {
      if (mode === 'login') {
        const data = await api.login({ email: form.email, password: form.password })
        api.saveSession(data); onLogin(data); if (!required) close()
        notify(`欢迎回来，${data.user.username}。`, 'success')
      } else if (mode === 'register') {
        await api.register(form); notify('注册成功，已赠送 3 次起名机会，请登录。', 'success'); setMode('login')
      } else {
        const data = await api.resetPassword({ email: form.email, code: form.code, new_password: form.new_password, confirm_password: form.confirm_password })
        notify(data.message, 'success'); setMode('login'); update('code', '')
      }
    } catch(e) { notify(e.message, 'error') } finally { setLoading(false) }
  }
  const title = mode === 'login' ? '欢迎归来' : mode === 'register' ? '与好名字初次相遇' : '重置登录密码'
  const subtitle = mode === 'login' ? '登录后进入一念 AI 起名空间' : mode === 'register' ? '注册即赠 3 次免费起名额度' : '验证码将在 5 分钟内有效'
  const formCard = <div className="auth-modal">
    {!required && <button className="modal-close" onClick={close}><X/></button>}
    <div className="auth-brand"><span className="seal">念</span><div><h2>{title}</h2><p>{subtitle}</p></div></div>
    {mode !== 'reset' ? <div className="auth-tabs"><button className={mode === 'login' ? 'active' : ''} onClick={() => setMode('login')}>登录</button><button className={mode === 'register' ? 'active' : ''} onClick={() => setMode('register')}>注册</button></div> : <button className="auth-back" onClick={() => setMode('login')}><ChevronRight/> 返回登录</button>}
    <form onSubmit={submit}>
      <label className="field"><span>邮箱</span><input type="email" required autoComplete="email" value={form.email} onChange={(e) => update('email', e.target.value)} placeholder="name@example.com"/></label>
      {mode === 'register' && <label className="field"><span>用户名</span><input required minLength="4" maxLength="20" autoComplete="username" value={form.username} onChange={(e) => update('username', e.target.value)} placeholder="4–20 个字符"/></label>}
      {mode === 'register' && <label className="field"><span>邀请码 <small>可选，注册后不可改绑</small></span><input minLength="4" maxLength="20" value={form.invite_code} onChange={(e)=>update('invite_code',e.target.value.replace(/[^A-Za-z0-9]/g,'').toUpperCase())} placeholder="好友推广码"/></label>}
      {(mode === 'register' || mode === 'reset') && <label className="field"><span>邮箱验证码</span><div className="code-input"><input required maxLength={6} inputMode="numeric" value={form.code} onChange={(e) => update('code', e.target.value.replace(/\D/g,''))} placeholder="6 位验证码"/><button type="button" disabled={countdown > 0} onClick={mode === 'reset' ? sendResetCode : sendCode}>{countdown ? `${countdown}s` : '获取验证码'}</button></div></label>}
      {mode !== 'reset' && <label className="field"><span>密码</span><input type="password" required minLength="6" maxLength="20" autoComplete={mode === 'login' ? 'current-password' : 'new-password'} value={form.password} onChange={(e) => update('password', e.target.value)} placeholder="6–20 个字符"/></label>}
      {mode === 'reset' && <label className="field"><span>新密码</span><input type="password" required minLength="6" maxLength="20" autoComplete="new-password" value={form.new_password} onChange={(e) => update('new_password', e.target.value)} placeholder="6–20 个字符"/></label>}
      {(mode === 'register' || mode === 'reset') && <label className="field"><span>确认密码</span><input type="password" required autoComplete="new-password" value={form.confirm_password} onChange={(e) => update('confirm_password', e.target.value)} placeholder="再次输入密码"/></label>}
      {mode === 'login' && <button type="button" className="forgot-password" onClick={() => setMode('reset')}>忘记密码？</button>}
      <button className="red-button wide" disabled={loading}>{loading ? <LoaderCircle className="spin"/> : mode === 'login' ? '登录并进入' : mode === 'register' ? '创建账户' : '确认重置密码'}</button>
    </form>
    {required && <p className="auth-required-note">登录即表示你同意安全保存个人命名记录与最终选择。</p>}
  </div>
  if (!required) return <div className="modal-backdrop" onMouseDown={(e) => e.target === e.currentTarget && close()}>{formCard}</div>
  return <div className="auth-gate"><section className="auth-gate-story"><div className="auth-gate-brand"><span className="seal">念</span><span>一念 AI</span></div><div><span className="eyebrow"><Sparkles size={14}/> 你的私人命名空间</span><h1>好名字，<br/>从一次认真登录开始</h1><p>登录后，候选名字、连续微调、最终选择与企业 Logo 都会安全关联到你的账户。</p><ul><li><Check/> 保存每一次命名会话</li><li><Check/> 从 5 个候选中确认最终名称</li><li><Check/> 为选定企业名生成品牌 Logo</li></ul></div><small>一字一世界 · 一念一生名</small></section><section className="auth-gate-panel">{formCard}</section></div>
}

function App() {
  const initialRoute = parseHash(location.hash)
  const [route, setRoute] = useState(initialRoute.page)
  const [preset, setPreset] = useState(initialRoute.value), [session, setSession] = useState(api.getSession()), [balance, setBalance] = useState(null)
  const [authChecking, setAuthChecking] = useState(() => Boolean(api.getSession()))
  const [authMode, setAuthMode] = useState(null), [toast, setToast] = useState(null)
  const notify = (message, type = '') => { setToast({ message, type }); setTimeout(() => setToast(null), 4500) }
  const refreshBalance = () => session && api.balance().then((v) => setBalance(v.balance)).catch(() => {})
  useEffect(() => {
    if (!session) { setAuthChecking(false); return }
    setAuthChecking(true)
    api.balance().then((value) => setBalance(value.balance)).catch(() => {}).finally(() => setAuthChecking(false))
  }, [session?.access_token])
  useEffect(() => { const handler = () => setSession(api.getSession()); window.addEventListener('session-change', handler); return () => window.removeEventListener('session-change', handler) }, [])
  const go = (page, value = '') => { setRoute(page); setPreset(String(value || '')); location.hash = value ? `${page}/${encodeURIComponent(value)}` : page; window.scrollTo({ top: 0, behavior: 'smooth' }) }
  useEffect(() => { const handler = () => { const next = parseHash(location.hash); setRoute(next.page); setPreset(next.value) }; window.addEventListener('hashchange', handler); return () => window.removeEventListener('hashchange', handler) }, [])
  const content = useMemo(() => {
    const common = { session, openAuth: setAuthMode, notify, go }
    if (route === 'create') return <CreatePage {...common} refreshBalance={refreshBalance} preset={preset} go={go}/>
    if (route === 'knowledge') return <ManagedKnowledgePage {...common}/>
    if (route === 'logo') return <LogoPage {...common} selectionId={preset} go={go}/>
    if (route === 'validation') return <ValidationPage {...common} selectionId={preset} go={go}/>
    if (route === 'brand-assets') return <BrandAssetsPage {...common} selectionId={preset} go={go}/>
    if (route === 'reports') return <ReportsPage {...common}/>
    if (route === 'experts') return <ExpertsPage {...common}/>
    if (route === 'community') return <CommunityPage {...common}/>
    if (route === 'community-publish') return <CommunityPublishPage {...common}/>
    if (route === 'community-detail') return <CommunityDetailPage {...common} pollId={preset}/>
    if (route === 'developers') return <DevelopersPage {...common}/>
    if (route === 'growth') return <GrowthPage {...common}/>
    if (route === 'projects') return <ProjectsPage {...common} projectId={preset} go={go}/>
    if (route === 'pricing') return <PricingPage {...common}/>
    if (route === 'account') return <AccountPage {...common} onSessionUpdate={(user) => { const next = { ...session, user }; api.saveSession(next); setSession(next) }}/>
    if (route === 'orders') return <OrdersPage {...common}/>
    if (route === 'tasks') return <TasksPage {...common}/>
    if (route === 'credits') return <CreditsPage {...common}/>
    if (route === 'admin-dashboard' && hasPermission(session?.user,'dashboard.read')) return <AdminDashboardPage {...common}/>
    if (route === 'admin-users' && hasPermission(session?.user,'users.read')) return <AdminUsersPage {...common}/>
    if (route === 'admin-security' && (hasPermission(session?.user,'roles.manage')||hasPermission(session?.user,'audit.read'))) return <AdminSecurityPage {...common}/>
    if (route === 'admin-projects' && hasPermission(session?.user,'projects.manage')) return <AdminProjectsPage {...common}/>
    if (route === 'admin-experts' && hasPermission(session?.user,'experts.manage')) return <AdminExpertsPage {...common}/>
    if (route === 'admin-community' && hasPermission(session?.user,'community.moderate')) return <AdminCommunityPage {...common}/>
    if (route === 'admin-developers' && hasPermission(session?.user,'developers.manage')) return <AdminDevelopersPage {...common}/>
    if (route === 'admin-growth' && hasPermission(session?.user,'growth.manage')) return <AdminGrowthPage {...common}/>
    if (route === 'expert-workspace' && hasPermission(session?.user,'expert.work')) return <ExpertWorkspacePage {...common}/>
    if (route === 'admin-credits' && hasPermission(session?.user,'credits.manage')) return <AdminCreditsPage {...common}/>
    if (route === 'admin-packages' && hasPermission(session?.user,'packages.manage')) return <AdminPackagesPage {...common}/>
    if (route === 'admin-orders' && hasPermission(session?.user,'orders.manage')) return <AdminOrdersPage {...common}/>
    if (route === 'admin-knowledge' && hasPermission(session?.user,'knowledge.manage')) return <AdminKnowledgePage {...common}/>
    if (route === 'admin-tasks' && hasPermission(session?.user,'tasks.manage')) return <AdminTasksPage {...common}/>
    if (route === 'admin-validations' && hasPermission(session?.user,'validations.manage')) return <AdminValidationsPage {...common}/>
    if (route === 'admin-brand-assets' && hasPermission(session?.user,'brand_assets.manage')) return <AdminBrandAssetsPage {...common}/>
    if (route === 'admin-reports' && hasPermission(session?.user,'reports.manage')) return <AdminReportsPage {...common}/>
    if (route.startsWith('admin-')) return <AccessDeniedPage area="运营后台" go={go}/>
    if (route === 'expert-workspace') return <AccessDeniedPage area="专家工作台" go={go}/>
    return <Home go={go}/>
  }, [route, session, preset])
  if (authChecking) return <div className="session-check"><div className="brand"><span className="seal">念</span><span>一念 AI</span></div><LoaderCircle className="spin"/><p>正在验证登录状态…</p></div>
  if (!session) return <div className="app auth-required"><AuthModal key={`${route}:${preset}`} required mode={route==='register'?'register':'login'} inviteCode={route==='register'?preset:''} close={() => {}} onLogin={(data) => { setAuthChecking(true); setSession(data) }} notify={notify}/><Toast toast={toast} close={() => setToast(null)}/></div>
  return <div className="app"><Header page={route} go={go} session={session} balance={balance} openAuth={setAuthMode} logout={async () => { try { await api.logout() } catch {} finally { api.saveSession(null);setSession(null);setBalance(null);go('home');notify('已安全退出。') } }}/>{content}<footer><div className="wrap"><div className="brand"><span className="seal">念</span><span>一念</span><small>AI 起名</small></div><p>让每一个名字，都有来处、有寓意、有未来。</p><span>© 2026 一念 AI</span></div></footer>{authMode && <AuthModal mode={authMode} close={() => setAuthMode(null)} onLogin={(data) => setSession(data)} notify={notify}/>}<Toast toast={toast} close={() => setToast(null)}/></div>
}

export default App
