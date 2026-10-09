import { nav } from '../config/nav'
import { company, contact } from '../config/site'
import Wordmark from '../ui/Wordmark'

export default function Footer() {
  return (
    <footer className="footer sec-dark">
      <div className="sec-inner footer-grid">
        <div>
          <Wordmark className="footer-mark" />
          <p className="footer-c4">{company.c4}</p>
        </div>
        <nav aria-label="Footer">
          <ul className="footer-nav">
            {nav.map((n) => (
              <li key={n.href}>
                <a href={n.href}>{n.label}</a>
              </li>
            ))}
          </ul>
        </nav>
        <div className="footer-contact">
          {contact.phones.map((p) => (
            <a key={p.href} className="tnum" href={p.href}>
              {p.label}
            </a>
          ))}
          <a href={`mailto:${contact.email}`}>{contact.email}</a>
          <span>{contact.office}</span>
        </div>
      </div>
      <div className="sec-inner footer-base">
        <span>© Skylark Exim</span>
        <span>Made in Blender. No AI imagery.</span>
        <a href="/licenses">Licences</a>
      </div>
    </footer>
  )
}
