const fs = require('fs');
const path = require('path');
const xml2js = require('xml2js');
const { toJsonLdFromXmlString } = require('./rechtspraak-js/lib/model/json-ld/to-json-ld');

const INPUT_DIR  = path.resolve(__dirname, '../_data/rechtspraak-xml');
const OUTPUT_DIR = path.resolve(__dirname, '../_data/rechtspraak-json');
if (!fs.existsSync(OUTPUT_DIR)) fs.mkdirSync(OUTPUT_DIR, { recursive: true });

// xml2js parser with trimming and normalized whitespace
const parser = new xml2js.Parser({
  explicitArray: false,
  trim: true,
  normalize: true
});

// Recursively extract non-empty <para> text from a node
function extractParas(node) {
  let paras = [];
  if (node.para != null) {
    const arr = Array.isArray(node.para) ? node.para : [node.para];
    for (let p of arr) {
      const txt = typeof p === 'string' ? p : p._;
      if (txt) paras.push(txt);
    }
  }
  if (node.paragroup) {
    const groups = Array.isArray(node.paragroup) ? node.paragroup : [node.paragroup];
    for (let g of groups) paras.push(...extractParas(g));
  }
  if (node.parablock) {
    const blocks = Array.isArray(node.parablock) ? node.parablock : [node.parablock];
    for (let b of blocks) paras.push(...extractParas(b));
  }
  return paras;
}

// Process one XML file, skipping on errors
async function processFile(xmlPath) {
  const xml = fs.readFileSync(xmlPath, 'utf8');
  let metadata;

  // 1) metadata → JSON-LD (skip file on error)
  try {
    metadata = toJsonLdFromXmlString(xml);
  } catch (err) {
    console.warn(`Skipping ${path.basename(xmlPath)} due to metadata error: ${err.message}`);
    return;
  }

  // 2) full-text extraction via xml2js, then filter to only OVERWEGINGEN and BESLISSING
  let fullText = [];
  try {
    const doc = await parser.parseStringPromise(xml);
    const uitspraak = doc['open-rechtspraak']?.uitspraak;
    if (uitspraak && uitspraak.section) {
      const sections = Array.isArray(uitspraak.section) ? uitspraak.section : [uitspraak.section];
      for (let sec of sections) {
        const title = sec.title ? (typeof sec.title === 'string' ? sec.title.trim().toUpperCase() : sec.title._.trim().toUpperCase()) : '';
        if (title === 'OVERWEGINGEN' || title === 'BESLISSING') {
          fullText.push({
            title,
            paragraphs: extractParas(sec)
          });
        }
      }
    }
  } catch (err) {
    console.warn(`Partial extract failed for ${path.basename(xmlPath)}: ${err.message}`);
  }

  // 3) merge and write
  const out = { metadata, fullText };
  const filename = path.basename(xmlPath, '.xml') + '.json';
  fs.writeFileSync(path.join(OUTPUT_DIR, filename), JSON.stringify(out, null, 2), 'utf8');
  console.log('Converted:', filename);
}

async function convertAll() {
  const files = fs.readdirSync(INPUT_DIR).filter(f => f.endsWith('.xml'));
  console.log(`Found ${files.length} XML files.`);
  for (let f of files) {
    await processFile(path.join(INPUT_DIR, f));
  }
  console.log('All files processed.');
}

convertAll().catch(err => console.error('Fatal error during conversion:', err));
