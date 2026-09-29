// Build workshop/exercises.pdf with Codex's bundled presentation runtime.
// Required: PRESENTATIONS_SKILL_DIR, RUNTIME_NODE_MODULES, RUNTIME_PYTHON.
// Optional: RUNTIME_SOFFICE. Intermediate files stay in the system temp folder.
import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import { spawnSync } from 'node:child_process';
import { createRequire } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';

const repo = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const skillDir = process.env.PRESENTATIONS_SKILL_DIR;
const modules = process.env.RUNTIME_NODE_MODULES;
if (!skillDir || !modules || !process.env.RUNTIME_PYTHON) throw new Error('Load Codex workspace dependencies first.');
const require = createRequire(path.join(modules, '__psc_exercises__.cjs'));
const { Presentation, PresentationFile } = await import(pathToFileURL(require.resolve('@oai/artifact-tool')).href);
const { finalizePresentation, resolvePresentationFont } = await import(pathToFileURL(path.join(skillDir, 'container_tools/artifact_tool_utils.mjs')).href);
const family = resolvePresentationFont({ fontFamily: 'Arial' });
const deck = Presentation.create({ slideSize: { width: 1280, height: 720 } });
const ink = '#172C31', accent = '#147477', muted = '#536166';
const assets = path.join(repo, 'workshop/assets/exercises');

function text(s, value, x, y, w, h, size = 26, opt = {}) {
  const a = s.shapes.add({ geometry: 'textbox', position: { left: x, top: y, width: w, height: h }, fill: 'none', line: { fill: 'none', width: 0 } });
  a.text = value;
  a.text.style = { typeface: family, fontSize: size, color: opt.color || ink, bold: opt.bold || false,
    autoFit: 'none', wrap: 'none', verticalAlignment: 'top', alignment: opt.align || 'left',
    insets: { left: 0, right: 0, top: 0, bottom: 0 } };
  if (opt.link) a.text.get(value).link = { uri: opt.link, isExternal: true };
  return a;
}
function page(title, notes, size = 44) {
  const s = deck.slides.add(); s.background.fill = '#FFFFFF';
  if (title) text(s, title, 64, 38, 1152, 64, size, { bold: true, color: accent });
  text(s, String(deck.slides.items.length), 1168, 677, 48, 24, 17, { color: muted, align: 'right' });
  s.speakerNotes.textFrame.setText(notes);
  return s;
}
function line(s, x, y, w, h, color = '#A7B9B8', width = 2) {
  return s.shapes.add({ geometry: 'line', position: { left: x, top: y, width: w, height: h }, fill: 'none', line: { fill: color, width, style: 'solid' } });
}
function arrow(s, x, y, size = 34) { return text(s, '→', x, y, 48, 48, size, { color: accent }); }
function diagramArrow(s, x1, x2, y) {
  const anchor = (x) => s.shapes.add({ geometry: 'rect',
    position: { left: x - 0.5, top: y - 0.5, width: 1, height: 1 },
    fill: 'none', line: { fill: 'none', width: 0 } });
  return s.shapes.connect(anchor(x1), anchor(x2), {
    kind: 'straight', fromSide: 'right', toSide: 'left',
    line: { style: 'solid', fill: accent, width: 2 },
    tail: { type: 'triangle', width: 'med', length: 'med' },
  });
}
async function picture(s, file, alt, x, y, w, h, crop) {
  s.images.add({ blob: new Uint8Array(await fs.readFile(path.join(assets, file))), contentType: 'image/png',
    alt, fit: crop ? 'cover' : 'contain', ...(crop ? { crop } : {}), position: { left: x, top: y, width: w, height: h } });
}

let s = page('', 'Presenter: Hongyuan Zhang, hongyuan.zhang@usys.ethz.ch. PSC workshop, 30 September 2026. '
  + 'ETH logo: unmodified inline SVG from https://ethz.ch/en.html, retrieved 29 September 2026. '
  + 'Placement guidance: https://ethz.ch/staffnet/en/service/communication/corporate-design/logo.html');
