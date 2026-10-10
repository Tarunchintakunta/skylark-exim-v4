/* eslint-disable react/immutability -- three.js objects are mutated per frame by design (R3F useFrame) */
import { Canvas, useFrame, useThree } from '@react-three/fiber'
import { useGLTF } from '@react-three/drei'
import { Suspense, useEffect, useMemo } from 'react'
import { ACESFilmicToneMapping, AnimationMixer, Box3, PMREMGenerator, Vector3, type Group } from 'three'
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js'
import Guard from './Guard'
import { MODEL_URL, stage3d, type ModelId } from './store'

/** Procedural studio light (no HDRI download): RoomEnvironment through PMREM. */
function Studio() {
  const { gl, scene } = useThree()
  useEffect(() => {
    const pm = new PMREMGenerator(gl)
    const env = pm.fromScene(new RoomEnvironment(), 0.04).texture
    scene.environment = env
    return () => {
      env.dispose()
      pm.dispose()
    }
  }, [gl, scene])
  return null
}

function Model({ id }: { id: ModelId }) {
  const gltf = useGLTF(MODEL_URL[id], false, true)
  const { root, mixer, action, duration, scale } = useMemo(() => {
    const root = gltf.scene.clone(true) as Group
    const size = new Box3().setFromObject(root).getSize(new Vector3())
    const scale = 1.35 / Math.max(size.x, size.y, size.z)
    const clip = gltf.animations[0]
    const mixer = clip ? new AnimationMixer(root) : null
    const action = mixer && clip ? mixer.clipAction(clip).play() : null
    return { root, mixer, action, duration: clip?.duration ?? 0, scale }
  }, [gltf])

  useFrame(() => {
    const on = stage3d.model === id
    root.visible = on && stage3d.visible > 0.01
    if (!on) return
    const p = stage3d.progress
    // Carton: 1.5 turns and the lid opens over the second half (STORYBOARD B1). Products: one slow turn.
    root.rotation.y = id === 'carton' ? p * Math.PI * 3 : -0.6 + p * Math.PI * 2
    root.rotation.x = id === 'carton' ? 0.35 : 0.12
    // Scrubbed, not played: set the clip time directly, then evaluate with a zero step.
    if (mixer && action) {
      action.time = Math.min(1, Math.max(0, (p - 0.45) / 0.45)) * duration * 0.999
      mixer.update(0)
    }
    const s =
      scale *
      (stage3d.mobile ? (id === 'carton' ? 0.45 : 0.7) : id === 'carton' ? 0.9 : 1) *
      (0.92 + 0.08 * stage3d.visible)
    root.scale.setScalar(s)
    // Desktop: the carton sits right of centre so the left-hand copy stays clear.
    root.position.x = id === 'carton' ? (stage3d.mobile ? 0.3 : 0.75) : 0
    root.position.y = id === 'carton' ? (stage3d.mobile ? 0.3 : -0.1) : stage3d.mobile ? 0.15 : 0
  })
  return <primitive object={root} />
}

function Invalidator() {
  const { invalidate } = useThree()
  useEffect(() => {
    stage3d.invalidate = invalidate
    return () => {
      stage3d.invalidate = () => {}
    }
  }, [invalidate])
  return null
}

export default function CanvasRoot({ models }: { models: ModelId[] }) {
  return (
    <Canvas
      className="canvas3d"
      dpr={stage3d.mobile ? [1, 1.5] : [1, 1.75]}
      gl={{ antialias: false, powerPreference: 'high-performance', stencil: false, alpha: true }}
      frameloop="demand"
      camera={{ position: [0, 0.4, 4.2], fov: 32 }}
      onCreated={({ gl }) => {
        gl.toneMapping = ACESFilmicToneMapping
        gl.toneMappingExposure = 1.05
      }}
    >
      <Invalidator />
      <Studio />
      <directionalLight position={[3, 4, 2]} intensity={1.2} />
      {models.map((m) => (
        <Guard key={m}>
          <Suspense fallback={null}>
            <Model id={m} />
          </Suspense>
        </Guard>
      ))}
    </Canvas>
  )
}
