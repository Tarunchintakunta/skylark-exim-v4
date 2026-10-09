import { useEffect, useRef } from 'react'
import Wordmark from './Wordmark'

/** No progress bar: ink + wordmark until the first poster has decoded and fonts are ready (max 1.2 s). */
export default function Loader() {
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => {
    const el = ref.current!
    const poster = document.querySelector<HTMLImageElement>('.stage-media')
    const ready = Promise.all([
      document.fonts.ready,
      poster ? poster.decode().catch(() => undefined) : Promise.resolve(),
    ])
    const cap = new Promise((r) => setTimeout(r, 1200))
    Promise.race([ready, cap]).then(() => el.classList.add('is-done'))
  }, [])
  return (
    <div ref={ref} className="loader" aria-hidden="true">
      <Wordmark className="loader-mark" />
    </div>
  )
}
