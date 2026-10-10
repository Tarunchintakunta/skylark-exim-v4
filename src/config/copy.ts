// Every factual sentence traces to docs/CONTENT.md (ref in the comment). Headlines without a claim are creative copy.
// "−18 °C": U+2212 minus + NBSP before °C; rendered in a nowrap span that SplitText does not split.

export interface ChapterCopy {
  eyebrow?: string
  headline: string
  line?: string
  closing?: string // shown at 85 % (v-sea only)
  hint?: string // v-table "Scroll" hint
}

export const MINUS18 = '−18 °C'
export const MINUS20 = '−20 °C'

export const filmCopy: Record<string, ChapterCopy> = {
  'v-table': {
    eyebrow: 'Skylark Exim · Visakhapatnam', // CONTENT §1 C1 (name + city)
    headline: 'Trace it back.', // creative
    line: 'Before it reached this table, it came a long way. Scroll to follow it home.', // creative, no claim
    hint: 'Scroll',
  },
  'v-reefer': {
    eyebrow: 'Step 9 · Export documentation & logistics', // CONTENT §5.9
    headline: 'Under a cold seal.', // creative
    line: 'Shipped in reefer containers that keep the cold chain unbroken to the destination.', // CONTENT §5.9
  },
  'v-port': {
    eyebrow: 'Step 9 · Export documentation & logistics', // CONTENT §5.9
    headline: 'Papers before ports.', // creative
    line: 'Our documentation staff prepare all necessary documents and track every shipment, in compliance with export certificates — HACCP, EU, FDA, etc.', // CONTENT W2 + §5.9
  },
  'v-cold': {
    eyebrow: 'Step 8 · Cold storage', // CONTENT §5.8
    headline: `Held at ${MINUS18} to ${MINUS20}.`, // CONTENT §5.8
    line: 'Cold rooms until dispatch. Our warehouse holds 700 pallets.', // CONTENT §5.8 + F2
  },
  'v-pack': {
    eyebrow: 'Step 7 · Packaging', // CONTENT §5.7
    headline: 'Packed and labelled.', // CONTENT §5.7
    line: 'Export-grade cartons, vacuum packs or custom packaging, labelled with product, size, batch and export compliance.', // CONTENT §5.7
  },
  'v-freeze': {
    eyebrow: 'Step 6 · Freezing & glazing', // CONTENT §5.6
    headline: 'Frozen, then glazed.', // CONTENT §5.6
    line: 'Frozen by IQF or block freezing, then glazed with a thin layer of ice to keep it fresh in transit.', // CONTENT §5.6
  },
  'v-qc': {
    eyebrow: 'Step 5 · Quality control & inspection', // CONTENT §5.5
    headline: 'Tested before it moves.', // CONTENT §5.5 (samples tested)
    line: 'Checked for hygiene, freshness, texture and defects. Samples tested for international food-safety compliance.', // CONTENT §5.5
  },
  'v-grade': {
    eyebrow: 'Step 4 · Grading & sorting', // CONTENT §5.4
    headline: 'Sorted by size, weight and type.', // CONTENT §5.4
    line: 'Graded for uniformity to export standards.', // CONTENT §5.4
  },
  'v-peel': {
    eyebrow: 'Step 3 · De-heading, peeling & deveining', // CONTENT §5.3
    headline: 'Made to order.', // CONTENT §5.3 (to the product requirement)
    line: 'Head, shell and vein removed by hand or machine, to the product requirement: head-on, headless, peeled or value-added.', // CONTENT §5.3
  },
  'v-wash': {
    eyebrow: 'Step 2 · Receiving & washing', // CONTENT §5.2
    headline: 'Washed clean.', // CONTENT §5.2
    line: 'Washed thoroughly with clean, treated water to remove impurities.', // CONTENT §5.2
  },
  'v-truck': {
    eyebrow: 'Step 2 · Receiving', // CONTENT §5.2
    headline: 'Kept chilled on the road.', // CONTENT §5.2
    line: 'Transported under chilled conditions to our processing plant at Anandapuram, Visakhapatnam.', // CONTENT §5.2 + F3
  },
  'v-pond': {
    eyebrow: 'Step 1 · Raw material procurement', // CONTENT §5.1
    headline: 'Raised with partner farmers.', // CONTENT C2 (partnerships with aquaculture farmers)
    line: 'Strategic partnerships with aquaculture farmers and a focus on responsible sourcing.', // CONTENT C2
  },
  'v-sea': {
    eyebrow: 'Step 1 · Raw material procurement', // CONTENT §5.1
    headline: 'Landed at dawn.', // creative (scene description; no claim beyond §5.1 fishing vessels)
    line: 'Sourced directly from farms or fishing vessels, and checked for size, freshness and health before acceptance.', // CONTENT §5.1
    closing: 'This is where it starts.', // creative
  },
}
