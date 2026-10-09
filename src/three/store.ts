// What the single 3D canvas shows right now; written by sections on the gsap tick, read in useFrame.
export type ModelId = 'carton' | 'tuna' | 'prawn' | 'swordfish'
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
  swordfish: '/models/swordfish.glb',
}
