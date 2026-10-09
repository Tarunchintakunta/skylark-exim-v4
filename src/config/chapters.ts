// Film chapters in scroll order — docs/STORYBOARD.md (frame ranges in scripts/scenes.sh). Copy lives in copy.ts.
export type TypeZone = 'tl' | 'tr' | 'l' | 'r' | 'top' | 'bottom'

export interface ChapterDef {
  id: string // clip id = public/media/<id>_<tier>.mp4
  vh: number // desktop pinned length (≈ 40 vh per second of clip)
  mobileVh?: number // default 0.8 × vh
  countdown?: string
  typeZone: TypeZone
  objectPosition: string // mobile crop
  alt: string
}

export const chapters: ChapterDef[] = [
  {
    id: 'v-table',
    vh: 360,
    typeZone: 'tl',
    objectPosition: '60% 50%',
    alt: 'A dinner table with grilled shrimp and tuna; an opened Skylark Exim carton of frozen shrimp on the counter.',
  },
  {
    id: 'v-reefer',
    vh: 320,
    countdown: '09',
    typeZone: 'r',
    objectPosition: '50% 50%',
    alt: 'Cartons of frozen shrimp inside a refrigerated container, then the container ship at sea.',
  },
  {
    id: 'v-port',
    vh: 440,
    mobileVh: 440 * 0.9,
    countdown: '09',
    typeZone: 'top',
    objectPosition: '55% 50%',
    alt: 'A crane lowers a white refrigerated container onto a ship at the Visakhapatnam port while staff check export documents.',
  },
  {
    id: 'v-cold',
    vh: 320,
    countdown: '08',
    typeZone: 'l',
    objectPosition: '40% 50%',
    alt: 'Frosted pallet racks in a cold store; a forklift operator in a thermal suit moves a pallet of cartons.',
  },
  {
    id: 'v-pack',
    vh: 320,
    countdown: '07',
    typeZone: 'top',
    objectPosition: '50% 50%',
    alt: 'Workers in hairnets, masks and gloves pack frozen shrimp into Skylark Exim cartons.',
  },
  {
    id: 'v-freeze',
    vh: 320,
    countdown: '06',
    typeZone: 'l',
    objectPosition: '50% 50%',
    alt: 'Individually quick-frozen shrimp leave a freezer tunnel under a fine glazing spray.',
  },
  {
    id: 'v-qc',
    vh: 320,
    countdown: '05',
    typeZone: 'tr',
    objectPosition: '45% 50%',
    alt: 'A lab technician checks shrimp samples at the quality-control bench.',
  },
  {
    id: 'v-grade',
    vh: 320,
    countdown: '04',
    typeZone: 'top',
    objectPosition: '50% 50%',
    alt: 'Shrimp roll through a grading machine into crates by size.',
  },
  {
    id: 'v-peel',
    vh: 320,
    countdown: '03',
    typeZone: 'top',
    objectPosition: '50% 50%',
    alt: 'Rows of workers in masks and gloves peel and devein shrimp on ice.',
  },
  {
    id: 'v-wash',
    vh: 320,
    countdown: '02',
    typeZone: 'l',
    objectPosition: '50% 50%',
    alt: 'Shrimp are washed in a stainless tank at the receiving bay.',
  },
  {
    id: 'v-truck',
    vh: 360,
    countdown: '02',
    typeZone: 'top',
    objectPosition: '50% 50%',
    alt: 'A refrigerated truck at the plant dock in Anandapuram, then the road toward the coast.',
  },
  {
    id: 'v-pond',
    vh: 360,
    countdown: '01',
    typeZone: 'top',
    objectPosition: '55% 50%',
    alt: 'Farmers lift a net of shrimp from a pond at sunrise; aerators turn the water.',
  },
  {
    id: 'v-sea',
    vh: 440,
    countdown: '01',
    typeZone: 'top',
    objectPosition: '50% 50%',
    alt: 'A fishing crew hauls and sorts its catch on ice at dawn off the Visakhapatnam coast.',
  },
]
