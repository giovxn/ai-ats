// Beyond the Scan deck: OVI's warm neutrals, a serif for titles, a clean sans for text, and one
// motif, the OVI halftone ball. Content and speaker notes are the original deck's.
const pptxgen = require('pptxgenjs')
// Optional: writes the palette into the deck's theme (from the pptx skill). Without it the deck still builds.
const applyTheme = process.env.PPTX_SKILL ? require(process.env.PPTX_SKILL + '/scripts/apply_theme.js').applyTheme : async () => {}
const notes = require('./notes.json')

const OUT = process.argv[2] || '../beyond-the-scan.pptx'
const COLOR = {
  bg: 'F6F3EE', surface: 'FFFDFA', sunken: 'ECE7DF', border: 'E3DDD3',
  text: '1C1A17', muted: '6B645A', gio: '46423B',
  amberBg: 'F6E7BD', amberText: '6E5410', amber: 'B08A2E', sage: '6B8F4E', sageText: '4D6B38', mutedIcon: '8C8478',
}
const THEME = {
  name: 'OVI x Gio',
  headFontFace: 'Georgia',
  bodyFontFace: 'Helvetica Neue',
  colors: {
    dk1: COLOR.text, lt1: COLOR.bg, dk2: COLOR.muted, lt2: COLOR.sunken,
    accent1: COLOR.amber, accent2: COLOR.sage, accent3: COLOR.sageText, accent4: COLOR.amberBg,
    accent5: '56789B', accent6: 'B0614F', hlink: COLOR.text, folHlink: COLOR.muted,
  },
}
const SERIF = 'Georgia', SANS = 'Helvetica Neue', LIGHT = 'Helvetica Neue Light', MONO = 'Menlo'
const W = 13.333, M = 0.75 // slide width, outer margin

const pres = new pptxgen()
pres.layout = 'LAYOUT_WIDE'
pres.author = 'Gio'
pres.title = 'Beyond the Scan'
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace }

const footer = [
  { image: { x: M, y: 6.94, w: 0.55, h: 0.25, path: 'logo.png' } },
  { text: { text: '× gio', options: { x: 1.39, y: 6.86, w: 1.2, h: 0.4, fontFace: LIGHT, fontSize: 13, color: COLOR.gio, margin: 0, valign: 'middle' } } },
]
pres.defineSlideMaster({
  title: 'CONTENT',
  background: { color: COLOR.bg },
  objects: [
    ...footer,
    { placeholder: { options: { name: 'title', type: 'title', x: M, y: 0.55, w: W - 2 * M, h: 0.9, fontFace: SERIF, fontSize: 34, color: COLOR.text, align: 'left', valign: 'top', margin: 0 }, text: '' } },
  ],
  slideNumber: { x: W - M - 0.6, y: 6.88, w: 0.6, h: 0.36, fontFace: SANS, fontSize: 11, color: COLOR.muted, align: 'right' },
})
pres.defineSlideMaster({ title: 'FEATURE', background: { color: COLOR.bg } }) // title, quote, closing: no footer

