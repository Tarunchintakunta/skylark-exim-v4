// What the single 3D canvas shows right now; written by sections on the gsap tick, read in useFrame.
// Swordfish failed G-PROD-2 (CG-looking) and is a text entry only (see PR #11).
export type ModelId = 'carton' | 'tuna' | 'prawn'
export const stage3d = {
  model: null as ModelId | null,
  progress: 0, // 0..1 within the active section
  visible: 0, // 0..1 fade
  mobile: false,
  invalidate: () => {},
}

export const MODEL_URL: Record<ModelId, string> = {
  carton: '/models/hero-carton.glb',
  tuna: '/models/tuna.glb',
  prawn: '/models/prawn.glb',
}
