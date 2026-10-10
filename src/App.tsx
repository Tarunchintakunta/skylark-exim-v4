import Film from './film/Film'
import NowForward from './sections/NowForward'
import Stage3D from './three/Stage3D'
import Quality from './sections/Quality'
import Markets from './sections/Markets'
import People from './sections/People'
import Quote from './sections/Quote'
import Footer from './sections/Footer'
import './sections/sections.css'
import Header from './ui/Header'
import Loader from './ui/Loader'
import StickyRfq from './ui/StickyRfq'

export default function App() {
  return (
    <>
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      <a className="skip-link" href="#quote">
        Skip to request a quote
      </a>
      <Header />
      <main id="main">
        <Film />
        <div data-3d-zone>
          <NowForward />
        </div>
        <Quality />
        <Markets />
        <People />
        <Quote />
      </main>
      <Footer />
      <Stage3D models={['carton']} />
      <StickyRfq />
      <Loader />
    </>
  )
}
