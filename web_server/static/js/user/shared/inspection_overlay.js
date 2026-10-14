/* InspectionOverlay - shared live-inspection UI (canvas boxes, checklist, defect table, decision, override).
   Detection JSON: { box:[x1,y1,x2,y2], score:0-1, class_name:str, status:"PASS"|"DEFECT", check_id?:str, severity?:str, ts?:ms }
   Messages (WebSocket or ingest()):
     {type:"detections", frame_w, frame_h, detections:[...]}
     {type:"checklist", id, status:"PASS"|"FAIL"|"PENDING"}
     {type:"decision", decision:"ACCEPTED"|"REJECTED"}
     {type:"reset"}                                                                      */
(function (g) {
  'use strict';
  var OK = '#16a34a', BAD = '#dc2626';
  var esc = function (s) { return String(s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); };

  function InspectionOverlay(opts) {
    this.o = Object.assign({ title: 'Live Inspection', streamUrl: null, wsUrl: null, overrideUrl: null,
      checklist: [], severityMap: {}, minScore: 0, onOverride: null }, opts || {});
    this.root = typeof this.o.mount === 'string' ? document.querySelector(this.o.mount) : this.o.mount;
    if (!this.root) throw new Error('InspectionOverlay: mount element not found');
    this.s = { items: [], defects: new Map(), dets: [], fw: 0, fh: 0, serverDecision: null, override: null, audit: [] };
    this._build();
    this.setChecklist(this.o.checklist);
    if (this.o.wsUrl) this.connect();
  }
  var P = InspectionOverlay.prototype;

  P._build = function () {
    var self = this, o = this.o;
    this.root.classList.add('io-root');
    this.root.innerHTML =
      '<div class="io-grid"><section class="io-main">' +
      '<div class="io-card"><div class="io-card-h"><span>' + esc(o.title) + '</span><span class="io-conn" data-r="conn">offline</span></div>' +
      '<div class="io-stage" data-r="stage"><img class="io-media" data-r="img" alt="live feed" hidden><canvas class="io-media" data-r="bg" width="1280" height="720" hidden></canvas><canvas class="io-ov" data-r="ov"></canvas></div>' +
      '<div class="io-legend"><span><i class="io-dot ok"></i>Pass / Present</span><span><i class="io-dot bad"></i>Defect / Missing</span></div></div>' +
      '<div class="io-card"><div class="io-card-h"><span>Defect summary</span><span data-r="dcount">0</span></div><div class="io-tablewrap"><table class="io-table"><thead><tr><th>Time</th><th>Check</th><th>Defect</th><th>Conf.</th><th>Severity</th></tr></thead><tbody data-r="dbody"></tbody></table></div></div>' +
      '</section><aside class="io-side">' +
      '<div class="io-banner pending" data-r="banner"><div class="io-banner-t" data-r="bt"></div><div class="io-banner-s" data-r="bs"></div></div>' +
      '<div class="io-card"><div class="io-card-h"><span>Inspection checklist</span><span data-r="ccount"></span></div><ul class="io-check" data-r="clist"></ul></div>' +
      '<div class="io-card"><div class="io-card-h"><span>Operator override</span></div><div class="io-ov-body">' +
      '<button class="io-btn" data-r="ovbtn" disabled></button>' +
      '<div class="io-form" data-r="ovform" hidden><textarea data-r="ovreason" placeholder="Reason (required, min 5 characters)"></textarea><div class="io-row"><button class="io-btn solid" data-r="ovok">Confirm</button><button class="io-btn" data-r="ovno">Cancel</button></div></div>' +
      '<ul class="io-audit" data-r="audit"></ul></div></div>' +
      '</aside></div>';
    this.r = {};
    [].forEach.call(this.root.querySelectorAll('[data-r]'), function (el) { self.r[el.dataset.r] = el; });
    this.media = o.streamUrl ? this.r.img : this.r.bg;
    this.media.hidden = false;
    if (o.streamUrl) this.r.img.src = o.streamUrl;
    this.r.ovbtn.onclick = function () { self.r.ovform.hidden = false; self.r.ovreason.focus(); };
    this.r.ovno.onclick = function () { self.r.ovform.hidden = true; self.r.ovreason.value = ''; };
    this.r.ovok.onclick = function () { self._override(); };
    if (g.ResizeObserver) new ResizeObserver(function () { self._draw(); }).observe(this.r.stage);
    if (o.streamUrl) this.r.img.addEventListener('load', function () { self._draw(); });
    if (o.hideDecision) { this.r.banner.hidden = true; this.r.ovbtn.closest('.io-card').hidden = true; }
    this._render();
  };

  /* ---------- public API ---------- */
  P.setChecklist = function (items) {
    this.s.items = (items || []).map(function (i) { return { id: i.id, label: i.label || i.id, status: 'PENDING', score: null }; });
    this._render();
  };
  P.setStream = function (url) { if (this.o.streamUrl && this.r.img.getAttribute('src') !== url) this.r.img.src = url; };
  P.setFrame = function (src) { // canvas/img/video used as background when no streamUrl
    var bg = this.r.bg, c = bg.getContext('2d');
    bg.width = src.width || src.videoWidth || 1280; bg.height = src.height || src.videoHeight || 720;
    c.drawImage(src, 0, 0, bg.width, bg.height); this._draw();
  };
  P.ingest = function (m) {
    if (!m) return;
    if (m.type === 'reset') return this.reset();
    if (m.type === 'decision') { this.s.serverDecision = m.decision; return this._render(); }
    if (m.type === 'checklist') { this._setItem(m.id, m.status); return this._render(); }
    if (m.type && m.type !== 'detections') return;   // other messages on a shared socket (instruction, parameter_update...)
    var dets = m.detections || [];
    if (m.frame_w) this.s.fw = m.frame_w; if (m.frame_h) this.s.fh = m.frame_h;
    var self = this;
    this.s.dets = dets.filter(function (d) { return d.score >= self.o.minScore; }).map(function (d) {
      d.status = d.status === 'DEFECT' ? 'DEFECT' : 'PASS'; return d;
    });
    this.s.dets.forEach(function (d) {
      if (d.check_id) self._setItem(d.check_id, d.status === 'DEFECT' ? 'FAIL' : 'PASS', d.box ? d.score : null);
      if (d.status === 'DEFECT') {
        var k = (d.check_id || '') + '|' + d.class_name, old = self.s.defects.get(k);
        if (!old || (d.box && d.score > old.score)) self.s.defects.set(k, { ts: d.ts || Date.now(), check: self._label(d.check_id), cls: d.class_name, score: d.box ? d.score : null,
          sev: d.severity || self.o.severityMap[d.class_name] || 'major' });
      }
    });
    this._draw(); this._render();
  };
  P.reset = function () {
    this.s.items.forEach(function (i) { i.status = 'PENDING'; i.score = null; });
    this.s.defects.clear(); this.s.dets = []; this.s.serverDecision = null; this.s.override = null;
    this._draw(); this._render();
  };
  P.decision = function () {
    if (this.s.override) return this.s.override.to;
    if (this.s.serverDecision) return this.s.serverDecision;
    var it = this.s.items;
    if (it.some(function (i) { return i.status === 'FAIL'; })) return 'REJECTED';
    if (it.length && it.every(function (i) { return i.status === 'PASS'; })) return 'ACCEPTED';
    return 'PENDING';
  };
  P.connect = function () {
    var self = this, retry = 1000;
    function open() {
      var ws = new WebSocket(self.o.wsUrl); self.ws = ws;
      ws.onopen = function () { retry = 1000; self.r.conn.textContent = 'live'; self.r.conn.classList.add('on'); };
      ws.onmessage = function (e) { try { self.ingest(JSON.parse(e.data)); } catch (err) { console.error('bad WS message', err); } };
      ws.onclose = function () { self.r.conn.textContent = 'offline'; self.r.conn.classList.remove('on'); setTimeout(open, retry = Math.min(retry * 2, 10000)); };
    }
    open();
  };

  /* ---------- internals ---------- */
  P._label = function (id) { var i = this.s.items.find(function (x) { return x.id === id; }); return i ? i.label : (id || '-'); };
  P._setItem = function (id, status, score) {
    var i = this.s.items.find(function (x) { return x.id === id; });
    if (!i) return;
    if (i.status === 'FAIL' && status !== 'FAIL') return; // a defect is sticky until reset
    i.status = status; if (score != null) i.score = score;
  };

  P._draw = function () {
    var cv = this.r.ov, st = this.r.stage, w = st.clientWidth, h = st.clientHeight, dpr = g.devicePixelRatio || 1;
    if (!w || !h) return;
    cv.width = w * dpr; cv.height = h * dpr;
    var c = cv.getContext('2d'); c.setTransform(dpr, 0, 0, dpr, 0, 0); c.clearRect(0, 0, w, h);
    var m = this.media, fw = this.s.fw || m.naturalWidth || m.width, fh = this.s.fh || m.naturalHeight || m.height;
    if (!fw || !fh) return;
    var sc = Math.min(w / fw, h / fh), ox = (w - fw * sc) / 2, oy = (h - fh * sc) / 2;
    c.font = '600 12px system-ui,sans-serif'; c.textBaseline = 'middle'; c.lineWidth = 2.5;
    this.s.dets.forEach(function (d) {
      if (!d.box) return; // missing part: no box to draw, still listed in the table
      var col = d.status === 'DEFECT' ? BAD : OK, b = d.box;
      var x = ox + b[0] * sc, y = oy + b[1] * sc, bw = (b[2] - b[0]) * sc, bh = (b[3] - b[1]) * sc;
      c.strokeStyle = col; c.strokeRect(x, y, bw, bh);
      var t = d.class_name + ' ' + Math.round(d.score * 100) + '%', tw = c.measureText(t).width + 10, ty = y >= 20 ? y - 20 : y;
      c.fillStyle = col; c.fillRect(x, ty, tw, 20);
      c.fillStyle = '#fff'; c.fillText(t, x + 5, ty + 10);
    });
  };

  P._render = function () {
    var s = this.s, r = this.r, dec = this.decision(), done = s.items.filter(function (i) { return i.status === 'PASS'; }).length;
    r.clist.innerHTML = s.items.map(function (i) {
      var cls = i.status.toLowerCase(), mark = i.status === 'PASS' ? '&#10003;' : i.status === 'FAIL' ? '&#10005;' : '';
      return '<li class="io-ci ' + cls + '"><span class="io-tick">' + mark + '</span><span class="io-ci-l">' + esc(i.label) + '</span><span class="io-ci-c">' +
        (i.score != null ? Math.round(i.score * 100) + '%' : '') + '</span></li>';
    }).join('') || '<li class="io-empty">No checklist configured</li>';
    r.ccount.textContent = s.items.length ? done + ' / ' + s.items.length + ' passed' : '';
    var rows = Array.from(s.defects.values());
    r.dcount.textContent = rows.length;
    r.dbody.innerHTML = rows.length ? rows.map(function (d) {
      return '<tr><td>' + new Date(d.ts).toLocaleTimeString() + '</td><td>' + esc(d.check) + '</td><td>' + esc(d.cls) + '</td><td>' + (d.score == null ? '&mdash;' : Math.round(d.score * 100) + '%') +
        '</td><td><span class="io-sev ' + esc(d.sev) + '">' + esc(d.sev) + '</span></td></tr>';
    }).join('') : '<tr><td colspan="5" class="io-empty">No defects detected</td></tr>';
    r.banner.className = 'io-banner ' + dec.toLowerCase();
    r.bt.textContent = dec === 'PENDING' ? 'INSPECTING...' : dec;
    r.bs.textContent = s.override ? 'Overridden by operator' : dec === 'PENDING' ? 'Waiting for all checks' : s.serverDecision ? 'Final decision from server' : 'Provisional (from checks)';
    r.ovbtn.disabled = dec === 'PENDING';
    var to = dec === 'ACCEPTED' ? 'REJECTED' : 'ACCEPTED';
    r.ovbtn.textContent = 'Override to ' + to; r.ovbtn.className = 'io-btn ' + (to === 'ACCEPTED' ? 'ok' : 'bad');
    r.audit.innerHTML = s.audit.map(function (a) {
      return '<li>' + new Date(a.ts).toLocaleTimeString() + ' - ' + esc(a.from) + ' &rarr; ' + esc(a.to) + '<br>' + esc(a.reason) + '</li>';
    }).join('');
  };

  P._override = function () {
    var reason = this.r.ovreason.value.trim();
    if (reason.length < 5) { this.r.ovreason.focus(); return; }
    var from = this.decision(), to = from === 'ACCEPTED' ? 'REJECTED' : 'ACCEPTED';
    var rec = { ts: Date.now(), from: from, to: to, reason: reason };
    this.s.override = rec; this.s.audit.push(rec);
    this.r.ovform.hidden = true; this.r.ovreason.value = '';
    if (this.o.overrideUrl) fetch(this.o.overrideUrl, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(rec) })
      .catch(function (e) { console.error('override not saved', e); });
    if (this.o.onOverride) this.o.onOverride(rec);
    this._render();
  };

  g.InspectionOverlay = InspectionOverlay;
})(window);
