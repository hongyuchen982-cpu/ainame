import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './styles.css'

class AppErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { error: null }
  }

  static getDerivedStateFromError(error) {
    return { error }
  }

  render() {
    if (this.state.error) {
      return (
        <main className="fatal-error">
          <span className="seal">念</span>
          <h1>页面暂时没有加载成功</h1>
          <p>{this.state.error.message || '发生了未知的前端错误'}</p>
          <button className="red-button" onClick={() => window.location.reload()}>重新加载</button>
        </main>
      )
    }
    return this.props.children
  }
}

clearTimeout(window.__qimingBootTimer)
ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode><AppErrorBoundary><App /></AppErrorBoundary></React.StrictMode>,
)
