import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import md from '../../docs/LICENSES.md?raw'
import { renderMarkdown } from './markdown'
import Wordmark from '../ui/Wordmark'
import '../styles/tokens.css'
import '../styles/type.css'
import '../styles/global.css'
import './pages.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <header className="page-header">
      <a href="/">
        <Wordmark />
      </a>
    </header>
    <main id="main" className="page on-light" dangerouslySetInnerHTML={{ __html: renderMarkdown(md) }} />
  </StrictMode>,
)
