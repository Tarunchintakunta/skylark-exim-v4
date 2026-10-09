import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import Wordmark from '../ui/Wordmark'
import '../styles/tokens.css'
import '../styles/type.css'
import '../styles/global.css'
import './pages.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <main id="main" className="notfound">
      <a href="/" className="notfound-mark">
        <Wordmark />
      </a>
      <p className="eyebrow">Page not found</p>
      <h1 className="display">Off the route.</h1>
      <p className="lede">This page isn’t part of the journey.</p>
      <a className="btn-quote" href="/">
        Back to the start
      </a>
    </main>
  </StrictMode>,
)