s.images.add({ svg: await fs.readFile(path.join(assets, 'eth-logo.svg'), 'utf8'), alt: 'ETH Zürich',
  position: { left: 64, top: 64, width: 270, height: 45 } });
text(s, 'Agentic workflows\nfor literature research', 64, 230, 1140, 170, 62, { bold: true, color: accent });
text(s, 'Hongyuan Zhang', 64, 480, 900, 44, 32, { bold: true });
text(s, 'hongyuan.zhang@usys.ethz.ch', 64, 531, 1000, 42, 28,
  { color: muted, link: 'mailto:hongyuan.zhang@usys.ethz.ch' });

s = page('The double edge of AI agents',
  'Left: real screenshot of the official OpenClaw homepage, https://openclaw.ai/, captured 29 September 2026. '
  + 'The screenshot shows the official mascot and describes everyday tasks performed through existing chat apps. '
  + 'Optional spoken example: Peter Steinberger describes an early OpenClaw predecessor processing a voice message by choosing tools it already had. '
  + 'https://lexfridman.com/peter-steinberger-transcript/ (15:16–17:37). This is the creator\'s account. '
  + 'Moltbook: https://www.moltbook.com/ describes itself as a social network for AI agents. '
  + 'Right: GeekWire, 20 September 2026, https://www.geekwire.com/2026/amazon-blocks-metas-muse-ai-assistant-in-new-standoff-over-agentic-shopping/. '
  + 'Amazon cited privacy and security concerns about agent access. This is not evidence of a confirmed data breach. Meta disputed the characterization. '
  + 'Response: https://research.meta.ai/blog/security-and-safety-for-ai-agents-our-approach-with-muse.');
await picture(s, 'openclaw-official-2026-09-29.png', 'Official OpenClaw homepage with its mascot and everyday tasks',
  64, 120, 470 * 651 / 550, 470, { left: 0, top: 42 / 878, right: 0, bottom: (878 - 592) / 878 });
await picture(s, 'amazon-muse-news-2026-09-28.png', 'GeekWire report on Amazon blocking Meta Muse',
  674, 120, 470 * 788 / 720, 470, { left: 76 / 1280, top: 0, right: (1280 - 864) / 1280, bottom: 0 });
text(s, 'moltbook.com', 64, 651, 250, 28, 20, { color: accent, link: 'https://www.moltbook.com/' });

s = page('Before the exercises',
  'Workshop guidance provided by Hongyuan Zhang. ETH-Guest or eduroam may not provide access to every licensed tool or journal; '
  + 'participants should use their own institution\'s VPN. Hongyuan has tested the UZH VPN. '
  + 'Recommended workshop model: GPT-5.6 or newer, with High reasoning or above. '
  + 'The free Luna model was slow and missed instructions in the workshop preparation tests; this is a report of those tests, not a universal model benchmark. '
  + 'Use visible browser tabs during the exercises to observe agent behaviour. Use background tabs for routine daily work. '
  + 'Real publisher verification screenshot supplied by Hongyuan: Screenshot 2026-09-29 at 15.44.56.png. '
  + 'Only whitespace is cropped for the slide; the security-check content is unchanged.');
text(s, 'Use your institution’s VPN', 64, 155, 554, 42, 28, { bold: true, color: accent });
text(s, 'ETH-Guest / eduroam may lack access.\nUZH VPN tested.', 64, 208, 554, 72, 25);
text(s, 'GPT-5.6+ · High reasoning or above', 64, 328, 554, 42, 28, { bold: true, color: accent });
text(s, 'Free Luna was slow and missed instructions\nin our tests.', 64, 381, 554, 72, 25);
text(s, 'Visible tabs for the workshop', 64, 501, 554, 42, 28, { bold: true, color: accent });
text(s, 'Observe the agent as it works.\nUse background tabs for daily searches.', 64, 554, 554, 72, 25);
text(s, 'Example: website security check', 670, 215, 546, 40, 26, { bold: true, color: accent });
await picture(s, 'publisher-security-check-2026-09-29.png', 'Wiley performing security verification',
  670, 282, 546, 546 * 460 / 1312,
  { left: 24 / 1366, top: 120 / 876, right: 30 / 1366, bottom: (876 - 580) / 876 });
