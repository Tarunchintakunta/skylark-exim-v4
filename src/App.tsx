import { lazy, Suspense, useEffect, useState } from 'react'
import Film from './film/Film'
import Header from './ui/Header'
import Loader from './ui/Loader'
import Chroma from './ui/Chroma'

// Split the first frame from the rest: the sections below the film (and zod, three, their CSS) parse and lay out in
// their own chunk once the browser is idle, so the load frame stays well under 50 ms (QUALITY_GATES G-SITE-5).
const Rest = lazy(() => import('./Rest'))
const Footer = lazy(() => import('./Rest').then((m) => ({ default: m.Footer })))

function useIdle(timeout = 800) {
  const [idle, setIdle] = useState(false)
  useEffect(() => {
    const go = () => setIdle(true)
    if ('requestIdleCallback' in window) {
      const id = requestIdleCallback(go, { timeout })
      return () => cancelIdleCallback(id)
    }
    const t = setTimeout(go, 200)
    return () => clearTimeout(t)
  }, [timeout])
  return idle
}

export default function App() {
  const idle = useIdle()
  return (
    <>
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      <a className="skip-link" href="#quote">
        Skip to request a quote
      </a>
      <Chroma />
      <Header />
      <main id="main">
        <Film />
        <Suspense fallback={null}>{idle && <Rest />}</Suspense>
      </main>
      <Suspense fallback={null}>{idle && <Footer />}</Suspense>
      <Loader />
    </>
  )
}
