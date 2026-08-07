import { useEffect, useMemo, useState } from 'react'
import {
  ArrowRight, BookOpen, Building2, Check, ChevronRight, CircleUserRound,
  Coins, Crown, Dog, Download, Feather, FileText, Heart, Image, LoaderCircle,
  LogOut, Menu, MessageCircleMore, MoonStar, Palette, RefreshCw, Send,
  Sparkles, UploadCloud, UserRound, WandSparkles, X, Zap,
} from 'lucide-react'
import { api, resolveAssetUrl } from './api'

const navItems = [
  ['home', '首页'], ['create', '智能起名'], ['knowledge', '专属知识库'],
  ['logo', '品牌 Logo'], ['pricing', '套餐'],
]

function Toast({ toast, close }) {
  if (!toast) return null
  return <div className={`toast ${toast.type || ''}`}><span>{toast.message}</span><button onClick={close}><X size={16}/></button></div>
}

function Header({ page, go, session, balance, openAuth, logout }) {
  const [mobile, setMobile] = useState(false)
  const nav = (id) => { go(id); setMobile(false) }
  return <header className="topbar">
    <button className="brand" onClick={() => nav('home')}><span className="seal">念</span><span>一念</span><small>AI 起名</small></button>
    <nav className={mobile ? 'nav open' : 'nav'}>
      {navItems.map(([id, label]) => <button key={id} className={page === id ? 'active' : ''} onClick={() => nav(id)}>{label}</button>)}
    </nav>
    <div className="header-actions">
      {session ? <>
        <button className="credit-pill" onClick={() => go('pricing')}><Coins size={16}/><b>{balance ?? '—'}</b> 次</button>
        <div className="user-menu"><CircleUserRound size={20}/><span>{session.user?.username}</span><button title="退出登录" onClick={logout}><LogOut size={16}/></button></div>
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

function NameCard({ item, index, onLogo }) {
  return <article className="result-card">
    <div className="result-index">0{index + 1}</div><div className="result-main"><h3>{item.name}</h3><div className="result-detail"><span>灵感出处</span><p>{item.reference || '源于 AI 创意推演'}</p></div><div className="result-detail"><span>名字寓意</span><p>{item.moral}</p></div>
    {item.domain && <div className="domain-row"><code>{item.domain}</code><span className={item.domain_status?.includes('未注册') ? 'available' : ''}>{item.domain_status}</span></div>}</div>
    {onLogo && <button className="icon-action" title="生成 Logo" onClick={() => onLogo(item.name)}><Palette size={18}/></button>}
  </article>
}

function CreatePage({ session, openAuth, refreshBalance, preset, go, notify }) {
  const [category, setCategory] = useState(preset || '人名')
  const [form, setForm] = useState({ surname: '', gender: '不限', length: '不限', other: '', exclude: '' })
  const [loading, setLoading] = useState(false), [results, setResults] = useState([])
  const [thread, setThread] = useState(''), [feedback, setFeedback] = useState(''), [refining, setRefining] = useState(false)
  useEffect(() => { if (preset) setCategory(preset) }, [preset])
  const update = (key, value) => setForm((old) => ({ ...old, [key]: value }))
  const generate = async (e) => {
    e.preventDefault(); if (!session) return openAuth('login')
    setLoading(true); setResults([])
    try {
      const data = await api.generateNames({ category, surname: form.surname.trim(), gender: form.gender, length: form.length, other: form.other.trim(), exclude: form.exclude.split(/[，,、\s]+/).filter(Boolean) })
      setResults(data.names || []); setThread(data.thread_id); refreshBalance(); notify('名字已为你准备好，欢迎继续微调。', 'success')
    } catch (e) { notify(e.message, 'error') } finally { setLoading(false) }
  }
  const refine = async () => {
    if (!feedback.trim()) return
    setRefining(true)
    try { const data = await api.feedbackNames({ thread_id: thread, category, feedback: feedback.trim() }); setResults(data.names || []); setFeedback(''); notify('已根据你的想法重新推演。', 'success') }
    catch (e) { notify(e.message, 'error') } finally { setRefining(false) }
  }
  return <main className="page-shell wrap">
    <div className="page-title"><span className="eyebrow"><WandSparkles size={14}/> 智能命名工坊</span><h1>把你的期待，写进名字里</h1><p>{categoryMeta[category].text}</p></div>
    <div className="creator-layout">
      <form className="form-panel" onSubmit={generate}>
        <div className="category-tabs">{Object.entries(categoryMeta).map(([key, meta]) => { const Icon = meta.icon; return <button type="button" className={category === key ? 'active' : ''} key={key} onClick={() => setCategory(key)}><Icon size={18}/>{key}</button> })}</div>
        {category === '人名' && <div className="field-row"><label className="field"><span>姓氏 <i>*</i></span><input required value={form.surname} onChange={(e) => update('surname', e.target.value)} placeholder="例如：陈" maxLength={4}/></label><label className="field"><span>性别偏好</span><select value={form.gender} onChange={(e) => update('gender', e.target.value)}><option>不限</option><option>男</option><option>女</option></select></label></div>}
        <div className="field"><span>名字长度</span><div className="choice-row">{['不限','单字','两字','多字'].map((v) => <button type="button" key={v} className={form.length === v ? 'selected' : ''} onClick={() => update('length', v)}>{v}</button>)}</div></div>
        <label className="field"><span>{category === '企业名' ? '品牌故事与行业定位' : category === '宠物名' ? '它的品种、性格和故事' : '你对名字的期待'}</span><textarea value={form.other} onChange={(e) => update('other', e.target.value)} placeholder={category === '企业名' ? '例如：面向年轻人的 AI 智能硬件品牌，希望简洁、有未来感…' : category === '宠物名' ? '例如：一只活泼的金毛，毛色像暖阳…' : '例如：希望名字清朗大方，寄托坚韧与自由的期望…'} rows="5"/></label>
        <label className="field"><span>不希望出现的字 <small>选填，用逗号分隔</small></span><input value={form.exclude} onChange={(e) => update('exclude', e.target.value)} placeholder="例如：伟，强，轩"/></label>
        <button className="red-button wide" disabled={loading}>{loading ? <><LoaderCircle className="spin" size={18}/> 正在翻阅典籍与灵感…</> : <><Sparkles size={18}/> 为我起名</>}</button>
        <p className="cost-note"><Coins size={14}/> 每次首次生成消耗 1 次额度，微调不额外消耗</p>
      </form>
      <section className="results-panel">
        {!results.length && !loading && <div className="empty-state"><div className="empty-orbit"><Feather/></div><h3>好名字，值得等待</h3><p>完善左侧信息，AI 将为你精选 5 个名字<br/>并逐一解读出处与寓意。</p></div>}
        {loading && <div className="thinking-state"><div className="ink-loader"><span/><span/><span/></div><h3>正在推演名字</h3><p>从音韵、字形、寓意与文化出处多维筛选</p></div>}
        {!!results.length && <><div className="results-head"><div><small>本轮灵感</small><h2>为你精选的名字</h2></div><button onClick={() => { setResults([]); setThread('') }}><RefreshCw size={15}/> 重新填写</button></div><div className="results-list">{results.map((item, i) => <NameCard key={`${item.name}-${i}`} item={item} index={i} onLogo={category === '企业名' ? (name) => go('logo', name) : null}/>)}</div><div className="feedback-box"><div><MessageCircleMore size={19}/><span><b>还差一点感觉？</b> 直接告诉 AI 如何调整</span></div><div className="feedback-input"><input value={feedback} onChange={(e) => setFeedback(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && refine()} placeholder="例如：更古典一些，保留第二个名字的感觉…"/><button onClick={refine} disabled={refining || !feedback.trim()}>{refining ? <LoaderCircle className="spin"/> : <Send/>}</button></div></div></>}
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

function LogoPage({ preset, notify }) {
  const [name, setName] = useState(preset || ''), [style, setStyle] = useState(''), [loading, setLoading] = useState(false), [result, setResult] = useState(null)
  useEffect(() => { if (preset) setName(preset) }, [preset])
  const styles = ['极简现代','东方雅韵','未来科技','自然清新','高端奢华']
  const generate = async (e) => { e.preventDefault(); setLoading(true); setResult(null); try { setResult(await api.generateLogo({ company_name: name, style_feedback: style })); } catch(e) { notify(e.message, 'error') } finally { setLoading(false) } }
  return <main className="page-shell wrap"><div className="page-title"><span className="eyebrow"><Palette size={14}/> AI 品牌视觉</span><h1>从名字，到第一眼心动</h1><p>为你的企业名称生成专属 Logo 概念，让品牌灵感跃然眼前。</p></div><div className="logo-layout"><form className="form-panel" onSubmit={generate}><label className="field"><span>企业名称 <i>*</i></span><input required value={name} onChange={(e) => setName(e.target.value)} placeholder="输入企业名称"/></label><div className="field"><span>选择风格</span><div className="style-chips">{styles.map((v) => <button type="button" className={style === v ? 'selected' : ''} key={v} onClick={() => setStyle(v)}>{v}</button>)}</div></div><label className="field"><span>补充你的想法</span><textarea rows="5" value={style} onChange={(e) => setStyle(e.target.value)} placeholder="例如：主色使用青绿色，图形融入山水意象，避免复杂细节…"/></label><button className="red-button wide" disabled={loading}>{loading ? <><LoaderCircle className="spin"/> AI 正在绘制…</> : <><WandSparkles size={18}/> 生成 Logo</>}</button></form><section className="logo-canvas">{!result && !loading && <div className="empty-state"><div className="logo-placeholder"><span>{name?.[0] || '念'}</span></div><h3>你的品牌印记</h3><p>填写名称与风格，开启第一次视觉探索</p></div>}{loading && <div className="thinking-state"><div className="brush-loader"/><h3>正在描绘品牌气质</h3><p>图像生成通常需要一些时间，请耐心等待</p></div>}{result && <div className="logo-result"><div className="logo-image-wrap"><img src={resolveAssetUrl(result.logo_url)} alt={`${result.company_name} Logo`}/></div><div><span className="status-dot">{result.logo_status}</span><h2>{result.company_name}</h2><p>{result.logo_prompt}</p><a className="outline-button" href={resolveAssetUrl(result.logo_url)} download target="_blank"><Download size={16}/> 查看原图</a></div></div>}</section></div></main>
}

function PricingPage({ session, openAuth, notify }) {
  const [packages, setPackages] = useState([]), [loading, setLoading] = useState(true), [buying, setBuying] = useState(null)
  useEffect(() => { api.packages().then(setPackages).catch((e) => notify(e.message, 'error')).finally(() => setLoading(false)) }, [])
  const buy = async (pkg) => { if (!session) return openAuth('login'); setBuying(pkg.id); try { const order = await api.createOrder(pkg.id); window.location.href = order.pay_url } catch(e) { notify(e.message, 'error'); setBuying(null) } }
  return <main className="page-shell wrap narrow"><div className="page-title"><span className="eyebrow"><Crown size={14}/> 灵感补给</span><h1>为下一次好名字续上灵感</h1><p>每次首次生成消耗 1 次额度，连续反馈与精细调整不另收费。</p></div>{loading ? <div className="center-loading"><LoaderCircle className="spin"/> 正在加载套餐…</div> : packages.length ? <div className="pricing-grid">{packages.map((pkg, i) => <article className={`price-card ${i === 1 ? 'popular' : ''}`} key={pkg.id}>{i === 1 && <span className="popular-tag">更多人的选择</span>}<div className="price-icon">{i === 0 ? <Feather/> : i === 1 ? <Sparkles/> : <Crown/>}</div><h3>{pkg.name}</h3><p className="credits"><b>{pkg.credit_count}</b> 次起名额度</p><div className="price"><small>¥</small><strong>{Number(pkg.price).toFixed(2)}</strong></div><ul><li><Check/>完整名字释义</li><li><Check/>支持多轮免费微调</li><li><Check/>企业名域名查询</li></ul><button className={i === 1 ? 'red-button wide' : 'outline-button wide'} onClick={() => buy(pkg)} disabled={buying === pkg.id}>{buying === pkg.id ? <LoaderCircle className="spin"/> : '选择此套餐'}</button></article>)}</div> : <div className="empty-state standalone"><Coins/><h3>暂时没有上架套餐</h3><p>请先在后端 package 表中配置可用套餐。</p></div>}<div className="pricing-note"><Zap/><span>新用户注册即赠 <b>3 次</b> 免费起名额度</span></div></main>
}

function AuthModal({ mode: initial, close, onLogin, notify }) {
  const [mode, setMode] = useState(initial), [loading, setLoading] = useState(false), [countdown, setCountdown] = useState(0)
  const [form, setForm] = useState({ email: '', username: '', password: '', confirm_password: '', code: '' })
  useEffect(() => { if (!countdown) return; const timer = setTimeout(() => setCountdown(countdown - 1), 1000); return () => clearTimeout(timer) }, [countdown])
  const update = (key, value) => setForm((old) => ({ ...old, [key]: value }))
  const sendCode = async () => { if (!form.email) return notify('请先填写邮箱。', 'error'); try { await api.sendCode(form.email); setCountdown(60); notify('验证码已发送，请查看邮箱。', 'success') } catch(e) { notify(e.message, 'error') } }
  const submit = async (e) => { e.preventDefault(); setLoading(true); try { if (mode === 'login') { const data = await api.login({ email: form.email, password: form.password }); api.saveSession(data); onLogin(data); close(); notify(`欢迎回来，${data.user.username}。`, 'success') } else { await api.register(form); notify('注册成功，已赠送 3 次起名机会。', 'success'); setMode('login') } } catch(e) { notify(e.message, 'error') } finally { setLoading(false) } }
  return <div className="modal-backdrop" onMouseDown={(e) => e.target === e.currentTarget && close()}><div className="auth-modal"><button className="modal-close" onClick={close}><X/></button><div className="auth-brand"><span className="seal">念</span><div><h2>{mode === 'login' ? '欢迎归来' : '与好名字初次相遇'}</h2><p>{mode === 'login' ? '继续寻找那个恰如其分的名字' : '注册即赠 3 次免费起名额度'}</p></div></div><div className="auth-tabs"><button className={mode === 'login' ? 'active' : ''} onClick={() => setMode('login')}>登录</button><button className={mode === 'register' ? 'active' : ''} onClick={() => setMode('register')}>注册</button></div><form onSubmit={submit}><label className="field"><span>邮箱</span><input type="email" required value={form.email} onChange={(e) => update('email', e.target.value)} placeholder="name@example.com"/></label>{mode === 'register' && <><label className="field"><span>用户名</span><input required minLength="4" maxLength="20" value={form.username} onChange={(e) => update('username', e.target.value)} placeholder="4–20 个字符"/></label><label className="field"><span>邮箱验证码</span><div className="code-input"><input required maxLength="4" value={form.code} onChange={(e) => update('code', e.target.value.replace(/\D/g,''))} placeholder="4 位验证码"/><button type="button" disabled={countdown > 0} onClick={sendCode}>{countdown ? `${countdown}s` : '获取验证码'}</button></div></label></>}<label className="field"><span>密码</span><input type="password" required minLength="6" maxLength="20" value={form.password} onChange={(e) => update('password', e.target.value)} placeholder="6–20 个字符"/></label>{mode === 'register' && <label className="field"><span>确认密码</span><input type="password" required value={form.confirm_password} onChange={(e) => update('confirm_password', e.target.value)} placeholder="再次输入密码"/></label>}<button className="red-button wide" disabled={loading}>{loading ? <LoaderCircle className="spin"/> : mode === 'login' ? '登录' : '创建账户'}</button></form></div></div>
}

function App() {
  const [route, setRoute] = useState(() => location.hash.slice(1).split('/')[0] || 'home')
  const [preset, setPreset] = useState(''), [session, setSession] = useState(api.getSession()), [balance, setBalance] = useState(null)
  const [authMode, setAuthMode] = useState(null), [toast, setToast] = useState(null)
  const notify = (message, type = '') => { setToast({ message, type }); setTimeout(() => setToast(null), 4500) }
  const refreshBalance = () => session && api.balance().then((v) => setBalance(v.balance)).catch(() => {})
  useEffect(() => {
    refreshBalance()
  }, [session?.access_token])
  useEffect(() => { const handler = () => setSession(api.getSession()); window.addEventListener('session-change', handler); return () => window.removeEventListener('session-change', handler) }, [])
  const go = (page, value = '') => { setRoute(page); setPreset(value); location.hash = page; window.scrollTo({ top: 0, behavior: 'smooth' }) }
  useEffect(() => { const handler = () => setRoute(location.hash.slice(1).split('/')[0] || 'home'); window.addEventListener('hashchange', handler); return () => window.removeEventListener('hashchange', handler) }, [])
  const content = useMemo(() => {
    const common = { session, openAuth: setAuthMode, notify }
    if (route === 'create') return <CreatePage {...common} refreshBalance={refreshBalance} preset={preset} go={go}/>
    if (route === 'knowledge') return <KnowledgePage {...common}/>
    if (route === 'logo') return <LogoPage {...common} preset={preset}/>
    if (route === 'pricing') return <PricingPage {...common}/>
    return <Home go={go}/>
  }, [route, session, preset])
  return <div className="app"><Header page={route} go={go} session={session} balance={balance} openAuth={setAuthMode} logout={() => {api.saveSession(null);setSession(null);setBalance(null);go('home');notify('已安全退出。')}}/>{content}<footer><div className="wrap"><div className="brand"><span className="seal">念</span><span>一念</span><small>AI 起名</small></div><p>让每一个名字，都有来处、有寓意、有未来。</p><span>© 2026 一念 AI</span></div></footer>{authMode && <AuthModal mode={authMode} close={() => setAuthMode(null)} onLogin={(data) => setSession(data)} notify={notify}/>}<Toast toast={toast} close={() => setToast(null)}/></div>
}

export default App
