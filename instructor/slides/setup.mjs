// Build with the Node runtime and presentation dependencies supplied by Codex.
// Required environment: PRESENTATIONS_SKILL_DIR, RUNTIME_NODE_MODULES,
// RUNTIME_PYTHON. Optional: SETUP_PPTX_PATH (must be a new output path).
import fs from 'node:fs/promises';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';

const repo = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const skillDir = process.env.PRESENTATIONS_SKILL_DIR;
const runtimeModules = process.env.RUNTIME_NODE_MODULES;
if (!skillDir || !runtimeModules || !process.env.RUNTIME_PYTHON) {
  throw new Error('Load Codex workspace dependencies and set the required environment variables.');
}
const require = createRequire(path.join(runtimeModules, '__setup_builder__.cjs'));
const { Presentation, PresentationFile } = await import(
  pathToFileURL(require.resolve('@oai/artifact-tool')).href
);
const { finalizePresentation, resolvePresentationFont } = await import(
  pathToFileURL(path.join(skillDir, 'container_tools/artifact_tool_utils.mjs')).href
);
const family = resolvePresentationFont({ fontFamily: 'Arial' });
const buildDir = path.join(repo, 'tmp/slides/setup');
const finalPath = process.env.SETUP_PPTX_PATH || path.join(repo, 'output/slides/setup-guide.pptx');
await fs.mkdir(buildDir, { recursive: true });
await fs.mkdir(path.dirname(finalPath), { recursive: true });

const deck = Presentation.create({ slideSize: { width: 1280, height: 720 } });
const ink = '#172C31';
const accent = '#147477';
const muted = '#536166';

function text(slide, value, x, y, w, h, size = 26, options = {}) {
  const shape = slide.shapes.add({
    geometry: 'textbox',
    position: { left: x, top: y, width: w, height: h },
    fill: 'none', line: { fill: 'none', width: 0 },
  });
  shape.text = value;
  shape.text.style = {
    typeface: options.font || family, fontSize: size, color: options.color || ink,
    bold: options.bold || false, autoFit: 'none', wrap: 'none',
    verticalAlignment: 'top', alignment: options.align || 'left',
    insets: { left: 0, right: 0, top: 0, bottom: 0 },
  };
  if (options.link) shape.text.get(value).link = { uri: options.link, isExternal: true };
  return shape;
}

function page(title, notes, titleOptions = {}) {
  const slide = deck.slides.add();
  slide.background.fill = '#FFFFFF';
  text(slide, title, titleOptions.left || 64, titleOptions.top || 38, titleOptions.width || 1152,
    titleOptions.height || 60, titleOptions.size || 44, { bold: true, color: accent });
  text(slide, String(deck.slides.items.length), 1168, 677, 48, 24, 17,
    { color: muted, align: 'right' });
  slide.speakerNotes.textFrame.setText(notes);
  return slide;
}

async function screenshot(slide, name, sourceWidth, sourceHeight, box) {
  const ratio = Math.min(box.width / sourceWidth, box.height / sourceHeight);
  const width = sourceWidth * ratio;
  const height = sourceHeight * ratio;
  const sourcePath = path.join(repo, 'workshop/assets', name);
  const source = name.endsWith('.svg')
    ? { svg: await fs.readFile(sourcePath, 'utf8') }
    : { blob: new Uint8Array(await fs.readFile(sourcePath)), contentType: 'image/png' };
  slide.images.add({
    ...source, alt: name, fit: 'contain',
    position: {
      left: box.left + (box.width - width) / 2,
      top: box.top + (box.height - height) / 2,
      width, height,
    },
  });
}