text(s, 'Wait for verification; respond if prompted.', 670, 505, 546, 40, 24);

s = page('Exercise 1 · Compare search tools',
  'Use skills/paper-search in comparison mode. Students choose a topic they know and identify expected key papers before searching. '
  + 'Hold the topic, filters and paper limit constant. Compare each source\'s own results. '
  + 'Save the comparison and explicitly chosen preferred tools through paper-search research artifacts for paper-watch. No invented tool rankings are shown.');
text(s, 'Choose search tools that find your field’s key papers.', 64, 116, 1152, 46, 29, { bold: true });
const steps = [
  ['Choose a familiar topic', 'List its key papers as your ground truth.'],
  ['Use @paper-search in comparison mode', 'Use the same topic, filters and paper limit.'],
  ['Compare coverage and ranking', 'Which key papers appear? Which are missing?'],
];
for (const [i, [heading, body]] of steps.entries()) {
  const y = 215 + i * 126;
  text(s, String(i + 1), 64, y - 5, 70, 58, 42, { color: accent, bold: true });
  text(s, heading, 154, y, 1062, 44, 30, { bold: true });
  text(s, body, 154, y + 46, 1062, 38, 25);
}
text(s, 'Save the comparison and your preferred tools.', 64, 629, 1152, 36, 25, { color: muted });

s = page('Exercise 2 · Query fan-out',
  'Google describes query fan-out as concurrent related searches: https://developers.google.com/search/docs/fundamentals/ai-optimization-guide. '
  + 'This exercise uses a focused form: different wording and technical terminology for one specific question, rather than broadening into subquestions. '
  + 'Live test on 29 September 2026: PubMed ESearch, sort=relevance, retmax=10, no date filter. '
  + 'Original query caffeine falling asleep returned PMIDs 10323361,42544296,10607207,35970642,38962617,30504084,15889326,10472301,19120728,39697913. '
  + 'Variant caffeine sleep onset latency included PMID 36870101 at rank 1. Variant caffeine sleep initiation included PMID 39377163 at rank 3. '
  + 'Both are absent from the original top 10. Abstracts confirm both address caffeine and sleep initiation. This is a bounded retrieval example, not a claim of exhaustive recall. '
  + 'Paper sources: https://doi.org/10.1016/j.smrv.2023.101764 and https://doi.org/10.1093/sleep/zsae230. '
  + 'Save the tested query strategy through paper-search artifacts.');
text(s, 'Find relevant papers that one wording misses.', 64, 116, 1152, 44, 29, { bold: true });
text(s, 'Use @paper-search to search the same question with different terms.', 64, 161, 1152, 38, 25);
text(s, 'Example: does caffeine delay falling asleep?', 64, 227, 1152, 44, 30, { bold: true });
text(s, 'Original query', 64, 329, 380, 30, 21, { color: muted });
text(s, 'caffeine falling asleep', 64, 367, 370, 44, 29, { bold: true, color: accent });
text(s, 'Query variants', 648, 288, 568, 30, 21, { color: muted });
// One original query branches into the two tested variants for the same question.
line(s, 434, 389, 92, 0, accent);
line(s, 526, 347, 0, 84, accent);
for (const [q, y] of [['caffeine sleep onset latency', 325], ['caffeine sleep initiation', 409]]) {
  diagramArrow(s, 526, 620, y + 22);
  text(s, q, 648, y, 568, 44, 29, { color: accent });
}
text(s, 'Sleep onset latency = time to fall asleep.', 648, 461, 568, 31, 21, { color: muted });
line(s, 64, 520, 1152, 0, '#DCE5E3', 1);
text(s, 'PubMed variants found two papers missing from the original top 10', 64, 542, 1152, 35, 25, { bold: true });
text(s, 'Caffeine and subsequent sleep · meta-analysis', 64, 589, 1152, 33, 24,
  { color: accent, link: 'https://doi.org/10.1016/j.smrv.2023.101764' });
