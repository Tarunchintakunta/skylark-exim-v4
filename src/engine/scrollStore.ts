// Mutable progress store read by refs (no per-frame React state, TRD §2).
export const scrollStore = {
  chapter: 0,
  progress: 0, // 0..1 within the current film chapter
  direction: 1 as 1 | -1,
  inFilm: true,
  started: false, // set on the first user scroll/touch/key: nothing heavy is requested before it
}
