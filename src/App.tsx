import Film from './film/Film'
import Quality from './sections/Quality'
import People from './sections/People'
import Quote from './sections/Quote'
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
        <Quality />
        <People />
        <Quote />
      </main>
      <StickyRfq />
      <Loader />
    </>
  )
}