let slide = page('Setup', 'Source: workshop/00-start-here.md. App download links appear on the slide. Current desktop app setup: https://learn.chatgpt.com/docs/quickstart.');
text(slide, 'Install and open these apps.', 64, 118, 1100, 42, 28);
const apps = [
  ['Codex', 'chatgpt.com/download', 'https://chatgpt.com/download/', 'Open the desktop app, sign in, and select Codex.'],
  ['Google Chrome', 'google.com/chrome', 'https://www.google.com/chrome/', 'Install Chrome and open it once.'],
  ['Zotero', 'zotero.org/download', 'https://www.zotero.org/download/', 'Open Zotero 10+ to save reading notes.'],
];
for (const [index, [name, label, url, action]] of apps.entries()) {
  const y = 204 + index * 135;
  text(slide, name, 64, y, 340, 44, 32, { bold: true });
  text(slide, label, 440, y, 760, 44, 30, { color: accent, link: url });
  text(slide, action, 440, y + 48, 760, 36, 25, { color: muted });
}

slide = page('Be careful when giving AI\naccess to your computer',
  'Sources: https://learn.chatgpt.com/docs/computer-use and https://learn.chatgpt.com/docs/browser#developer-mode. '
  + 'Incident: Sebastien Guillemot, 26 August 2026, https://x.com/SebastienGllmt/status/2092634841863123047. '
  + 'Original X post read in the Codex built-in browser on 28 September 2026. This is the author\'s report of home-directory deletion during a Claude/Fable coding task. '
  + 'The thread also describes recovering files from Git and other copies. Do not characterize it as a verified whole-disk wipe or a failure of browser CDP. '
  + 'Full CDP and command Full Access are separate permissions. '
  + 'Screenshot includes the complete original post, attachment, timestamp and reactions; browser navigation and replies are outside the slide crop. '
  + 'Smiling emoji: Twemoji by Twitter and contributors, CC BY 4.0, https://github.com/twitter/twemoji.',
  { left: 64, top: 64, width: 600, height: 110, size: 40 });
// A native warning glyph keeps the symbol editable and avoids a fabricated image.
text(slide, 'Consider what information and files\nthe AI can access.',
  64, 232, 590, 80, 28);
text(slide, '⚠', 64, 340, 38, 48, 34, { font: 'Arial Unicode MS', color: '#B97700' });
text(slide, 'Private information may be exposed,\nand files may be deleted by mistake.',
  114, 338, 550, 86, 26, { bold: true });
text(slide, 'But don’t worry too much for this workshop.\nWe’ll only explore low-risk tasks here.',
  64, 508, 600, 86, 26);
slide.images.add({
  svg: await fs.readFile(path.join(repo, 'workshop/assets/slightly-smiling-face-twemoji.svg'), 'utf8'),
  alt: '🙂', position: { left: 504, top: 546, width: 26, height: 26 },
});
slide.images.add({
  blob: new Uint8Array(await fs.readFile(path.join(repo, 'workshop/assets/claude-file-loss-x-full-2026-08-26.png'))),
  contentType: 'image/png', alt: 'Full original X post by Sebastien Guillemot',
  fit: 'cover', crop: { left: 0, top: 54 / 888, right: 0, bottom: (888 - 634) / 888 },
  position: { left: 710, top: 64, width: 506, height: 580 * 506 / 560 },
});

slide = page('Computer Use', 'Source: workshop/00-start-here.md. Screenshot: workshop/assets/codex-computer-use-marked-2026-09-23.png. The instructions describe the settings shown in the teaching screenshot.');
text(slide, 'In Settings, search "computer use", open Computer use, and turn on Any App.',
  64, 108, 1152, 36, 25);
await screenshot(slide, 'codex-computer-use-marked-2026-09-23.png', 2844, 1368,
  { left: 64, top: 166, width: 1152, height: 495 });

slide = page('Full CDP access', 'Source: workshop/00-start-here.md. Screenshot: workshop/assets/codex-chrome-cdp-marked-2026-09-23.png.');
text(slide, 'In Settings, search "chrome" and turn on Enable full CDP access.',
  64, 108, 1152, 36, 25);
await screenshot(slide, 'codex-chrome-cdp-marked-2026-09-23.png', 2794, 1520,
  { left: 64, top: 156, width: 1152, height: 505 });

