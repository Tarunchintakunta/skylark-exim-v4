import { endPosterUrl } from '../config/media'
import { company, mission, partners, vision } from '../config/site'

/** B5 · The people behind it — no photos, no invented titles (CONTENT §8). */
export default function People() {
  return (
    <section id="people" className="sec sec-dark people" aria-labelledby="people-title">
      <img
        className="people-bg"
        src={endPosterUrl('v-sea', 1280)}
        alt=""
        width={1280}
        height={720}
        loading="lazy"
        decoding="async"
      />
      <div className="sec-inner people-inner">
        <p className="eyebrow">The people behind it</p>
        <h2 id="people-title" className="h2 sec-title">
          Managing partners
        </h2>
        <ul className="partners">
          {partners.map((p) => (
            <li key={p} className="display partner">
              {p}
            </li>
          ))}
        </ul>
        <div className="vm">
          <div>
            <h3 className="eyebrow">Vision</h3>
            <p>{vision}</p>
          </div>
          <div>
            <h3 className="eyebrow">Mission</h3>
            <p>{mission}</p>
          </div>
        </div>
        <p className="lede people-c3">{company.c3}</p>
      </div>
    </section>
  )
}