text(s, 'Dose and timing effects of caffeine · clinical trial', 64, 633, 1152, 33, 24,
  { color: accent, link: 'https://doi.org/10.1093/sleep/zsae230' });

s = page('Exercise 3 · Update the agent’s understanding',
  'The agent\'s training knowledge may lag recent evidence. Begin with a discussion of its existing understanding, then read recent papers found in exercise 2. '
  + 'Human domain expertise guides comparison of evidence, limitations and competing explanations. paper-reading saves draft notes and reviewed context for reuse. '
  + 'This is persistent research context, not model retraining. Newer publication date alone does not establish correctness. '
  + 'Brain example: Sorrells et al. (2018), Human hippocampal neurogenesis drops sharply in children to undetectable levels in adults, '
  + 'https://www.nature.com/articles/nature25975. This was one study in a disputed field, not a universal consensus. '
  + 'Disouky et al. (25 February 2026), Human hippocampal neurogenesis in adulthood, ageing and Alzheimer\'s disease, '
  + 'https://www.nature.com/articles/s41586-026-10169-4. Analysis of 355,997 nuclei in post-mortem tissue identified stem cells, neuroblasts, immature granule neurons and a developmental trajectory. '
  + 'It supports adult neurogenesis but does not directly birth-date neurons or prove their function in living adults. Compare methods rather than declaring the debate settled.', 41);
text(s, 'Correct outdated context with your domain expertise.', 64, 115, 1152, 43, 28, { bold: true });
text(s, 'Discuss your topic, then use @paper-reading on recent papers from exercise 2.',
  64, 164, 1152, 76, 25);
text(s, 'Example: can adult brains produce new neurons?', 64, 273, 1152, 45, 31, { bold: true });
text(s, '2018', 64, 340, 480, 39, 29, { color: accent, bold: true, link: 'https://www.nature.com/articles/nature25975' });
text(s, 'One study found no detectable\nformation of new neurons in\nthe adult hippocampus.', 64, 389, 510, 123, 28);
text(s, '2026', 686, 340, 510, 39, 29, { color: accent, bold: true, link: 'https://www.nature.com/articles/s41586-026-10169-4' });
text(s, 'A study found cells and molecular\nsignals supporting new-neuron\nformation in adults.', 686, 389, 530, 123, 28);
line(s, 631, 344, 0, 151);
const phases = [['Discuss', 64, 124], ['Read papers', 267, 164], ['Review evidence', 504, 214], ['Save context', 795, 176], ['Reuse', 1080, 136]];
for (const [label, x, w] of phases) text(s, label, x, 597, w, 37, 24, { color: accent, bold: true });
for (const x of [205, 444, 731, 1005]) arrow(s, x, 591, 29);
text(s, 'Revise the saved context as your research progresses.', 64, 647, 1100, 30, 22, { color: muted });

s = page('Exercise 4 · Routine automated searches: e.g. weekly',
  'Use skills/paper-watch to prepare a prefilled proposal from saved source choices, query strategy and human-reviewed context. '
  + 'Confirm once: schedule/timezone, maximum papers, tab mode and Zotero collection. Native Codex heartbeat automation runs in the same chat. '
  + 'Workflow: search with selected sources, history exclusion and optional Zotero exclusion, save through zotero-save, read evidence through paper-reading, '
  + 'report actually added papers, findings, relevance and reading recommendation. Propose changes to reviewed context; never apply scientific context updates automatically. '
  + 'Local runs require the computer awake and Codex running; Zotero desktop must be open for Connector saves. '
  + 'Native automation documentation: https://learn.chatgpt.com/docs/automations.', 40);
