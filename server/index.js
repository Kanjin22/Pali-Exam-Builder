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
const defaultFrontendUrl = 'https://kanjin22.github.io/Pali-Exam-Builder/pages/exam_builder.html';
const isRenderEnv = () => {
  return !!(
    process.env.RENDER ||
    process.env.RENDER_SERVICE_ID ||
    process.env.RENDER_EXTERNAL_URL ||
    process.env.RENDER_GIT_COMMIT
  );
};

app.get('/', (_req, res) => {
  res.status(200).type('text/plain; charset=utf-8').send('Pali-Exam-Builder PDF server');
});

app.get('/pages/exam_builder.html', (req, res, next) => {
  const target = String(process.env.FRONTEND_URL || defaultFrontendUrl);
  if (!/^https?:\/\//i.test(target)) return res.status(404).type('text/plain; charset=utf-8').send('Not Found');

  const host = String(req.headers.host || '');
  const hostname = String(req.hostname || '');
  const looksLikeRenderHost = /\.onrender\.com(?::\d+)?$/i.test(host) || /\.onrender\.com$/i.test(hostname);
  if (isRenderEnv() || looksLikeRenderHost) return res.redirect(302, target);

  return next();
});

app.get('/healthz', (_req, res) => {
  res.status(200).json({ ok: true });
});

app.use(express.static(rootDir, { etag: true, maxAge: '1h' }));

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

  const wantsHtml = () => {
    const accept = String(req.headers.accept || '');
    return /\btext\/html\b/i.test(accept);
  };
  const sendRenderError = (statusCode, message) => {
    const msg = String(message || 'render_failed');
    if (wantsHtml()) {
      res
        .status(statusCode)
        .type('text/html; charset=utf-8')
        .send(
          `<!doctype html><meta charset="utf-8"><title>PDF Render Error</title>` +
          `<div style="font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;max-width:900px;margin:24px auto;padding:16px;">` +
          `<h2 style="margin:0 0 12px 0;">สร้าง PDF ไม่สำเร็จ</h2>` +
          `<pre style="white-space:pre-wrap;word-break:break-word;background:#f7f7f7;border:1px solid #ddd;border-radius:8px;padding:12px;margin:0;">${escapeHtml(msg)}</pre>` +
          `<div style="margin-top:12px;color:#444;font-size:14px;">เปิด Render Logs เพื่อดูรายละเอียดเพิ่มเติม</div>` +
          `</div>`
        );
      return;
    }
    res.status(statusCode).json({ error: 'render_failed', message: msg });
  };

  let browser;
  try {
    const port = parseInt(process.env.PORT, 10) || 3000;
    const baseUrl = `http://127.0.0.1:${port}`;
    const localExamPath = path.join(rootDir, 'pages', 'exam_builder.html');
    const frontendUrl = (!isRenderEnv() && fs.existsSync(localExamPath))
      ? `${baseUrl}/pages/exam_builder.html`
      : String(process.env.FRONTEND_URL || defaultFrontendUrl);
    const hasFrontendUrl = /^https?:\/\//i.test(frontendUrl) || frontendUrl.startsWith('/');
    if (!hasFrontendUrl) {
      return res.status(500).json({ error: 'render_failed', message: 'invalid FRONTEND_URL' });
    }
    const frontendOrigin = (() => {
      try {
        return new URL(frontendUrl).origin;
      } catch (_) {
        return '';
      }
    })();

    const launchOptions = {
      headless: 'new',
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--no-zygote',
        '--single-process'
      ]
    };
    if (process.env.PUPPETEER_EXECUTABLE_PATH) {
      launchOptions.executablePath = String(process.env.PUPPETEER_EXECUTABLE_PATH);
    }
    browser = await puppeteer.launch(launchOptions);

    const page = await browser.newPage();
    await page.setViewport({ width: 1200, height: 800, deviceScaleFactor: 2 });

    page.on('pageerror', (err) => {
      try {
        process.stderr.write(`[pageerror] ${String(err && err.message ? err.message : err)}\n`);
      } catch (_) {}
    });
    page.on('console', (msg) => {
      try {
        const text = msg.text();
        if (text) process.stderr.write(`[console:${msg.type()}] ${text}\n`);
      } catch (_) {}
    });

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
        if (/^https:\/\/firebasestorage\.googleapis\.com\//i.test(url)) return r.continue();
        if (/^https:\/\/identitytoolkit\.googleapis\.com\//i.test(url)) return r.continue();
        if (/^https:\/\/securetoken\.googleapis\.com\//i.test(url)) return r.continue();
        if (/^https:\/\/www\.google-analytics\.com\//i.test(url)) return r.continue();
        return r.abort();
      } catch (_) {
        return r.abort();
      }
    });

    await page.goto(frontendUrl, { waitUntil: 'domcontentloaded', timeout: 120000 });

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

    const pdfScale = await page.evaluate((payload) => {
      const settings = (payload && payload.settings) ? payload.settings : {};
      const margins = settings.margins || {};
      const ensureNumber = (v, fallback) => {
        const n = typeof v === 'number' ? v : parseFloat(String(v));
        return Number.isFinite(n) ? n : fallback;
      };
      const topCm = ensureNumber(margins.top, 2.54);
      const bottomCm = ensureNumber(margins.bottom, 2.54);
      const leftCm = ensureNumber(margins.left, 2.54);
      const rightCm = ensureNumber(margins.right, 2.54);

      const paperSize = String(settings.paperSize || 'A4').toUpperCase();
      const pageMm = paperSize === 'A4'
        ? { w: 210, h: 297 }
        : { w: 215.9, h: 355.6 };

      const mmToPx = (mm) => (mm * 96) / 25.4;
      const cmToPx = (cm) => (cm * 96) / 2.54;

      const paper = document.createElement('div');
      paper.style.position = 'fixed';
      paper.style.left = '-10000px';
      paper.style.top = '0';
      paper.style.width = `${pageMm.w}mm`;
      paper.style.paddingTop = `${topCm}cm`;
      paper.style.paddingBottom = `${bottomCm}cm`;
      paper.style.paddingLeft = `${leftCm}cm`;
      paper.style.paddingRight = `${rightCm}cm`;
      paper.style.boxSizing = 'border-box';
      paper.style.visibility = 'hidden';
      paper.style.background = '#fff';

      const mirrorPaper = document.getElementById('printMirrorPaper');
      const mirrorEditable = document.getElementById('printMirrorEditable');
      if (mirrorPaper) {
        const cs = getComputedStyle(mirrorPaper);
        paper.style.fontFamily = cs.fontFamily;
        paper.style.fontSize = cs.fontSize;
        paper.style.setProperty('--paper-line-height', cs.getPropertyValue('--paper-line-height') || '1.6');
        paper.style.setProperty('--paper-letter-spacing', cs.getPropertyValue('--paper-letter-spacing') || '0');
      }

      const content = document.createElement('div');
      content.style.boxSizing = 'border-box';
      paper.appendChild(content);

      if (mirrorEditable) {
        const clone = mirrorEditable.cloneNode(true);
        clone.removeAttribute('id');
        content.appendChild(clone);
      }

      document.body.appendChild(paper);
      const padTopPx = cmToPx(topCm);
      const padBottomPx = cmToPx(bottomCm);
      const printableHeightPx = mmToPx(pageMm.h) - padTopPx - padBottomPx;
      const contentHeightPx = Math.max(0, paper.scrollHeight - padTopPx - padBottomPx);
      document.body.removeChild(paper);

      if (!Number.isFinite(printableHeightPx) || printableHeightPx <= 0) return 1;
      if (!Number.isFinite(contentHeightPx) || contentHeightPx <= 0) return 1;

      const ratio = contentHeightPx / printableHeightPx;
      if (ratio <= 1) return 1;

      const suggested = printableHeightPx / contentHeightPx;
      const minScale = 0.97;
      const maxAutoRatio = 1.03;
      if (ratio <= maxAutoRatio && suggested >= minScale) return suggested;
      return 1;
    }, { settings });

    const pdfBuffer = await page.pdf({
      printBackground: true,
      preferCSSPageSize: true,
      scale: (Number.isFinite(pdfScale) && pdfScale > 0 ? pdfScale : 1),
      margin: { top: '0', right: '0', bottom: '0', left: '0' }
    });

    const asBuf = Buffer.isBuffer(pdfBuffer) ? pdfBuffer : Buffer.from(pdfBuffer);
    const head = asBuf.subarray(0, 8).toString('utf8');
    if (!head.startsWith('%PDF-') || asBuf.length < 1000) {
      throw new Error(`invalid_pdf_output (len=${String(asBuf.length)}, head=${JSON.stringify(head)})`);
    }

    res.setHeader('Content-Type', 'application/pdf');
    res.setHeader('Content-Disposition', 'inline; filename="exam.pdf"');
    return res.status(200).send(asBuf);
  } catch (e) {
    try {
      process.stderr.write(`[render_failed] ${e && e.stack ? e.stack : String(e)}\n`);
    } catch (_) {}
    return sendRenderError(500, e && e.message ? String(e.message) : String(e));
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
