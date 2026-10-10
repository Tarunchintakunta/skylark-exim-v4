// CONTENT §6 — the only products v4 may name.
export const marineFish = [
  'Indian Mackerel',
  'Tuna',
  'Swordfish',
  'Cuttlefish',
  'Squid',
  'Leatherjacket',
  'Ribbon Fish',
  'Seer Fish',
]
export const shrimps = [
  'Vannamei',
  'Black Tiger Shrimp',
  'Sea White Shrimp',
  'Pink / Brown',
  'Sea Tiger Shrimp',
]
export const shrimpForms = [
  { form: 'Head-on, shell-on', options: 'Vannamei, Black Tiger' },
  { form: 'Headless, shell-on', options: 'Vannamei, Black Tiger' },
  { form: 'PUD', options: 'Vannamei' },
  { form: 'Peeled & deveined', options: 'tail-on or tail-off' },
  { form: 'Pin-deveined', options: 'tail-on or tail-off' },
  { form: 'Easy peel', options: 'Vannamei, Black Tiger' },
]
export const states = ['Raw fresh', 'Chilled', 'Frozen'] // C1
export const categories = { 'Marine fish': marineFish, Shrimps: shrimps } as const
export type Category = keyof typeof categories
