(function () {
    'use strict';
    try {
        var ua = (navigator && navigator.userAgent) ? navigator.userAgent : '';
        var uaL = ua.toLowerCase();
        var isLine = /\bline\//i.test(ua) || /\bnaver\b/i.test(ua) || (uaL.indexOf(' line') !== -1);
        var isFbOrIg = /\bfban\//i.test(ua) || /\bfbav\//i.test(ua) || /\binstagram\b/i.test(ua);
        var isTwitter = /\btwitter\b/i.test(ua);
        var isMessenger = /\bwv\b/i.test(ua) && /\bmobile\b/i.test(ua) && /\biphone|android\b/i.test(ua) && !isLine && !isFbOrIg && !isTwitter;
        var isRestrictedWebview = isLine || isFbOrIg || isTwitter || isMessenger;
        if (!isRestrictedWebview) return;
        var isIOS = /\biphone|ipad|ipod\b/i.test(ua) || (uaL.indexOf('mac') !== -1 && navigator.maxTouchPoints && navigator.maxTouchPoints > 1);
        var isAndroid = /\bandroid\b/i.test(ua);
        var rootUrl = location.href;
        var encoded = encodeURIComponent(rootUrl);
        var androidIntent = 'intent://' + (location.host || '') + (location.pathname || '') + (location.search || '') + (location.hash || '') + '#Intent;scheme=' + (location.protocol || 'https:').replace(':', '') + ';package=com.android.chrome;S.browser_fallback_url=' + encoded + ';end;';
        var iosSafari = 'x-web-search://' + encoded;
        var css = '.peb-lw-overlay{position:fixed;inset:0;z-index:2147483646;background:rgba(0,0,0,0.6);display:flex;align-items:flex-start;justify-content:center;padding:16px;font-family:Sarabun,"Noto Sans Thai",system-ui,-apple-system,Segoe UI,Roboto,Helvetica Neue,Arial,sans-serif;box-sizing:border-box;-webkit-overflow-scrolling:touch}.peb-lw-card{background:#fff;border-radius:16px;width:100%;max-width:560px;margin-top:5vh;box-shadow:0 20px 60px rgba(0,0,0,0.28);overflow:hidden;box-sizing:border-box}.peb-lw-head{background:linear-gradient(135deg,#1976D2,#004D40);color:#fff;padding:22px 22px 20px 22px;display:flex;gap:14px;align-items:flex-start}.peb-lw-icon{width:46px;height:46px;min-width:46px;border-radius:12px;background:rgba(255,255,255,0.18);display:flex;align-items:center;justify-content:center;font-size:24px}.peb-lw-title{margin:0 0 4px 0;font-size:20px;font-weight:700;line-height:1.35}.peb-lw-sub{margin:0;font-size:14px;opacity:0.92;line-height:1.55}.peb-lw-body{padding:20px 22px 18px 22px;color:#2c3e50}.peb-lw-body p{margin:0 0 12px 0;font-size:14.5px;line-height:1.7;color:#37474f}.peb-lw-ul{margin:0 0 4px 0;padding-left:22px}.peb-lw-ul li{margin:0 0 6px 0;font-size:14px;line-height:1.65;color:#455a64}.peb-lw-actions{display:flex;flex-wrap:wrap;gap:10px;padding:0 22px 22px 22px}.peb-lw-btn{flex:1 1 220px;border:0;cursor:pointer;border-radius:12px;padding:14px 16px;font-size:15.5px;font-weight:700;color:#fff;transition:transform .08s ease, filter .15s ease, box-shadow .15s ease;background:#1976D2;box-shadow:0 6px 14px rgba(25,118,210,0.28)}.peb-lw-btn:active{transform:translateY(1px);filter:brightness(0.96)}.peb-lw-btn.alt{background:#2E7D32;box-shadow:0 6px 14px rgba(46,125,50,0.26)}.peb-lw-btn.ghost{background:#eceff1;color:#37474f;box-shadow:none;border:1px solid #cfd8dc}.peb-lw-source{padding:12px 22px 14px 22px;background:#fff8e1;color:#5d4037;font-size:13px;line-height:1.6;border-top:1px dashed #ffe082}.peb-lw-src-label{font-weight:700;margin-right:6px}';
        var styleEl = document.createElement('style');
        styleEl.setAttribute('data-peb', 'lw-guard');
        styleEl.appendChild(document.createTextNode(css));
        var headOrRoot = document.head || document.documentElement;
        headOrRoot.appendChild(styleEl);
        var overlay = document.createElement('div');
        overlay.className = 'peb-lw-overlay';
        overlay.setAttribute('role', 'dialog');
        overlay.setAttribute('aria-modal', 'true');
        overlay.setAttribute('aria-labelledby', 'peb-lw-title');
        var appLabel = 'แอปต์ไลน์ (LINE)';
        if (isFbOrIg) appLabel = 'แอปต์เฟซบุ๊ก/อินสตาแกรม';
        else if (isTwitter) appLabel = 'แอปต์ทวิตเตอร์';
        else if (isMessenger) appLabel = 'แอปต์ Messenger หรือเว็บวิวภายในแอปต์อื่น';
        var hint = 'การพิมพ์ บันทึก PDF และการใช้งานฟอนต์พิเศษ บางอย่างอาจทำงานผิดปกติหรือไม่ทำงานเลย หากเปิดผ่านแอปต์นี้';
        var why1 = 'ระบบพิมพ์และบันทึก PDF ถูกปิดกั้นในเว็บวิวภายในแอปต์ไลน์';
        var why2 = 'แตะบรรทัดเลือกเนื้อหาใน iPad / มือถือ อาจติดขัดและไม่ติด';
        var why3 = 'ฟอนต์บาลีบางตัวอ่านไม่ออก อาจไม่โหลดและแสดงเป็นตาราง';
        var primaryLabel = 'เปิดใน Safari / Chrome';
        var altLabel = 'คัดลอกลิงก์';
        var ghostLabel = 'ฉันเข้าใจอยู่แล้ว';
        if (isLine) {
            primaryLabel = 'กดปุ่ม 3 จุดที่มุมบนขวา แล้วเลือก เปิดในเบราว์เซอร์ภายนอก';
        }
        var cardHTML =
            '<div class="peb-lw-card" role="document">' +
                '<div class="peb-lw-head">' +
                    '<div class="peb-lw-icon" aria-hidden="true">⚠️</div>' +
                    '<div>' +
                        '<h1 id="peb-lw-title" class="peb-lw-title">เปิดเว็บผ่าน ' + appLabel + ' ระบบพิมพ์อาจใช้ไม่ได้</h1>' +
                        '<p class="peb-lw-sub">' + hint + '</p>' +
                    '</div>' +
                '</div>' +
                '<div class="peb-lw-body">' +
                    '<p>คุณกำลังเปิดเว็บนี้ผ่าน <strong>เว็บวิวภายในแอปต์</strong> ซึ่งมีการจำกัดฟีเจอร์หลายอย่าง โดยเฉพาะ:</p>' +
                    '<ul class="peb-lw-ul">' +
                        '<li>' + why1 + '</li>' +
                        '<li>' + why2 + '</li>' +
                        '<li>' + why3 + '</li>' +
                    '</ul>' +
                '</div>' +
                '<div class="peb-lw-actions">' +
                    '<button type="button" class="peb-lw-btn" id="peb-lw-primary" aria-label="' + primaryLabel + '">' + primaryLabel + '</button>' +
                    '<button type="button" class="peb-lw-btn alt" id="peb-lw-alt">' + altLabel + '</button>' +
                    '<button type="button" class="peb-lw-btn ghost" id="peb-lw-dismiss">' + ghostLabel + '</button>' +
                '</div>' +
                '<div class="peb-lw-source">' +
                    '<span class="peb-lw-src-label">วิธีทำเอง:</span> ' +
                    (isLine
                        ? 'แตะ <strong>ปุ่ม 3 จุด</strong> ที่มุมบนขวาของไลน์ แล้วเลือก <strong>เปิดใน Safari</strong> (iPhone) หรือ <strong>เปิดใน Chrome</strong> (Android)'
                        : 'แตะปุ่ม <strong>แชร์ / เซิร์ฟเวอร์ภายนอก</strong> แล้วเปิดด้วย Safari หรือ Chrome') +
                '</div>' +
            '</div>';
        overlay.innerHTML = cardHTML;
        (document.body || document.documentElement).appendChild(overlay);
        function openExternal() {
            try {
                if (isAndroid) {
                    try { location.href = androidIntent; return; } catch (_) {}
                    try { location.href = 'googlechrome://navigate?url=' + encoded; return; } catch (_) {}
                    try { location.href = 'intent://' + (location.host || '') + location.pathname + '#Intent;scheme=http;package=com.android.chrome;end;'; return; } catch (_) {}
                }
                if (isIOS) {
                    try { location.href = 'safari-' + rootUrl; return; } catch (_) {}
                    try { location.href = iosSafari; return; } catch (_) {}
                    try { location.href = rootUrl; return; } catch (_) {}
                }
                try { location.href = rootUrl; } catch (_) {}
            } catch (e) {
                console.warn(e);
                copyLink(true);
            }
        }
        function copyLink(silent) {
            var ok = false;
            var done = function () {
                if (silent) return;
                try {
                    var b = document.getElementById('peb-lw-alt');
                    if (b) {
                        var t = b.textContent;
                        b.textContent = '✅ คัดลอกสำเร็จ';
                        setTimeout(function () { try { b.textContent = t; } catch (_) {} }, 1800);
                    }
                } catch (_) {}
            };
            try {
                if (navigator.clipboard && navigator.clipboard.writeText) {
                    navigator.clipboard.writeText(rootUrl).then(function () { ok = true; done(); }).catch(function () {
                        fallbackCopy();
                    });
                    return;
                }
            } catch (_) {}
            fallbackCopy();
            function fallbackCopy() {
                try {
                    var ta = document.createElement('textarea');
                    ta.value = rootUrl;
                    ta.setAttribute('readonly', '');
                    ta.style.position = 'fixed';
                    ta.style.left = '-9999px';
                    document.body.appendChild(ta);
                    ta.select();
                    ta.setSelectionRange(0, rootUrl.length);
                    ok = document.execCommand('copy');
                    document.body.removeChild(ta);
                } catch (_) { ok = false; }
                done();
            }
        }
        function dismiss() {
            try {
                overlay.style.transition = 'opacity .18s ease';
                overlay.style.opacity = '0';
                setTimeout(function () {
                    try { if (overlay && overlay.parentNode) overlay.parentNode.removeChild(overlay); } catch (_) {}
                    try { if (styleEl && styleEl.parentNode) styleEl.parentNode.removeChild(styleEl); } catch (_) {}
                }, 200);
            } catch (_) {}
        }
        function wire() {
            var p = document.getElementById('peb-lw-primary');
            var a = document.getElementById('peb-lw-alt');
            var d = document.getElementById('peb-lw-dismiss');
            if (p) p.addEventListener('click', openExternal);
            if (a) a.addEventListener('click', function () { copyLink(false); });
            if (d) d.addEventListener('click', dismiss);
            overlay.addEventListener('click', function (e) {
                if (e && e.target === overlay) dismiss();
            });
        }
        if (document.body) {
            wire();
        } else {
            document.addEventListener('DOMContentLoaded', wire, { once: true });
        }
    } catch (e) {
        try { console.warn('line_browser_guard init error', e); } catch (_) {}
    }
})();