// ---------- helpers ----------
const text = (slide, value, opts) => slide.addText(value, { isTextBox: true, margin: 0, fontFace: SANS, color: COLOR.text, valign: 'top', ...opts })
const caps = (slide, value, opts) => text(slide, value.toUpperCase(), { fontSize: 11, bold: true, charSpacing: 1.5, color: COLOR.muted, ...opts })
const shadow = () => ({ type: 'outer', blur: 14, offset: 4, angle: 90, color: COLOR.text, opacity: 0.12 })
const shot = (slide, path, x, y, w, h, name) => slide.addImage({ path, x, y, w, h, shadow: shadow(), altText: name, objectName: name })
const sphere = (slide, x, y, d, transparency = 0) => slide.addImage({ path: 'sphere.png', x, y, w: d, h: d, transparency, altText: 'OVI halftone ball', objectName: 'Halftone ball' })
// Every content slide carries its part of the brief's 20 minutes, so OVI can follow the structure.
const PARTS = { 'Why': 'Live demo', 'What it does': 'Live demo', 'How it is built': 'How it works', 'Judgement': 'Why it works this way', 'Next': 'Next 2 weeks' }
const content = (title, section) => {
  const slide = pres.addSlide({ masterName: 'CONTENT', sectionTitle: section })
  slide.addText(PARTS[section].toUpperCase(), { isTextBox: true, margin: 0, x: M, y: 0.22, w: 6, h: 0.25, fontFace: SANS, fontSize: 10, bold: true, charSpacing: 1.5, color: COLOR.muted })
  slide.addText(title, { placeholder: 'title' })
  return slide
}
// The app's status shapes: filled (found / solved), half (partly), dashed ring (not covered).
function status(slide, kind, x, y, d = 0.24) {
  if (kind === 'full') slide.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: COLOR.sage }, line: { color: COLOR.sage, width: 1 } })
  if (kind === 'half') {
    slide.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { type: 'none' }, line: { color: COLOR.mutedIcon, width: 1.25 } })
    slide.addShape(pres.shapes.PIE, { x, y, w: d, h: d, angleRange: [90, 270], fill: { color: COLOR.mutedIcon }, line: { type: 'none' } })
  }
  if (kind === 'none') slide.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { type: 'none' }, line: { color: COLOR.mutedIcon, width: 1.25, dashType: 'dash' } })
}

// ---------- 1. Title ----------
pres.addSection({ title: 'Why' })
{
  const s = pres.addSlide({ masterName: 'FEATURE', sectionTitle: 'Why' })
  sphere(s, 7.55, 1.05, 6.6)
  s.addImage({ path: 'logo.png', x: M, y: 0.62, w: 0.92, h: 0.42, altText: 'OVI' })
  text(s, '× gio', { x: 1.75, y: 0.6, w: 1.6, h: 0.46, fontFace: LIGHT, fontSize: 21, color: COLOR.gio, valign: 'middle' })
  text(s, 'Beyond the Scan', { x: M, y: 2.45, w: 7.2, h: 1.2, fontFace: SERIF, fontSize: 64, valign: 'bottom' })
  text(s, "An AI-native ATS that makes sure a recruiter never rejects someone without seeing what's in their CV", { x: M, y: 3.85, w: 6.2, h: 1.1, fontSize: 20, color: COLOR.muted, lineSpacingMultiple: 1.15 })
  text(s, 'OVI internship case study, Gio, November 2026', { x: M, y: 6.6, w: 6.2, h: 0.35, fontSize: 13, color: COLOR.muted })
  s.addNotes(notes[0])
}

// ---------- 2. What I built ----------
{
  const s = content('What I built', 'Why')
  const blocks = [
    ['Block 1', 'Role setup', 'Paste a job description. AI pulls out title, location, must-haves and nice-to-haves. Discriminatory criteria are flagged, never used.'],
    ['Block 2', 'CV upload', 'PDF or text. AI turns each CV into a profile. Years are counted in code; duplicates and non-CVs are caught.'],
    ['Block 3', 'Pipeline', 'New, Shortlisted, Interview, Rejected. Open any candidate and move them by menu or drag.'],
    ['Block 4, the twist', 'Beyond the Scan', 'Older CV evidence surfaced right before a reject.'],
  ]
  const colW = 2.75, gap = 0.27
  blocks.forEach(([label, name, desc], i) => {
    const x = M + i * (colW + gap)
    if (i === 3) s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: x - 0.2, y: 1.65, w: colW + 0.4, h: 2.55, rectRadius: 0.12, fill: { color: COLOR.amberBg }, line: { type: 'none' }, objectName: 'Twist highlight' })
    caps(s, label, { x, y: 1.85, w: colW, h: 0.3, color: i === 3 ? COLOR.amberText : COLOR.muted })
    text(s, name, { x, y: 2.2, w: colW, h: 0.45, fontSize: 20, bold: true })
    text(s, desc, { x, y: 2.72, w: colW, h: 1.4, fontSize: 13.5, color: COLOR.muted, lineSpacingMultiple: 1.1 })
  })
  const stats = [['119', 'automated tests, OpenAI mocked'], ['18 / 18', 'manual Block 4 tests passed'], ['1 + 9', 'job ad and fictional PDF CVs in the demo']]
  stats.forEach(([n, label], i) => {
    const x = M + i * 3.95
    text(s, n, { x, y: 4.75, w: 3.6, h: 0.95, fontFace: LIGHT, fontSize: 56, valign: 'bottom' })
    text(s, label, { x, y: 5.75, w: 3.6, h: 0.4, fontSize: 14, color: COLOR.muted })
  })
  s.addNotes(notes[1])
}

