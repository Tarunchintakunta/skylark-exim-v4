import { useEffect } from 'react'
import NowForward from './sections/NowForward'
import Products from './sections/Products'
import Stage3D from './three/Stage3D'
import Quality from './sections/Quality'
import Markets from './sections/Markets'
import People from './sections/People'
import Quote from './sections/Quote'
import Footer from './sections/Footer'
import './sections/sections.css'
import StickyRfq from './ui/StickyRfq'
import { scrollToEl } from './engine/clock'

/** Everything below the film: its own chunk, mounted once the first frame is up (App.tsx). */
export default function Rest() {
  useEffect(() => {
    // A deep link (#quote, #products …) could not land before these sections existed.
    if (location.hash.length > 1) scrollToEl(document.querySelector(location.hash))
  }, [])
  return (
    <>
      <div data-3d-zone>
        <NowForward />
        <Products />
      </div>
      <Quality />
      <Markets />
      <People />
      <Quote />
      <Stage3D models={['carton', 'tuna', 'prawn']} />
      <StickyRfq />
    </>
  )
}

export { Footer }
