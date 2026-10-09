// Business-section copy. Every factual line carries its docs/CONTENT.md reference.

export const company = {
  name: 'Skylark Exim',
  c1Short:
    'Skylark Exim, based in Visakhapatnam, Andhra Pradesh, is a trusted seafood exporter specialising in premium raw fresh, chilled and frozen seafood.', // C1 (first sentence)
  c1: 'Skylark Exim, based in Visakhapatnam, Andhra Pradesh, is a trusted seafood exporter specialising in premium raw fresh, chilled and frozen seafood. With a fully integrated value chain, we ensure complete control over quality, consistency and sustainability at every stage, from sourcing to delivery.', // C1
  c2: 'Our commitment to excellence is powered by advanced processing facilities, innovative technology, and strict adherence to international quality standards. Through strategic partnerships with aquaculture farmers and a focus on responsible sourcing, we guarantee superior freshness, traceability, and product integrity across all markets.', // C2
  c3: 'Today, Skylark Exim is recognised as one of India’s leading and globally trusted shrimp exporters, delivering world-class seafood solutions to customers worldwide.', // C3
  c4: 'Based in Vizag, Skylark Exim is a trusted seafood exporter delivering fresh and frozen seafood worldwide.', // C4
  c5: 'High professionalism and excellence', // C5
  c7: 'We deliver worldwide.', // C7
}

export const vision =
  'To be a trusted global leader in the seafood export industry by delivering premium-quality, sustainably sourced seafood to international markets, while building long-term partnerships and promoting responsible fishing practices for future generations.' // CONTENT §2 vision (Use)
export const mission =
  'Our mission is to deliver premium-quality seafood to global markets while ensuring sustainability, freshness, and customer satisfaction. We are committed to building long-term relationships with our clients by maintaining the highest standards of hygiene, ethical sourcing, and timely delivery.' // CONTENT §2 mission (Use)

export const quality = [
  { title: 'Quality control', line: 'Our quality control staff guarantee top-notch quality.' }, // W4
  {
    title: 'Processing facility',
    line: 'A state-of-the-art shrimp processing facility equipped with internationally acclaimed modernised equipment.',
  }, // F1
  { title: 'Storage', line: 'Our warehouse holds 700 pallets.' }, // F2
  {
    title: 'Lab and processing unit',
    line: 'Our lab unit and processing unit at Anandapuram, Visakhapatnam.',
  }, // F4
  {
    title: 'Compliance',
    line: 'Export certificates (HACCP, EU, FDA and others) and shipping in reefer containers that keep the cold chain unbroken to the destination.',
  }, // §5.9
  { title: 'Prompt delivery', line: 'Competent people for accurate order handling and prompt delivery.' }, // W1
  {
    title: 'Documentation',
    line: 'Our documentation staff prepare all necessary documents and track every shipment.',
  }, // W2
  {
    title: 'Best seafood, quickest time',
    line: 'We consider it our duty to provide the best seafood in the most effective manner and the quickest time.',
  }, // W3
]

// CONTENT §5 — the 9 steps, read forwards.
export const steps = [
  {
    n: '01',
    title: 'Raw material procurement',
    short: 'Sourced',
    line: 'Sourced directly from farms or fishing vessels. Checked for size, freshness and health before acceptance.',
  },
  {
    n: '02',
    title: 'Receiving & washing',
    short: 'Washed',
    line: 'Transported under chilled conditions to the processing plant. Washed thoroughly with clean, treated water.',
  },
  {
    n: '03',
    title: 'De-heading, peeling & deveining',
    short: 'Peeled',
    line: 'Head, shell and vein removed by hand or machine, to the product requirement: head-on, headless, peeled or value-added.',
  },
  {
    n: '04',
    title: 'Grading & sorting',
    short: 'Graded',
    line: 'Sorted by size, weight and type. Graded for uniformity to export standards.',
  },
  {
    n: '05',
    title: 'Quality control & inspection',
    short: 'Tested',
    line: 'Checked for hygiene, freshness, texture and defects. Samples tested for international food-safety compliance.',
  },
  {
    n: '06',
    title: 'Freezing & glazing',
    short: 'Frozen',
    line: 'Frozen by IQF (individually quick frozen) or block freezing, then glazed with a thin layer of ice to keep it fresh in transit.',
  },
  {
    n: '07',
    title: 'Packaging',
    short: 'Packed',
    line: 'Packed in export-grade cartons, vacuum packs or custom packaging, labelled with product, size, batch and export compliance.',
  },
  {
    n: '08',
    title: 'Cold storage',
    short: 'Stored',
    line: 'Held in −18 °C to −20 °C cold rooms until dispatch.',
  },
  {
    n: '09',
    title: 'Export documentation & logistics',
    short: 'Shipped',
    line: 'Export certificates (HACCP, EU, FDA and others) and shipping in reefer containers that keep the cold chain unbroken to the destination.',
  },
]

export const partners = ['V. Yashod Kumar', 'N.V. Prudhvi'] // CONTENT §8

export const contact = {
  phones: [
    { label: '+91-9000 604 070', href: 'tel:+919000604070' },
    { label: '+91-9885 827 318', href: 'tel:+919885827318' },
  ], // §9
  email: 'info@skylarkexim.com', // §9
  office: 'Sheela Nagar, Visakhapatnam, Andhra Pradesh', // §9
  plant:
    'Processing Unit: Abad Overseas Private Limited, S.No. 297/Part, Lodagalavanipalem, Anandapuram-Pendurthi Road, Anandapuram, Visakhapatnam-530052, Andhra Pradesh', // F3 verbatim
  profile: '/docs/skylark-exim-company-profile.pdf', // §9
}