slide = page('Zotero Connector', 'Source: workshop/00-start-here.md. Screenshot: workshop/assets/codex-zotero-connector-installed-marked-2026-09-23.png. Extension: https://chromewebstore.google.com/detail/zotero-connector/ekhagklcjbdpajgpjgmbionohlpdbjgc');
text(slide, 'In Codex’s browser, open Chrome Web Store and install Zotero Connector.',
  64, 108, 1152, 36, 25);
await screenshot(slide, 'codex-zotero-connector-installed-marked-2026-09-23.png', 2752, 1144,
  { left: 64, top: 166, width: 1152, height: 495 });

slide = page('Zotero access',
  'Screenshot supplied by the instructor: Screenshot 2026-09-28 at 18.00.10.png. '
  + 'Source: https://www.zotero.org/support/dev/web_api/v3/local_api. '
  + 'The original screenshot is preserved; the SVG adds red outlines and crops unrelated settings.');
text(slide, 'In Zotero Settings → Advanced, enable the highlighted option.',
  64, 108, 1152, 36, 25);
await screenshot(slide, 'zotero-local-access-marked-2026-09-28.svg', 901, 322,
  { left: 64, top: 166, width: 1152, height: 430 });
text(slide, 'Keep Zotero open. Allow “Paper Reading” to save notes when Zotero asks.',
  64, 622, 1152, 36, 25, { color: muted });

slide = page('Skill installation', 'Source: workshop/00-start-here.md. Repository: https://github.com/Alias-z/agentic-researcher-psc. '
  + 'The bundled skill-installer accepts multiple repository paths and makes skills available on the next turn. '
  + 'If the first two skills are already installed, ask to install only skills/paper-reading. '
  + 'Skills can be requested by name: https://learn.chatgpt.com/docs/skills-and-plugins.');
text(slide, 'In Codex, paste this request:', 64, 117, 1152, 45, 28);
slide.shapes.add({ geometry: 'rect',
  position: { left: 64, top: 190, width: 1152, height: 340 },
  fill: '#F1F2F3', line: { fill: 'none', width: 0 },
});
const codeFont = { font: 'Courier New' };
text(slide, 'Use skill-installer to install skills/paper-search,', 92, 220, 1096, 38, 26, codeFont);
text(slide, 'skills/zotero-save, and skills/paper-reading from:', 92, 260, 1096, 38, 26, codeFont);
text(slide, 'https://github.com/Alias-z/agentic-researcher-psc', 92, 324, 1096, 38, 26,
  { ...codeFont, link: 'https://github.com/Alias-z/agentic-researcher-psc' });
text(slide, 'If python3 is unavailable, use the Python executable from', 92, 401, 1096, 38, 26, codeFont);
text(slide, 'load_workspace_dependencies for the installer.', 92, 443, 1096, 38, 26, codeFont);
text(slide, 'Then ask to use a skill by name, for example: “Use paper-reading to read…”',
  64, 560, 1152, 38, 25, { color: muted });

slide = page('Zotero plugin (optional)',
  'Screenshot supplied by the instructor: Screenshot 2026-09-28 at 19.08.39.png. '
  + 'Plugin installation: https://learn.chatgpt.com/docs/plugins. '
  + 'Reading and citation capabilities were checked against the installed Zotero 0.1.2 skill and helper. '
  + 'The plugin provides general library searches and citation exports. paper-reading includes its own local API helper. '
  + 'The original screenshot is preserved; the SVG adds red outlines and crops the recent chat list.');
text(slide, 'For citation exports, open Plugins, search "zotero", and install Zotero.',
  64, 108, 1152, 36, 25);
await screenshot(slide, 'codex-zotero-plugin-marked-2026-09-28.svg', 1115, 340,
  { left: 64, top: 164, width: 1152, height: 385 });