text(s, 'Automate literature searches every week or month.', 64, 116, 1152, 44, 28, { bold: true });
text(s, '@paper-watch reuses your saved work', 64, 192, 1152, 43, 30, { bold: true });
for (const [label, value, x] of [['Exercise 1', 'Preferred tools', 64], ['Exercise 2', 'Tested queries', 466], ['Exercise 3', 'Reviewed context', 864]]) {
  text(s, label, x, 261, 342, 32, 23, { color: muted });
  text(s, value, x, 300, 350, 40, 28, { color: accent, bold: true });
}
text(s, 'Confirm how often to run, the paper limit and Zotero collection.', 64, 378, 1152, 40, 28, { bold: true });
text(s, 'Example: every Monday at 09:00, or the first day of each month.', 64, 423, 1152, 30, 22, { color: muted });
const cycle = [['Routine search', 64, 208], ['Save to Zotero', 374, 212], ['Read findings', 700, 211], ['Your review', 1020, 196]];
for (const [label, x, w] of cycle) text(s, label, x, 474, w, 39, 27, { color: accent, bold: true });
for (const x of [292, 614, 938]) arrow(s, x, 467, 33);
text(s, 'Updates: new papers, findings and reading suggestions.\nContext changes need your review.', 64, 553, 1152, 76, 26);
text(s, 'Keep the computer awake, with Codex and Zotero open.', 64, 648, 1100, 31, 22, { color: muted });

const legalSources = {
  UZH: 'https://www.ub.uzh.ch/en/literatur-suchen-nutzen/e-library-nutzen.html',
  uzhAI: 'https://www.ub.uzh.ch/en/literatur-suchen-nutzen/e-library-nutzen/ki-und-lizenzierte-volltexte.html',
  ETH: 'https://unlimited.ethz.ch/spaces/WWE/pages/194118851/Text%2Band%2Bdata%2Bmining%2Bresources%2Bfor%2Bdata-driven%2Band%2Bcomputational%2Bresearch',
  Basel: 'https://ub.unibas.ch/de/zugangsberechtigung/',
  Elsevier: 'https://www.elsevier.com/about/policies-and-standards/text-and-data-mining/faq',
  Wiley: 'https://onlinelibrary.wiley.com/library-info/resources/text-and-datamining',
  'Springer Nature': 'https://www.springernature.com/de/researchers/text-and-data-mining',
  PLOS: 'https://api.plos.org/text-and-data-mining.html',
  law: 'https://www.fedlex.admin.ch/eli/cc/1993/1798_1798_1798/en',
};
s = page('Legal reminder',
  'Here, we demonstrate what AI agents can do for educational purposes. '
  + 'University and publisher requirements apply during the workshop as well as in daily research. '
  + 'The table summarizes institutional and publisher guidance for licensed content and automated analysis; '
  + 'specific agreements and statutory exceptions may differ. It does not classify every individual Connector save as text and data mining. '
  + 'UZH general terms prohibit systematic downloads; licensed full-text AI use requires an explicit allowance. '
  + 'ETH asks members to consult the library before text and data mining licensed material, for non-commercial scientific research. '
  + 'Basel also treats external AI services as third parties when they control storage or further use of submitted content. '
  + 'Wiley advises checking institutional agreements before accepting its separate API terms. '
  + 'Swiss Copyright Act Art. 24d covers lawful-access reproductions technically necessary for scientific research. '
  + 'Sources checked 29 September 2026: ' + Object.entries(legalSources).map(([k, v]) => `${k}: ${v}`).join('; '));
text(s, 'Follow university and journal regulations', 64, 106, 1152, 43, 29, { bold: true });
text(s, 'Here, we demonstrate what AI agents can do for educational purposes.\nYou should also abide by your university’s and publishers’ guidelines and rules.',
  64, 160, 1152, 58, 22);
