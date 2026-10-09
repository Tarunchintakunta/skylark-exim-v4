import { lazy, Suspense, useEffect, useRef, useState } from 'react'
import Guard from './Guard'
import { onTick } from '../engine/clock'
import { isMobile } from '../engine/env'
import { stage3d, type ModelId } from './store'

const CanvasRoot = lazy(() => import('./CanvasRoot'))

export default function Stage3D({ models }: { models: ModelId[] }) {
  const [mounted, setMounted] = useState(false)
  const box = useRef<HTMLDivElement>(null)
  useEffect(() => {
    stage3d.mobile = isMobile
    const zone = document.querySelector('[data-3d-zone]')
    if (!zone) return
    const io = new IntersectionObserver(([e]) => setMounted(e.isIntersecting), {
      rootMargin: '200% 0px 100% 0px',
    })
    io.observe(zone)
    let last = -1
    const off = onTick(() => {
      const v = stage3d.visible
      if (v !== last) {
        last = v
        if (box.current) box.current.style.opacity = String(v)
      }
      if (stage3d.model) stage3d.invalidate()
    })
    return () => {
      io.disconnect()
      off()
    }
  }, [])
  return (
    <div ref={box} className="stage3d" aria-hidden="true">
      {mounted && (
        <Guard>
          <Suspense fallback={null}>
            <CanvasRoot models={models} />
          </Suspense>
        </Guard>
      )}
    </div>
  )
}
