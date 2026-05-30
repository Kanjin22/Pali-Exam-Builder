const path = require('path');
const fs = require('fs');
const express = require('express');
const puppeteer = require('puppeteer');

const app = express();
app.disable('x-powered-by');
app.set('trust proxy', 1);

app.use(express.json({ limit: '20mb' }));
app.use(express.urlencoded({ extended: false, limit: '20mb' }));

const rootDir = path.resolve(__dirname, '..');
app.use(express.static(rootDir, { etag: true, maxAge: '1h' }));

app.get('/', (_req, res) => {
  res.status(200).type('text/plain; charset=utf-8').send('Pali-Exam-Builder PDF server');
});

app.get('/pages/exam_builder.html', (req, res, next) => {
  const localFile = path.join(rootDir, 'pages', 'exam_builder.html');
  if (fs.existsSync(localFile)) return next();
  const target = String(process.env.FRONTEND_URL || 'https://kanjin22.github.io/Pali-Exam-Builder/pages/exam_builder.html');
  if (!/^https?:\/\//i.test(target)) return res.status(404).type('text/plain; charset=utf-8').send('Not Found');
  res.redirect(302, target);
});

app.get('/healthz', (_req, res) => {
  res.status(200).json({ ok: true });
});

app.post('/api/render-pdf', async (req, res) => {
  let draft = null;
  if (req.body && req.body.draft && typeof req.body.draft === 'object') {
    draft = req.body.draft;
  } else if (req.body && typeof req.body.draftJson === 'string') {
    try {
      const parsed = JSON.parse(req.body.draftJson);
      if (parsed && typeof parsed === 'object') draft = parsed;
    } catch (_) {}
  }
  if (!draft || typeof draft !== 'object') {
    return res.status(400).json({ error: 'missing draft' });
  }

  const settings = (draft.settings && typeof draft.settings === 'object') ? draft.settings : {};
  const paperHtml = typeof draft.paperHTML === 'string' ? draft.paperHTML : '';

  let browser;
  try {
    const port = parseInt(process.env.PORT, 10) || 3000;
    const baseUrl = `http://127.0.0.1:${port}`;
    const localExamPath = path.join(rootDir, 'pages', 'exam_builder.html');
    const frontendUrl = fs.existsSync(localExamPath)
      ? `${baseUrl}/pages/exam_builder.html`
      : String(process.env.FRONTEND_URL || 'https://kanjin22.github.io/Pali-Exam-Builder/pages/exam_builder.html');
    const frontendOrigin = (() => {
      try {
        return new URL(frontendUrl).origin;
      } catch (_) {
        return '';
      }
    })();

    browser = await puppeteer.launch({
      headless: 'new',
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const page = await browser.newPage();
    await page.setViewport({ width: 1200, height: 800, deviceScaleFactor: 2 });

    await page.setRequestInterception(true);
    page.on('request', (r) => {
      try {
        const url = r.url() || '';
        if (/^(data|blob):/i.test(url)) return r.continue();
        if (url.startsWith(baseUrl)) return r.continue();
        if (frontendOrigin && url.startsWith(frontendOrigin)) return r.continue();
        if (/^https:\/\/kanjin22\.github\.io\//i.test(url)) return r.continue();
        if (/^https:\/\/fonts\.googleapis\.com\//i.test(url)) return r.continue();
        if (/^https:\/\/fonts\.gstatic\.com\//i.test(url)) return r.continue();
        if (/^https:\/\/cdnjs\.cloudflare\.com\//i.test(url)) return r.continue();
        if (/^https:\/\/www\.gstatic\.com\//i.test(url)) return r.continue();
        return r.abort();
      } catch (_) {
        return r.abort();
      }
    });

    await page.goto(frontendUrl, { waitUntil: 'domcontentloaded' });

    await page.evaluate(async (payload) => {
      const paper = document.getElementById('paperEditable');
      if (!paper) throw new Error('missing paperEditable');
      const printMirrorEditable = document.getElementById('printMirrorEditable');
      const printMirrorPaper = document.getElementById('printMirrorPaper');
      const printMirrorInner = document.getElementById('printMirrorInner');

      const settings = payload && payload.settings ? payload.settings : {};
      const margins = settings.margins || {};
      const safe = (v, fallback) => (v === undefined || v === null || v === '') ? fallback : v;
      const ensureNumber = (v, fallback) => {
        const n = typeof v === 'number' ? v : parseFloat(v);
        return Number.isFinite(n) ? n : fallback;
      };

      try {
        const v = safe(settings.paperSize, 'A4');
        const sel = document.getElementById('paperSizeSelect');
        if (sel) sel.value = v;
        if (typeof changePaperSize === 'function') changePaperSize(v);
        if (printMirrorPaper) {
          printMirrorPaper.classList.toggle('size-a4', String(v).toUpperCase() === 'A4');
          printMirrorPaper.classList.toggle('size-f4', String(v).toUpperCase() !== 'A4');
        }
      } catch (_) {}

      try {
        const top = ensureNumber(safe(margins.top, 2.54), 2.54);
        const bottom = ensureNumber(safe(margins.bottom, 2.54), 2.54);
        const left = ensureNumber(safe(margins.left, 2.54), 2.54);
        const right = ensureNumber(safe(margins.right, 2.54), 2.54);
        if (typeof updateMargin === 'function') {
          updateMargin('top', isFinite(top) ? top : 2.54);
          updateMargin('bottom', isFinite(bottom) ? bottom : 2.54);
          updateMargin('left', isFinite(left) ? left : 2.54);
          updateMargin('right', isFinite(right) ? right : 2.54);
        }
        if (printMirrorInner) {
          printMirrorInner.style.setProperty('--p-top', `${top}cm`);
          printMirrorInner.style.setProperty('--p-bottom', `${bottom}cm`);
          printMirrorInner.style.setProperty('--p-left', `${left}cm`);
          printMirrorInner.style.setProperty('--p-right', `${right}cm`);
        }
      } catch (_) {}

      try {
        const v = safe(settings.fontFamily, 'DilleniaUPC');
        const sel = document.getElementById('fontFamilySelect');
        if (sel) sel.value = v;
        if (typeof changeFontFamily === 'function') changeFontFamily(v);
      } catch (_) {}

      try {
        const v = safe(settings.fontSize, '22px');
        const sel = document.getElementById('fontSizeSelect');
        if (sel) sel.value = v;
        if (typeof changeFontSize === 'function') changeFontSize(v);
      } catch (_) {}

      try {
        const v = safe(settings.lineHeight, '1.6');
        const sel = document.getElementById('lineHeightSelect');
        if (sel) sel.value = v;
        if (typeof changeLineHeight === 'function') changeLineHeight(v);
      } catch (_) {}

      try {
        const v = safe(settings.letterSpacing, '0');
        const sel = document.getElementById('letterSpacingSelect');
        if (sel) sel.value = v;
        if (typeof changeLetterSpacing === 'function') changeLetterSpacing(v);
      } catch (_) {}

      try {
        const v = safe(settings.paperHorizontalScale, 1);
        const n = typeof v === 'number' ? v : parseFloat(v);
        const sel = document.getElementById('horizontalScaleSelect');
        if (sel) sel.value = String(isFinite(n) ? n : 1);
        if (typeof changeHorizontalScale === 'function') changeHorizontalScale(isFinite(n) ? n : 1);
      } catch (_) {}

      try {
        const justifyAll = !!settings.justifyAll;
        const p = document.querySelector('.paper');
        if (p) p.classList.toggle('justify-all', justifyAll);
      } catch (_) {}

      const html = String(payload && payload.paperHTML ? payload.paperHTML : '');
      paper.innerHTML = html;
      if (printMirrorEditable) printMirrorEditable.innerHTML = html;

      try {
        if (typeof applyHeaderLockState === 'function') applyHeaderLockState();
      } catch (_) {}

      try {
        if (typeof syncPrintMirrorStyles === 'function') syncPrintMirrorStyles();
        if (typeof updatePrintPageStyle === 'function') updatePrintPageStyle();
      } catch (_) {}

      try {
        if (document.fonts && document.fonts.ready) {
          await document.fonts.ready;
        }
      } catch (_) {}

      await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
    }, { settings, paperHTML: paperHtml });

    await page.emulateMediaType('print');

    const pdfBuffer = await page.pdf({
      printBackground: true,
      preferCSSPageSize: true,
      margin: { top: '0', right: '0', bottom: '0', left: '0' }
    });

    res.setHeader('Content-Type', 'application/pdf');
    res.setHeader('Content-Disposition', 'inline; filename="exam.pdf"');
    return res.status(200).send(pdfBuffer);
  } catch (e) {
    return res.status(500).json({ error: 'render_failed' });
  } finally {
    try {
      if (browser) await browser.close();
    } catch (_) {}
  }
});

const PORT = parseInt(process.env.PORT, 10) || 3000;
app.listen(PORT, () => {
  process.stdout.write(`PDF server running: http://127.0.0.1:${PORT}\n`);
});