const legalRows = [
  ['UZH', 'No systematic downloads without a permitted route.\nAI use of licensed full texts needs explicit permission.'],
  ['ETH', 'Subscription analysis: ETH members, non-commercial research.\nContact the library before starting.'],
  ['Basel', 'No systematic downloads of whole issues, e-books or large database portions.\nUploads to external AI services can count as third-party sharing.'],
  ['Elsevier', 'Automated full-text analysis: register for the dedicated download API.\nFollow its rate limits and terms.'],
  ['Wiley', 'Use the approved download API, not webpage scraping.\nCheck your institutional agreement before accepting API terms.'],
  ['Springer Nature', 'Non-commercial analysis permitted.\nDirect downloads: at most one request per second.'],
  ['PLOS', 'Analysis and reuse allowed.\nUse bulk-download tools for large collections.'],
];
const legalTable = s.tables.add({ rows: legalRows.length, columns: 2,
  left: 64, top: 234, width: 1152, height: 392, columnWidths: [210, 942], values: legalRows });
legalTable.styleOptions = { headerRow: false, bandedRows: false, firstColumn: false };
legalTable.borders.assign({ style: 'solid', fill: '#DCE5E3', width: 0.7 });
for (let r = 0; r < legalRows.length; r++) {
  legalTable.rows[r].height = 56;
  for (let c = 0; c < 2; c++) {
    const cell = legalTable.getCell(r, c);
    cell.fill = c === 0 ? '#EEF5F4' : '#FFFFFF';
    cell.text.style = { typeface: family, fontSize: 20, color: c === 0 ? accent : ink,
      bold: c === 0, alignment: 'left', verticalAlignment: 'middle', autoFit: 'none' };
  }
  legalTable.getCell(r, 0).text.get(legalRows[r][0]).link = { uri: legalSources[legalRows[r][0]], isExternal: true };
}
legalTable.getCell(0, 1).text.get('AI use of licensed full texts needs explicit permission.').link = { uri: legalSources.uzhAI, isExternal: true };
text(s, 'Swiss Copyright Act, Art. 24d permits technically necessary scientific research copies with lawful access.',
  64, 645, 1110, 30, 19, { color: muted, link: legalSources.law });

const build = await fs.mkdtemp(path.join(os.tmpdir(), 'psc-exercises-'));
try {
  const candidatePath = path.join(build, 'candidate.pptx');
  const finalPath = path.join(build, 'validated', 'exercises.pptx');
  await fs.mkdir(path.dirname(finalPath), { recursive: true });
  await (await PresentationFile.exportPptx(deck)).save(candidatePath);
  await finalizePresentation({ workspaceDir: build, candidatePath, finalPath, explicitTotalSlideCount: 8,
    requiredNativeTableOwnerSlides: [8],
    pythonExecutable: process.env.RUNTIME_PYTHON,
    integrityValidatorPath: path.join(skillDir, 'container_tools/inspect_presentation_package_integrity.py'),
    layoutValidatorPath: path.join(skillDir, 'container_tools/inspect_presentation_layout_geometry.py'),
    layoutArgs: ['--expected-slide-size-emu', '12192000,6858000', '--validate-heading-fit', '--require-native-table-slide', '8'],
    fontPolicy: { basis: 'design', families: [family] }, verifyArtifactToolImport: true,
    receiptPath: path.join(build, 'validation.json') });
  const result = spawnSync(process.env.RUNTIME_SOFFICE || 'soffice', [
    `-env:UserInstallation=${pathToFileURL(path.join(build, 'lo-profile')).href}`,
    '--headless', '--convert-to', 'pdf', '--outdir', build, finalPath,
  ], { encoding: 'utf8', timeout: 60000 });
  if (result.error || result.status !== 0) throw new Error(result.error?.message || result.stderr || result.stdout);
  const pdf = await fs.readFile(path.join(build, 'exercises.pdf'));
  if (!pdf.subarray(0, 5).equals(Buffer.from('%PDF-'))) throw new Error('Invalid PDF output.');
  const output = path.join(repo, 'workshop/exercises.pdf');
  await fs.writeFile(output, pdf);
  console.log(output);
} finally { await fs.rm(build, { recursive: true, force: true }); }