text(slide, 'Use the plugin for general library searches and BibTeX/citation exports.',
  64, 581, 1152, 36, 25);
text(slide, 'paper-reading can read papers and save notes without this plugin.',
  64, 625, 1152, 36, 25);

slide = page('Reading always leaves notes',
  'Sources: skills/paper-reading/SKILL.md and workshop/00-start-here.md. '
  + 'One Markdown source file per paper; a generated HTML child note sits beside the PDF under that paper in Zotero. '
  + 'The HTML copy links to the Markdown source. The file remains in the chosen writing/notes folder, or task deliverables. '
  + 'Zotero searches generated note text by keyword. The Markdown file itself is not uploaded by its link. '
  + 'Refresh the Zotero copy after manual edits; there is no background synchronization. '
  + 'Local API writes require Zotero 10+ and application authorization: https://www.zotero.org/support/dev/web_api/v3/local_api.');
const noteRows = [
  ['Markdown file', 'One editable .md file per paper in your notes folder.\nKeep findings, evidence references, and LaTeX source together.'],
  ['Zotero copy', 'A searchable note beside the PDF under the same paper.\nIts Markdown source link opens your editable file.'],
  ['Human review', 'Saved immediately as human_reviewed: false / reading:draft.\nYour explicit content approval changes it to reviewed.'],
];
for (const [index, [label, detail]] of noteRows.entries()) {
  const y = 176 + index * 145;
  text(slide, label, 64, y, 300, 45, 30, { bold: true });
  text(slide, detail, 385, y, 830, 94, 26);
}
text(slide, 'An agent revision returns the note to draft. Zotero’s Allow button grants write access.',
  64, 628, 1152, 36, 24, { color: muted });

slide = page('Try reading, review, and discussion',
  'Source: workshop/01-literature-to-zotero.md, sections 3–5. These are example prompts; replace bracketed text. '
  + 'Read a paper first and inspect its saved note. Only approve content after checking it against the original paper. '
  + 'Unreviewed notes remain usable with their status stated; ask for reviewed-only evidence when desired. '
  + 'Discussion uses keyword retrieval plus original evidence, and newly read findings are saved back to notes.');
const prompts = [
  ['Read', '“Use paper-reading to read [paper] in my test collection.\nSave its Markdown note and Zotero copy, then show me.”'],
  ['Review', 'After checking the note against the paper:\n“I approve the current note for [paper]. Mark it human-reviewed.”'],
  ['Discuss', '“Search my test collection’s notes for [topic]. Discuss [question],\ncite the evidence, and state each note’s human-review status.”'],
];
for (const [index, [label, detail]] of prompts.entries()) {
  const y = 176 + index * 145;
  text(slide, label, 64, y, 250, 45, 30, { bold: true });
  text(slide, detail, 300, y, 916, 94, 26);
}
text(slide, 'Full copyable prompts are in the workshop exercise guide.',
  64, 628, 1152, 36, 25, { color: accent,
    link: 'https://github.com/Alias-z/agentic-researcher-psc/blob/main/workshop/01-literature-to-zotero.md' });

const candidatePath = path.join(buildDir, 'candidate.pptx');
await (await PresentationFile.exportPptx(deck)).save(candidatePath);
await finalizePresentation({
  workspaceDir: repo, candidatePath, finalPath,
  pythonExecutable: process.env.RUNTIME_PYTHON,
  integrityValidatorPath: path.join(skillDir, 'container_tools/inspect_presentation_package_integrity.py'),
  layoutValidatorPath: path.join(skillDir, 'container_tools/inspect_presentation_layout_geometry.py'),
  layoutArgs: ['--expected-slide-size-emu', '12192000,6858000', '--validate-heading-fit'],
  fontPolicy: { basis: 'design', families: [family, 'Courier New', 'Arial Unicode MS'] },
  verifyArtifactToolImport: true,
  receiptPath: path.join(buildDir, `${path.basename(finalPath)}.validation.json`),
});
console.log(finalPath);
