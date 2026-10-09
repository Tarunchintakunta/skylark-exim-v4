// Typographic wordmark. The live logo is a raster illustration; a vector lock-up is [CONFIRM] with Tarun (CONTENT §9).
export default function Wordmark({ className = '' }: { className?: string }) {
  return (
    <span className={`wordmark ${className}`}>
      Skylark <span className="wordmark-exim">Exim</span>
    </span>
  )
}