// ---------- 3. Discovery ----------
{
  const s = content('Discovery: a 15-minute role-play interview', 'Why')
  text(s, 'Tim and Chris played a Head of Talent and a CHRO at Talabat, hiring an AI engineering intern', { x: M, y: 1.4, w: 10, h: 0.4, fontSize: 16, color: COLOR.muted })
  const stats = [
    ['1,000', 'applications in the first 2 days, from LinkedIn, email and even phone'],
    ['100', 'CVs actually read. The other 900 were never opened'],
    ['15–20 s', 'per CV, reading only the last 2 jobs'],
  ]
  stats.forEach(([n, label], i) => {
    const x = M + i * 3.95
    text(s, n, { x, y: 2.25, w: 3.7, h: 1.25, fontFace: LIGHT, fontSize: 76, valign: 'bottom', color: i === 2 ? COLOR.amberText : COLOR.text })
    text(s, label, { x, y: 3.65, w: 3.3, h: 0.8, fontSize: 15, color: COLOR.muted, lineSpacingMultiple: 1.1 })
  })
  text(s, 'Also heard: CVs are tracked in Excel, rejected people are “lost already”, and they wish for a co-worker that briefs them each morning.', { x: M, y: 5.05, w: 11, h: 0.5, fontSize: 15 })
  text(s, 'Role-play, not customer research: these are hypotheses to test with real recruiters.', { x: M, y: 5.65, w: 11, h: 0.4, fontSize: 13, italic: true, color: COLOR.muted })
  s.addNotes(notes[2])
}

// ---------- 4. The quote ----------
{
  const s = pres.addSlide({ masterName: 'FEATURE', sectionTitle: 'Why' })
  sphere(s, 9.35, 2.3, 5.6)
  text(s, '“I look at the last 2 positions and I scan it for like 15 to 20 seconds, and then I reject or go to the next.”', { x: M, y: 1.3, w: 8.4, h: 2.9, fontFace: SERIF, fontSize: 38, lineSpacingMultiple: 1.1, valign: 'bottom' })
  text(s, 'Chris, playing a CHRO', { x: M, y: 4.4, w: 6, h: 0.35, fontSize: 15, color: COLOR.muted })
  text(s, [
    { text: 'The insight: ', options: { bold: true } },
    { text: 'AI can already read every CV. The human still reads 2 jobs, and the evidence further down gets missed at the moment of rejection.' },
  ], { x: M, y: 5.35, w: 7.9, h: 0.9, fontSize: 17, lineSpacingMultiple: 1.15 })
  s.addNotes(notes[3])
}

// ---------- 5. Live demo ----------
pres.addSection({ title: 'What it does' })
{
  const s = content('Live demo', 'What it does')
  const steps = [
    'Create a role from a pasted job ad',
    'Upload all 9 CVs: AI turns each into a profile',
    'Move candidates through the pipeline',
    'Scan mode: reject James (no check), then Priya (check appears)',
  ]
  steps.forEach((step, i) => {
    const y = 1.75 + i * 0.95
    text(s, String(i + 1), { x: M, y, w: 0.45, h: 0.5, fontFace: LIGHT, fontSize: 28, color: COLOR.muted })
    text(s, step, { x: M + 0.55, y: y + 0.05, w: 4.55, h: 0.75, fontSize: 16, lineSpacingMultiple: 1.1 })
  })
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: M, y: 5.75, w: 4.55, h: 0.48, rectRadius: 0.08, fill: { color: COLOR.sunken }, line: { type: 'none' } })
  text(s, 'cd backend && uv run python reset_demo.py', { x: M + 0.18, y: 5.75, w: 4.3, h: 0.48, fontFace: MONO, fontSize: 11.5, valign: 'middle' })
  shot(s, 'board.png', 5.85, 2.05, 6.73, 2.71, 'Pipeline board screenshot')
  text(s, 'The pipeline board: 4 stages, one card per candidate', { x: 5.85, y: 4.98, w: 6.7, h: 0.35, fontSize: 12, color: COLOR.muted })
  s.addNotes(notes[4])
}

