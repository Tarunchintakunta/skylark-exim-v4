import Film from './film/Film'
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
      </main>
      <StickyRfq />
      <Loader />
    </>
  )
}