// ---------- 6. Beyond the Scan in 3 steps ----------
{
  const s = content('Beyond the Scan, in 3 steps', 'What it does')
  const steps = [
    ['AI reads the whole CV', 'For each must-have: the exact quote, and which job it comes from.'],
    ['Scan mode shows the last 2 jobs', "Like the recruiter's own habit. An amber note appears when a must-have only shows up in an older job."],
    ['Before you reject', 'The quote shows first. Look again, or Reject anyway. The recruiter always decides.'],
  ]
  steps.forEach(([head, desc], i) => {
    const y = 1.7 + i * 1.5
    text(s, String(i + 1), { x: M, y, w: 0.45, h: 0.5, fontFace: LIGHT, fontSize: 28, color: COLOR.muted })
    text(s, head, { x: M + 0.55, y: y + 0.04, w: 4.6, h: 0.4, fontSize: 19, bold: true })
    text(s, desc, { x: M + 0.55, y: y + 0.5, w: 4.6, h: 0.85, fontSize: 14, color: COLOR.muted, lineSpacingMultiple: 1.1 })
  })
  shot(s, 'scancard.png', 6.45, 1.6, 6.13, 4.3, 'Scan mode card screenshot')
  s.addNotes(notes[5])
}

// ---------- 7. The check ----------
{
  const s = content('The check only appears when it should', 'What it does')
  caps(s, 'Shown only when all 4 are true', { x: M, y: 1.65, w: 6, h: 0.3 })
  const rules = ["It's a must-have, not a nice-to-have", 'No evidence in the 2 jobs on the card', 'Evidence in an older job', "The quote is verified in that job's text"]
  rules.forEach((rule, i) => {
    const y = 2.15 + i * 0.6
    status(s, 'full', M, y + 0.05)
    text(s, rule, { x: M + 0.42, y, w: 5.9, h: 0.36, fontSize: 17, valign: 'middle' })
  })
  text(s, [
    { text: 'Never ', options: { bold: true, color: COLOR.text } },
    { text: 'blocks the recruiter, scores anyone, or changes a stage. Rejecting anyone else goes straight through. Every choice is logged; Undo adds a row instead of erasing one.' },
  ], { x: M, y: 4.85, w: 6.1, h: 1.1, fontSize: 14.5, color: COLOR.muted, lineSpacingMultiple: 1.15 })
  shot(s, 'check.png', 7.95, 1.5, 4.63, 4.59, 'Before you reject dialog screenshot')
  s.addNotes(notes[6])
}

// ---------- 8. Architecture ----------
pres.addSection({ title: 'How it is built' })
{
  const s = content('Architecture', 'How it is built')
  const nodes = [
    ['Browser', 'React, Vite, TypeScript', 'One page: role, board, profile, Scan mode'],
    ['API', 'FastAPI (Python)', 'Roles, uploads, stage moves, decisions'],
    ['Database', 'SQLite', 'roles, candidates, decisions'],
  ]
  const nodeW = 3.45, gap = 0.72
  nodes.forEach(([label, name, desc], i) => {
    const x = M + i * (nodeW + gap)
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.65, w: nodeW, h: 1.55, rectRadius: 0.12, fill: { color: COLOR.surface }, line: { color: COLOR.border, width: 0.75 } })
    caps(s, label, { x: x + 0.25, y: 1.85, w: nodeW - 0.5, h: 0.3 })
    text(s, name, { x: x + 0.25, y: 2.17, w: nodeW - 0.5, h: 0.4, fontSize: 18, bold: true })
    text(s, desc, { x: x + 0.25, y: 2.6, w: nodeW - 0.5, h: 0.5, fontSize: 13, color: COLOR.muted })
    if (i < 2) s.addShape(pres.shapes.LINE, { x: x + nodeW + 0.12, y: 2.42, w: gap - 0.24, h: 0, line: { color: COLOR.mutedIcon, width: 1.25, endArrowType: 'triangle' } })
  })
  // The API calls OpenAI through one function.
  const apiX = M + nodeW + gap + nodeW / 2
  s.addShape(pres.shapes.LINE, { x: apiX, y: 3.2, w: 0, h: 0.55, line: { color: COLOR.mutedIcon, width: 1.25, endArrowType: 'triangle' } })
  text(s, 'OpenAI (gpt-5.4-mini), structured outputs: 3 calls, one entry point', { x: M, y: 3.85, w: W - 2 * M, h: 0.4, fontSize: 15, bold: true, align: 'center' })
  const calls = [
    ['Role extraction', 'Job description → title, location, requirements, excluded criteria'],
    ['CV parsing', 'CV text → name, skills, jobs, education. Never judges'],
    ['Evidence check', 'CV × requirements → quotes, job index, duty / action / outcome'],
  ]
  calls.forEach(([name, desc], i) => {
    const x = M + i * (nodeW + gap)
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 4.45, w: nodeW, h: 1.35, rectRadius: 0.12, fill: { color: i === 2 ? COLOR.amberBg : COLOR.sunken }, line: { type: 'none' } })
    text(s, name, { x: x + 0.25, y: 4.65, w: nodeW - 0.5, h: 0.35, fontSize: 16, bold: true })
    text(s, desc, { x: x + 0.25, y: 5.03, w: nodeW - 0.5, h: 0.7, fontSize: 13, color: i === 2 ? COLOR.amberText : COLOR.muted })
  })
  s.addNotes(notes[7])
}

// ---------- 9. AI extracts. Code decides. ----------
{
  const s = content('AI extracts. Code decides.', 'How it is built')
  const ai = ['Pull requirements from a job description', 'Turn a CV into a profile', 'Find quotes for each requirement', 'Tag bullets as duty, action or outcome', 'Flag criteria about who someone is']
  const code = ['Count years of experience from job dates', "Check each quote is really in the CV, in that job's section", 'Decide if evidence is buried, and when to show the check', 'Find email, phone and links', 'Catch duplicate CVs by fingerprint']
  const list = (items) => items.map((t, i) => ({ text: t, options: { bullet: { indent: 16 }, breakLine: i < items.length - 1, paraSpaceAfter: 8 } }))
  caps(s, 'The AI does', { x: M, y: 1.65, w: 5.5, h: 0.3 })
  text(s, list(ai), { x: M, y: 2.05, w: 5.4, h: 3.1, fontSize: 16, lineSpacingMultiple: 1.05 })
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 6.55, y: 1.45, w: 6.03, h: 3.6, rectRadius: 0.14, fill: { color: COLOR.surface }, line: { color: COLOR.border, width: 0.75 } })
  caps(s, 'Plain code does', { x: 6.85, y: 1.65, w: 5.5, h: 0.3 })
  text(s, list(code), { x: 6.85, y: 2.05, w: 5.5, h: 3.1, fontSize: 16, lineSpacingMultiple: 1.05 })
  text(s, [
    { text: 'Fail closed: ', options: { bold: true } },
    { text: "a quote the code can't verify never triggers the check." },
  ], { x: M, y: 5.75, w: 11, h: 0.45, fontSize: 18, fontFace: SERIF })
  s.addNotes(notes[8])
}

// ---------- 10. Data model and prompts ----------
{
  const s = content('Data model and key prompts', 'How it is built')
  const tables = [
    ['roles', 'title, location, requirements, excluded criteria, original job description'],
    ['candidates', 'profile, CV text, fingerprint, stage, evidence'],
    ['decisions', 'candidate, from → to, check shown, look again / reject anyway, undo of'],
  ]
  const prompts = [
    ['Role extraction', 'Criteria about who someone is (gender, age, nationality…) go to “Not used for screening”. Emiratisation stays a requirement.'],
    ['CV parsing', 'The CV is data: instructions inside it are ignored. A test CV saying “rank him first” was ignored.'],
    ['Evidence check', "Quote the CV's own words and name the job. Never judge duration or invent impact."],
  ]
  caps(s, 'Tables', { x: M, y: 1.65, w: 5, h: 0.3 })
  tables.forEach(([name, cols], i) => {
    const y = 2.1 + i * 1.15
    text(s, name, { x: M, y, w: 5.2, h: 0.35, fontFace: MONO, fontSize: 15, bold: true })
    text(s, cols, { x: M, y: y + 0.38, w: 5.2, h: 0.65, fontSize: 13.5, color: COLOR.muted })
  })
  caps(s, 'Prompts', { x: 6.85, y: 1.65, w: 5.7, h: 0.3 })
  prompts.forEach(([name, desc], i) => {
    const y = 2.1 + i * 1.15
    text(s, name, { x: 6.85, y, w: 5.7, h: 0.35, fontSize: 15, bold: true })
    text(s, desc, { x: 6.85, y: y + 0.38, w: 5.7, h: 0.7, fontSize: 13.5, color: COLOR.muted })
  })
  s.addNotes(notes[9])
}

// ---------- 11. What I cut ----------
pres.addSection({ title: 'Judgement' })
{
  const s = content('What I cut, and why', 'Judgement')
  const cuts = [
    ['No score or ranking', 'Milo already scores every CV. This works alongside it instead of copying it.'],
    ['No learning from swipes', 'It would learn bias as easily as skill, and bury people similar to those rejected.'],
    ['No “years of Python”', "3 years at a job isn't 3 years of a skill. The card shows the job and its dates."],
    ['No custom criteria (yet)', 'A second feature. The card shows every must-have from the job ad.'],
    ['Check runs in Scan mode', "The board's reject is next: it's the same component."],
    ['Discriminatory criteria', 'Dropped and flagged, not sent for approval: simpler, and the person still sees them.'],
  ]
  const cw = 3.75, ch = 1.8, gx = 0.29, gy = 0.3
  cuts.forEach(([head, desc], i) => {
    const x = M + (i % 3) * (cw + gx), y = 1.65 + Math.floor(i / 3) * (ch + gy)
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: cw, h: ch, rectRadius: 0.12, fill: { color: COLOR.surface }, line: { color: COLOR.border, width: 0.75 } })
    text(s, head, { x: x + 0.28, y: y + 0.25, w: cw - 0.56, h: 0.4, fontSize: 17, bold: true })
    text(s, desc, { x: x + 0.28, y: y + 0.72, w: cw - 0.56, h: 1.1, fontSize: 13.5, color: COLOR.muted, lineSpacingMultiple: 1.1 })
  })
  s.addNotes(notes[10])
}

// ---------- 12. Where it can be wrong ----------
{
  const s = content("Where it can be wrong, and how I'd know it works", 'Judgement')
  const wrong = [
    ['Quote linked to the wrong requirement', 'Seen in testing: school software matched to “fintech”.'],
    ['Quote linked to the wrong job', "Checked in code against each job's section."],
    ["Old skills that aren't current", 'Shown with dates; the recruiter judges.'],
    ['Inflated CV claims', 'Labelled “as claimed in the CV”.'],
  ]
  const know = [
    ['Evidence accuracy', 'Do quotes support the requirement, in the right job?'],
    ['Useful-check rate', 'How often recruiters choose Look again'],
    ['Scan-gap rate', 'How often must-haves sit outside the last 2 jobs in real CVs'],
  ]
  const column = (title, items, x) => {
    caps(s, title, { x, y: 1.65, w: 5.6, h: 0.3 })
    items.forEach(([head, desc], i) => {
      const y = 2.05 + i * 0.8
      text(s, head, { x, y, w: 5.6, h: 0.32, fontSize: 15.5, bold: true })
      text(s, desc, { x, y: y + 0.33, w: 5.6, h: 0.35, fontSize: 13.5, color: COLOR.muted })
    })
  }
  column('Where it can be wrong', wrong, M)
  column("How I'd know it works", know, 6.85)
  text(s, "Success isn't more shortlists. It's better-informed decisions.", { x: M, y: 5.6, w: 11.8, h: 0.6, fontFace: SERIF, fontSize: 24 })
  s.addNotes(notes[11])
}

// ---------- 13. What it solves ----------
{
  const s = content("What it solves, and what it doesn't", 'Judgement')
  const rows = [
    ['Long CVs: only the last 2 jobs get read', 'full', 'Solved'],
    ['Good people rejected and “lost already”', 'full', 'Caught before the reject'],
    ['“Did they actually contribute value?”', 'half', 'Partly: duty / action / outcome labels'],
    ['900 of 1,000 CVs never opened', 'none', "Not this feature: that's Milo's job"],
    ['Excel tracking, scattered channels, morning briefing', 'none', 'Next steps'],
  ]
  rows.forEach(([pain, kind, verdict], i) => {
    const y = 1.7 + i * 0.86
    text(s, pain, { x: M, y, w: 6.4, h: 0.62, fontSize: 17, valign: 'middle' })
    status(s, kind, 7.45, y + 0.19)
    text(s, verdict, { x: 7.85, y, w: 4.75, h: 0.62, fontSize: 15, valign: 'middle', color: kind === 'full' ? COLOR.sageText : COLOR.muted, bold: kind === 'full' })
    if (i < rows.length - 1) s.addShape(pres.shapes.LINE, { x: M, y: y + 0.74, w: W - 2 * M, h: 0, line: { color: COLOR.border, width: 0.75 } })
  })
  s.addNotes(notes[12])
}

// ---------- 14. Next 2 weeks ----------
pres.addSection({ title: 'Next' })
{
  const s = content('Next 2 weeks', 'Next')
  const cols = [
    ['Week 1', 'Validate', ['Test on real, consented CVs', 'Measure the scan-gap rate', 'Ask recruiters if the check helps']],
    ['Week 2', 'Plug into Milo', ["Use Milo's per-requirement output as the evidence", 'Add the check to the board', 'Measure false alarms']],
    ['After that', 'One inbox, less Excel', ['Careers page, jobs@ email agent, LinkedIn import', 'No LinkedIn auto-rejects', 'Morning briefing, recruiter-chosen criteria']],
  ]
  const cw = 3.75, gx = 0.29
  s.addShape(pres.shapes.LINE, { x: M + 0.15, y: 1.96, w: 2 * (cw + gx), h: 0, line: { color: COLOR.border, width: 1.25 } })
  cols.forEach(([when, head, items], i) => {
    const x = M + i * (cw + gx)
    sphere(s, x, 1.78, 0.36)
    caps(s, when, { x, y: 2.4, w: cw, h: 0.3 })
    text(s, head, { x, y: 2.75, w: cw, h: 0.55, fontFace: SERIF, fontSize: 24 })
    text(s, items.map((t, j) => ({ text: t, options: { bullet: { indent: 14 }, breakLine: j < items.length - 1, paraSpaceAfter: 7 } })),
      { x, y: 3.45, w: cw - 0.2, h: 2.2, fontSize: 14.5, color: COLOR.muted, lineSpacingMultiple: 1.05 })
  })
  s.addNotes(notes[13])
}

// ---------- 15. Close ----------
{
  const s = pres.addSlide({ masterName: 'FEATURE', sectionTitle: 'Next' })
  sphere(s, 7.55, 1.05, 6.6)
  caps(s, 'Beyond the Scan', { x: M, y: 1.9, w: 5, h: 0.3 })
  text(s, "You don't have to read the whole CV. We just make sure you don't reject someone without seeing what's in it.", { x: M, y: 2.35, w: 7.0, h: 2.6, fontFace: SERIF, fontSize: 36, lineSpacingMultiple: 1.1 })
  text(s, 'Thank you. Questions?', { x: M, y: 5.35, w: 6, h: 0.45, fontSize: 18, color: COLOR.muted })
  s.addImage({ path: 'logo.png', x: M, y: 6.62, w: 0.68, h: 0.31, altText: 'OVI' })
  text(s, '× gio', { x: 1.5, y: 6.58, w: 1.4, h: 0.4, fontFace: LIGHT, fontSize: 16, color: COLOR.gio, valign: 'middle' })
  s.addNotes(notes[14])
}

pres.writeFile({ fileName: OUT }).then(async () => {
  await applyTheme(OUT, THEME)
  console.log('wrote', OUT)
})
