/* Online ITI Inspection Portal — proforma renderer, autosave and offline drafts.
 * Renders the approved proforma (schema from proforma.py) into inputs, saves
 * changes to the server, and keeps unsent changes on the device when offline.
 */
(function () {
  "use strict";

  const $ = (sel, root) => (root || document).querySelector(sel);
  const readJSON = (id) => JSON.parse(document.getElementById(id).textContent);
  const S = readJSON("schema-data");
  let D = readJSON("form-data");
  const C = readJSON("ctx-data");
  const ATT = readJSON("att-data");
  const MODE = C.mode; // "edit" or "view"
  const EDITABLE = new Set(C.editable_parts || []);
  const MANDATORY = new Set(C.mandatory_units || []);
  const CPN = S.cpn_options;
  const LS_KEY = "iti-pending-" + C.inspection_id;
  const LS_PART = "iti-part-" + C.inspection_id;
  const csrf = () => {
    const i = document.querySelector("#csrf-holder input[name=csrfmiddlewaretoken]");
    return i ? i.value : (document.cookie.match(/csrftoken=([^;]+)/) || [])[1] || "";
  };

  // ------------------------------------------------------------ DOM helper
  function el(tag, attrs, ...kids) {
    const n = document.createElement(tag);
    if (attrs) {
      for (const [k, v] of Object.entries(attrs)) {
        if (v === null || v === undefined || v === false) continue;
        if (k === "class") n.className = v;
        else if (k === "text") n.textContent = v;
        else if (k.startsWith("on") && typeof v === "function") n.addEventListener(k.slice(2), v);
        else if (k === "dataset") Object.assign(n.dataset, v);
        else n.setAttribute(k, v === true ? "" : v);
      }
    }
    for (const kid of kids.flat()) {
      if (kid === null || kid === undefined || kid === false) continue;
      n.appendChild(typeof kid === "string" ? document.createTextNode(kid) : kid);
    }
    return n;
  }

  // ------------------------------------------------------------ pending queue
  let pending = {};
  try { pending = JSON.parse(localStorage.getItem(LS_KEY) || "{}") || {}; } catch (e) { pending = {}; }
  if (MODE === "edit") {
    for (const [k, v] of Object.entries(pending)) {
      if (v === null) delete D[k]; else D[k] = v;
    }
  }
  const pendingWarn = document.getElementById("pending-warning");
  if (pendingWarn && Object.keys(pending).length) pendingWarn.hidden = false;

  function persistPending() {
    try { localStorage.setItem(LS_KEY, JSON.stringify(pending)); } catch (e) { /* storage full */ }
  }

  // ------------------------------------------------------------ schema index
  const UNITS = [];      // {key, part, kind, block, inputs:[keys], sno, label}
  const UNIT_BY_KEY = {};
  const PARTS = [];      // {key, section, code, title, govt_only, el}
  (function buildIndex() {
    for (const sec of S.sections) {
      for (const part of sec.parts) {
        const pkey = sec.id + "." + part.code;
        PARTS.push({ key: pkey, section: sec, part, govt_only: !!part.govt_only });
        const add = (key, kind, block, inputs, sno, label) => {
          const u = { key, part: pkey, kind, block, inputs, sno, label };
          UNITS.push(u); UNIT_BY_KEY[key] = u;
        };
        for (const b of part.blocks) {
          const t = b.type, sid = sec.id;
          if (t === "particulars") {
            for (const r of b.rows) {
              const uk = sid + "." + r.sno;
              add(uk, t, b.id, r.fields.map(f => f.k ? uk + "." + f.k : uk), r.sno, r.text);
            }
          } else if (t === "checklist") {
            for (const r of b.rows) {
              const uk = sid + "." + r.sno;
              add(uk, t, b.id, [uk + ".obs", uk + ".cpn"].concat((r.extras || []).map(x => uk + "." + x.k)), r.sno, r.text);
            }
          } else if (t === "area") {
            for (const r of b.rows) {
              const uk = sid + "." + r.sno;
              add(uk, t, b.id, r.repeat ? [uk] : [uk + ".measured", uk + ".cpn"], r.sno, r.text);
            }
          } else if (t === "grid") {
            const uk = sid + "." + b.id;
            add(uk, t, b.id, [uk].concat((b.header_inputs || []).map(h => uk + ".hdr." + h.k)), b.id, b.title);
          } else if (t === "staffing") {
            for (const p of b.posts) {
              const uk = sid + "." + b.id + "." + p.k;
              add(uk, t, b.id, b.columns.map(c => uk + "." + c.k), b.id, p.post);
              if (p.k === b.trade_rows_after) {
                const tk = sid + "." + b.id + ".trades";
                add(tk, "trades", b.id, [tk], b.id, "Trade instructors — trade-wise rows");
              }
            }
          } else if (t === "register") {
            for (const r of b.rows) {
              const uk = sid + "." + r.sno;
              add(uk, t, b.id, [uk + ".maint", uk + ".uptodate", uk + ".remarks"], r.sno, r.text);
            }
          } else if (t === "office") {
            for (const r of b.rows) {
              const uk = sid + "." + r.sno;
              add(uk, t, b.id, [uk + ".avail", uk + ".updated", uk + ".deficiency", uk + ".action"], r.sr + " " + r.sno, r.text);
            }
          } else if (t === "j1") {
            for (const r of b.rows) {
              const uk = sid + ".J1." + r.k;
              add(uk, t, b.id, [uk + ".found", uk + ".evidence"], "J1", r.ground);
            }
          } else if (t === "choice" || t === "text") {
            const uk = sid + "." + b.id;
            add(uk, t, b.id, [uk], b.id, b.title);
          } else if (t === "declaration") {
            const uk = sid + "." + b.id;
            add(uk, t, b.id, [uk + ".members", uk + ".ack_received", uk + ".atr_due"], b.id, b.title);
          }
        }
      }
    }
  })();

  const isFilled = (v) => {
    if (v === null || v === undefined) return false;
    if (typeof v === "string") return v.trim() !== "";
    if (Array.isArray(v)) return v.some(rowFilled);
    return true;
  };
  const rowFilled = (r) => r && typeof r === "object" &&
    Object.entries(r).some(([k, v]) => k !== "user_id" && isFilled(v));

  function unitAnswered(u) {
    if (u.kind === "declaration") {
      return (D[u.key + ".members"] || []).some(m => m && m.declared);
    }
    return u.inputs.some(k => isFilled(D[k]));
  }
  const partApplicable = (p) => C.iti_is_govt || !p.govt_only;
  function partCounts(pkey) {
    let done = 0, total = 0;
    for (const u of UNITS) if (u.part === pkey) { total++; if (unitAnswered(u)) done++; }
    return { done, total };
  }
  function overall() {
    let done = 0, total = 0;
    for (const p of PARTS) {
      if (!partApplicable(p)) continue;
      const c = partCounts(p.key); done += c.done; total += c.total;
    }
    return { done, total, pct: total ? Math.round(100 * done / total) : 0 };
  }

  // ------------------------------------------------------------ validation
  function checkScalar(t, v, options) {
    if (v === null || v === undefined || v === "") return null;
    switch (t) {
      case "number": { const n = Number(v); if (!isFinite(n)) return "Enter a number"; if (n < 0) return "Cannot be negative"; return null; }
      case "date": return /^\d{4}-\d{2}-\d{2}$/.test(v) && !isNaN(Date.parse(v)) ? null : "Enter a valid date";
      case "time": return /^\d{2}:\d{2}$/.test(v) ? null : "Enter a valid time";
      case "email": return /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(v) ? null : "Enter a valid e-mail address";
      case "tel": return /^[0-9+\-\s()]{6,20}$/.test(v) ? null : "Enter a valid phone number";
      case "lat": { const n = Number(v); return isFinite(n) && n >= -90 && n <= 90 ? null : "Latitude must be between -90 and 90"; }
      case "lng": { const n = Number(v); return isFinite(n) && n >= -180 && n <= 180 ? null : "Longitude must be between -180 and 180"; }
      case "radio": case "select": return !options || options.includes(v) ? null : "Choose one of the options";
      default: return null;
    }
  }

  // ------------------------------------------------------------ saving
  let saveTimer = null, inflight = false, retryTimer = null, lastError = "";
  const stateEl = $("#savestate");
  function setState(text, cls) {
    if (!stateEl) return;
    stateEl.textContent = text;
    stateEl.className = "savestate" + (cls ? " " + cls : "");
  }
  function updateStateIdle() {
    const n = Object.keys(pending).length;
    if (!n) setState("All changes saved", "ok");
    else if (!navigator.onLine) setState("Offline — " + n + " change(s) kept on this device", "warn");
    else setState(n + " unsaved change(s)", "warn");
  }

  function setValue(key, value, opts) {
    if (MODE !== "edit") return;
    const empty = value === "" || value === null || value === undefined || (Array.isArray(value) && !value.length);
    if (empty) delete D[key]; else D[key] = value;
    pending[key] = empty ? null : value;
    persistPending();
    refreshUnit(key);
    updateProgress();
    if (key.startsWith("SA.") && /cpn|maint|uptodate|C2\.\d+$/.test(key)) renderJ2();
    clearTimeout(saveTimer);
    saveTimer = setTimeout(flush, (opts && opts.now) ? 0 : 1500);
    updateStateIdle();
  }

  async function flush() {
    clearTimeout(saveTimer);
    if (MODE !== "edit" || inflight) return;
    const snapshot = Object.assign({}, pending);
    if (!Object.keys(snapshot).length) { updateStateIdle(); return true; }
    if (!navigator.onLine) { updateStateIdle(); scheduleRetry(); return false; }
    inflight = true;
    setState("Saving…", "busy");
    try {
      const changes = {};
      for (const [k, v] of Object.entries(snapshot)) changes[k] = v === null ? "" : v;
      const resp = await fetch(C.urls.save, {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json", "X-CSRFToken": csrf() },
        body: JSON.stringify({ changes, version: C.version }),
      });
      if (resp.status === 403 && (resp.headers.get("content-type") || "").indexOf("json") < 0) {
        throw new Error("Your session has expired. Please sign in again in another tab; your entries are kept on this device.");
      }
      if (resp.redirected || resp.status === 302) throw new Error("Please sign in again; your entries are kept on this device.");
      const body = await resp.json();
      if (resp.status === 409) {
        setState("Locked — " + (body.errors && body.errors._form || "already submitted"), "err");
        pending = {}; persistPending();
        inflight = false;
        disableAll();
        return false;
      }
      for (const k of body.saved || []) {
        if (JSON.stringify(pending[k]) === JSON.stringify(snapshot[k])) delete pending[k];
      }
      const errs = body.errors || {};
      for (const [k, msg] of Object.entries(errs)) {
        if (k === "_form") continue;
        delete pending[k];
        showFieldError(k, msg);
      }
      persistPending();
      C.version = body.version;
      if (body.values) {
        for (const [k, v] of Object.entries(body.values)) {
          if (pending[k] === undefined) { if (v === null || v === undefined) delete D[k]; else D[k] = v; rerenderKey(k); }
        }
      }
      updateProgress();
      lastError = "";
      if (Object.keys(errs).length) setState("Some entries were not accepted — see highlighted fields", "err");
      else if (Object.keys(pending).length) { inflight = false; return flush(); }
      else setState("All changes saved · " + body.saved_at, "ok");
      inflight = false;
      return !Object.keys(errs).length;
    } catch (e) {
      inflight = false;
      lastError = e.message || "Network error";
      setState("Not saved to server — kept on this device. " + (navigator.onLine ? lastError : ""), "warn");
      scheduleRetry();
      return false;
    }
  }
  function scheduleRetry() {
    clearTimeout(retryTimer);
    retryTimer = setTimeout(flush, 20000);
  }
  window.addEventListener("online", () => { updateStateIdle(); flush(); });
  window.addEventListener("offline", updateStateIdle);
  document.addEventListener("visibilitychange", () => { if (document.visibilityState === "hidden") flush(); });
  window.addEventListener("beforeunload", (e) => {
    if (MODE === "edit" && Object.keys(pending).length && navigator.onLine) {
      flush();
    }
  });

  // ------------------------------------------------------------ field errors
  function showFieldError(key, msg) {
    document.querySelectorAll('[data-err-for="' + CSS.escape(key) + '"]').forEach(n => { n.textContent = msg; n.hidden = !msg; });
    document.querySelectorAll('[data-key="' + CSS.escape(key) + '"]').forEach(n => n.classList.toggle("invalid", !!msg));
  }
  const errSlot = (key) => el("div", { class: "fielderr", dataset: { errFor: key }, hidden: true });

  // ------------------------------------------------------------ controls
  function canEditPart(pkey) { return MODE === "edit" && EDITABLE.has(pkey); }

  function autoGrow(t) { t.style.height = "auto"; t.style.height = Math.min(t.scrollHeight + 2, 600) + "px"; }

  function scalarInput(key, spec, ro, onChange) {
    // spec: {t, options, label, unit}
    const t = spec.t;
    const val = onChange ? spec.value : D[key];
    let ctrlNode = null;
    const commit = (v) => {
      const err = checkScalar(t, v, spec.options);
      if (!onChange) showFieldError(key, err);
      else if (ctrlNode) { ctrlNode.classList.toggle("invalid", !!err); ctrlNode.title = err || ""; }
      if (err) return;
      if (onChange) onChange(v); else setValue(key, v);
    };
    if (t === "radio" || (t === "select" && spec.segmented)) {
      const name = "r_" + key + "_" + Math.random().toString(36).slice(2, 7);
      const wrap = el("div", { class: "seg" + (spec.options.length > 4 || spec.options.some(o => o.length > 18) ? " seg-wrap" : ""), role: "radiogroup", dataset: onChange ? {} : { key } });
      spec.options.forEach(o => {
        const id = name + "_" + o.replace(/\W+/g, "");
        const inp = el("input", { type: "radio", name, id, value: o, disabled: ro, checked: val === o });
        inp.addEventListener("click", () => {
          // Clicking a selected option again clears it.
          if (inp.dataset.was === "1") { inp.checked = false; inp.dataset.was = "0"; commit(""); return; }
          wrap.querySelectorAll("input").forEach(x => x.dataset.was = "0");
          inp.dataset.was = "1";
          commit(o);
        });
        if (val === o) inp.dataset.was = "1";
        wrap.appendChild(el("label", { for: id, class: "segopt" }, inp, el("span", { text: o })));
      });
      return wrap;
    }
    if (t === "select") {
      const s = el("select", { disabled: ro, dataset: onChange ? {} : { key }, "aria-label": spec.label || "" },
        el("option", { value: "", text: "—" }),
        spec.options.map(o => el("option", { value: o, text: o, selected: val === o })));
      s.addEventListener("change", () => commit(s.value));
      return s;
    }
    if (t === "textarea") {
      const ta = el("textarea", { rows: spec.rows || 2, disabled: ro, dataset: onChange ? {} : { key }, "aria-label": spec.label || "", placeholder: ro ? "" : (spec.placeholder || "") });
      ta.value = val || "";
      ctrlNode = ta;
      ta.addEventListener("input", () => { autoGrow(ta); if (!onChange) { clearTimeout(ta._t); ta._t = setTimeout(() => commit(ta.value), 600); } });
      ta.addEventListener("change", () => commit(ta.value));
      requestAnimationFrame(() => autoGrow(ta));
      return ta;
    }
    if (t === "bool") {
      const cb = el("input", { type: "checkbox", disabled: ro, checked: !!val });
      cb.addEventListener("change", () => (onChange ? onChange(cb.checked) : setValue(key, cb.checked)));
      return cb;
    }
    const typeMap = { number: "number", date: "date", time: "time", email: "email", tel: "tel", lat: "number", lng: "number", text: "text" };
    const inp = el("input", {
      type: typeMap[t] || "text", disabled: ro, dataset: onChange ? {} : { key },
      "aria-label": spec.label || "",
      inputmode: t === "number" || t === "lat" || t === "lng" ? "decimal" : (t === "tel" ? "tel" : null),
      step: t === "number" || t === "lat" || t === "lng" ? "any" : null,
      min: t === "number" ? "0" : null,
    });
    inp.value = val === undefined || val === null ? "" : val;
    ctrlNode = inp;
    const fire = () => {
      let v = inp.value;
      if (t === "number" || t === "lat" || t === "lng") v = v === "" ? "" : (isFinite(Number(v)) ? Number(v) : v);
      commit(v);
    };
    inp.addEventListener("change", fire);
    if (t === "text" || t === "email" || t === "tel") {
      inp.addEventListener("input", () => { if (!onChange) { clearTimeout(inp._t); inp._t = setTimeout(fire, 800); } });
    }
    if (spec.unit) {
      return el("span", { class: "withunit" }, spec.unit === "Rs" ? el("span", { class: "unit", text: "Rs" }) : null, inp,
        spec.unit !== "Rs" ? el("span", { class: "unit", text: spec.unit }) : null);
    }
    return inp;
  }

  const labelled = (label, ctrl, key) => el("div", { class: "lf" }, el("label", { class: "lfl", text: label }), ctrl, key ? errSlot(key) : null);

  // ------------------------------------------------------------ attachments
  function attachmentBox(unitKey, pkey) {
    const list = ATT[unitKey] || [];
    const ro = !canEditPart(pkey);
    if (ro && !list.length) return null;
    const box = el("div", { class: "attbox", dataset: { att: unitKey } });
    const files = el("div", { class: "attlist" });
    const renderList = () => {
      files.textContent = "";
      (ATT[unitKey] || []).forEach(a => {
        const item = el("div", { class: "att" });
        if (a.image) {
          const img = el("img", { src: a.url, alt: a.name, loading: "lazy", class: "thumb" });
          img.addEventListener("click", () => openLightbox(a.url));
          item.appendChild(img);
        } else {
          item.appendChild(el("a", { href: a.url, target: "_blank", rel: "noopener", class: "docicon", text: "PDF" }));
        }
        item.appendChild(el("div", { class: "attmeta" },
          el("a", { href: a.url + "?download=1", text: a.name }),
          el("small", { class: "muted", text: (a.caption ? a.caption + " · " : "") + Math.max(1, Math.round(a.size / 1024)) + " KB" + (a.by ? " · " + a.by : "") })));
        if (!ro && a.can_delete) {
          item.appendChild(el("button", {
            type: "button", class: "linkbtn danger", text: "Remove", onclick: async () => {
              if (!confirm("Remove this file from the inspection record?")) return;
              const r = await fetch(C.urls.delete + a.id + "/delete/", { method: "POST", credentials: "same-origin", headers: { "X-CSRFToken": csrf() } });
              const b = await r.json().catch(() => ({}));
              if (r.ok && b.ok) { ATT[unitKey] = (ATT[unitKey] || []).filter(x => x.id !== a.id); renderList(); updateAttCount(); }
              else alert(b.error || "Could not remove the file.");
            },
          }));
        }
        files.appendChild(item);
      });
    };
    const countEl = el("span", { class: "attcount" });
    const updateAttCount = () => { const n = (ATT[unitKey] || []).length; countEl.textContent = n ? " (" + n + ")" : ""; };
    updateAttCount();
    renderList();
    box.appendChild(files);
    if (!ro) {
      const status = el("span", { class: "muted small" });
      const doUpload = async (input) => {
        const fl = Array.from(input.files || []);
        input.value = "";
        if (!fl.length) return;
        if (!navigator.onLine) { alert("You are offline. Photos and documents can be uploaded when the connection returns. Your typed entries are saved on this device."); return; }
        for (const f of fl) {
          const ext = (f.name.split(".").pop() || "").toLowerCase();
          if (!C.upload.types.includes(ext) && !(f.type === "image/jpeg" && C.upload.types.includes("jpg"))) { alert(f.name + ": file type not allowed (" + C.upload.types.join(", ") + ")."); continue; }
          if (f.size > C.upload.max_mb * 1048576) { alert(f.name + ": larger than " + C.upload.max_mb + " MB."); continue; }
          const fd = new FormData();
          fd.append("file", f, f.name || ("photo." + (f.type === "image/png" ? "png" : "jpg")));
          fd.append("unit_key", unitKey);
          status.textContent = "Uploading " + f.name + "…";
          try {
            const r = await fetch(C.urls.upload, { method: "POST", credentials: "same-origin", headers: { "X-CSRFToken": csrf() }, body: fd });
            const b = await r.json();
            if (r.ok && b.ok) { (ATT[unitKey] = ATT[unitKey] || []).push(b.attachment); renderList(); updateAttCount(); status.textContent = "Uploaded."; }
            else { status.textContent = ""; alert(b.error || "Upload failed."); }
          } catch (e) { status.textContent = ""; alert("Upload failed — check the connection and try again."); }
        }
      };
      const accept = C.upload.types.map(t => "." + t).join(",");
      const cam = el("input", { type: "file", accept: "image/*", capture: "environment", hidden: true, onchange: (e) => doUpload(e.target) });
      const pick = el("input", { type: "file", accept, multiple: true, hidden: true, onchange: (e) => doUpload(e.target) });
      box.appendChild(el("div", { class: "attactions" },
        el("button", { type: "button", class: "btn small", onclick: () => cam.click() }, "📷 Take photo"),
        el("button", { type: "button", class: "btn small", onclick: () => pick.click() }, "📎 Attach file", countEl),
        cam, pick, status));
    }
    return box;
  }

  function openLightbox(url) {
    const lb = $("#lightbox");
    if (!lb) { window.open(url, "_blank"); return; }
    lb.querySelector("img").src = url;
    lb.hidden = false;
  }
  const lbx = $("#lightbox");
  if (lbx) lbx.addEventListener("click", () => { lbx.hidden = true; lbx.querySelector("img").src = ""; });

  // ------------------------------------------------------------ row editor (grids)
  function rowsEditor(key, columns, opts) {
    // columns: [{k,label,t,options,calc,short}], opts: {ro, minRows, initialRows, fixedFirst, numbered, headerLabels, onRowsChange}
    const wrap = el("div", { class: "rows", dataset: { key } });
    let rows = Array.isArray(D[key]) ? JSON.parse(JSON.stringify(D[key])) : [];
    if (!rows.length && opts.initialRows) rows = JSON.parse(JSON.stringify(opts.initialRows));
    if (opts.fixedFirst && (!rows.length || Object.entries(opts.fixedFirst).some(([k, v]) => rows[0][k] !== v))) {
      rows.unshift(Object.assign({}, opts.fixedFirst));
    }
    while (rows.length < (opts.minRows || 0)) rows.push({});
    const commit = () => {
      const clean = rows.map(r => {
        const o = {};
        for (const [k, v] of Object.entries(r)) if (v !== "" && v !== null && v !== undefined) o[k] = v;
        return o;
      });
      // Keep fixed/initial rows' labels; drop trailing empty rows beyond the minimum.
      while (clean.length > (opts.minRows || 0) && !rowFilled(clean[clean.length - 1]) &&
             !(opts.fixedFirst && clean.length === 1)) clean.pop();
      const anyData = clean.some(r => rowFilled(r) && !isOnlyFixed(r));
      setValue(key, anyData ? clean : "");
    };
    const isOnlyFixed = (r) => {
      const base = Object.assign({}, opts.fixedFirst || {});
      const keys = Object.keys(r).filter(k => isFilled(r[k]));
      return keys.length && keys.every(k => (base[k] !== undefined && base[k] === r[k]) ||
        (opts.initialRows || []).some(ir => ir[k] === r[k] && Object.keys(ir).includes(k)));
    };
    const draw = () => {
      wrap.textContent = "";
      rows.forEach((row, i) => {
        const card = el("div", { class: "rowcard" });
        const head = el("div", { class: "rowhead" }, el("strong", { text: opts.numbered ? String(i + 1) : "Row " + (i + 1) }));
        const locked = opts.fixedFirst && i === 0;
        if (!opts.ro && !locked && rows.length > (opts.minRows || 0)) {
          head.appendChild(el("button", {
            type: "button", class: "linkbtn danger", text: "Delete row", onclick: () => {
              if (rowFilled(row) && !confirm("Delete this row?")) return;
              rows.splice(i, 1); draw(); commit();
            },
          }));
        }
        card.appendChild(head);
        const grid = el("div", { class: "rowfields" });
        columns.forEach(c => {
          let label = c.label;
          if (c.group && opts.headerLabels) {
            const h = opts.headerLabels[c.group];
            if (h) label = label.replace(/\((\d)\)/, "(" + h + ")");
          }
          let ctrl;
          if (c.calc) {
            const v = calcValue(c.calc, row);
            ctrl = el("output", { class: "calc", text: v === "" ? "—" : v + " %" });
          } else if (locked && opts.fixedFirst[c.k] !== undefined) {
            ctrl = el("div", { class: "fixedval", text: opts.fixedFirst[c.k] });
          } else {
            const rowKeyLocked = opts.lockCols && opts.lockCols(row, c.k);
            ctrl = scalarInput(key + "[" + i + "]." + c.k, { t: c.t, options: c.options, label, value: row[c.k] }, opts.ro || rowKeyLocked, (v) => {
              row[c.k] = v;
              if (columns.some(cc => cc.calc)) draw();
              commit();
            });
          }
          grid.appendChild(el("div", { class: "lf" + (c.t === "textarea" ? " wide" : "") }, el("label", { class: "lfl", text: label }), ctrl));
        });
        card.appendChild(grid);
        if (opts.rowExtra) { const x = opts.rowExtra(row, i, draw, commit); if (x) card.appendChild(x); }
        wrap.appendChild(card);
      });
      if (!opts.ro) {
        wrap.appendChild(el("button", { type: "button", class: "btn small addrow", onclick: () => { rows.push({}); draw(); } }, "+ Add row"));
      }
    };
    draw();
    wrap._redraw = () => { rows = Array.isArray(D[key]) ? JSON.parse(JSON.stringify(D[key])) : rows; draw(); };
    return wrap;
  }

  function calcValue(calc, row) {
    if (calc[0] === "pct") {
      const p = Number(row[calc[1]]), a = Number(row[calc[2]]);
      if (row[calc[1]] === undefined || row[calc[2]] === undefined || row[calc[1]] === "" || row[calc[2]] === "" || !(a > 0)) return "";
      return Math.round(1000 * p / a) / 10;
    }
    return "";
  }

  // ------------------------------------------------------------ item wrappers
  function itemShell(unitKey, pkey, sno, contentNodes, extraClass) {
    const u = UNIT_BY_KEY[unitKey];
    const mand = MANDATORY.has(unitKey);
    const node = el("div", { class: "item " + (extraClass || "") + (mand ? " mandatory" : ""), id: "u-" + unitKey.replace(/\./g, "-"), dataset: { unit: unitKey } },
      el("div", { class: "sno" }, el("span", { text: sno }), mand ? el("span", { class: "req", title: "Mandatory", text: "*" }) : null,
        el("span", { class: "dot", title: "Answered" })),
      el("div", { class: "itembody" }, contentNodes, attachmentBox(unitKey, pkey)));
    if (u) node.classList.toggle("answered", unitAnswered(u));
    return node;
  }

  function refreshUnit(key) {
    const spec = Object.values(UNIT_BY_KEY).find(u => u.inputs.includes(key));
    if (!spec) return;
    const node = document.querySelector('[data-unit="' + CSS.escape(spec.key) + '"]');
    if (node) node.classList.toggle("answered", unitAnswered(spec));
  }

  function rerenderKey(key) {
    const n = document.querySelector('.rows[data-key="' + CSS.escape(key) + '"]');
    if (n && n._redraw) n._redraw();
    if (key === "SA.J8.members") { const d = document.querySelector('[data-decl]'); if (d && d._redraw) d._redraw(); }
  }

  // ------------------------------------------------------------ blocks
  function blockParticulars(b, sid, pkey, ro) {
    const out = el("div", { class: "block" });
    b.rows.forEach(r => {
      const uk = sid + "." + r.sno;
      const fields = el("div", { class: "fields" });
      r.fields.forEach(f => {
        const key = f.k ? uk + "." + f.k : uk;
        if (f.t === "rows") {
          fields.appendChild(el("div", { class: "lf wide" }, rowsEditor(key, f.columns, { ro, minRows: 1 })));
        } else {
          const ctrl = scalarInput(key, { t: f.t, options: f.options, label: f.label || r.text }, ro);
          fields.appendChild(f.label ? labelled(f.label, ctrl, key) : el("div", { class: "lf" + (f.t === "radio" ? " wide" : "") }, ctrl, errSlot(key)));
        }
      });
      if (r.geo && !ro) {
        fields.appendChild(el("div", { class: "lf" }, el("button", {
          type: "button", class: "btn small", onclick: (e) => {
            const btn = e.target;
            if (!navigator.geolocation) { alert("Location is not available on this device."); return; }
            btn.textContent = "Getting location…";
            navigator.geolocation.getCurrentPosition((pos) => {
              setValue(uk + ".lat", Number(pos.coords.latitude.toFixed(6)));
              setValue(uk + ".lng", Number(pos.coords.longitude.toFixed(6)));
              document.querySelector('[data-key="' + uk + '.lat"]').value = pos.coords.latitude.toFixed(6);
              document.querySelector('[data-key="' + uk + '.lng"]').value = pos.coords.longitude.toFixed(6);
              btn.textContent = "📍 Location captured (±" + Math.round(pos.coords.accuracy) + " m)";
            }, (err) => { btn.textContent = "📍 Use current location"; alert("Could not get location: " + err.message); },
            { enableHighAccuracy: true, timeout: 20000, maximumAge: 0 });
          },
        }, "📍 Use current location")));
      }
      out.appendChild(itemShell(uk, pkey, r.sno, [el("div", { class: "qtext", text: r.text }), fields], "particular"));
    });
    return out;
  }

  function blockChecklist(b, sid, pkey, ro) {
    const out = el("div", { class: "block" });
    out.appendChild(el("div", { class: "colhead" + (b.no_norm ? " nonorm" : "") },
      el("span", { text: "S.No" }), el("span", { text: "Item to verify" }), b.no_norm ? null : el("span", { text: "Norm / Ref" }),
      el("span", { text: "Observed" }), el("span", { text: "C/P/N" })));
    b.rows.forEach(r => {
      const uk = sid + "." + r.sno;
      const q = el("div", { class: "qtext" }, r.star ? el("span", { class: "star", title: S.star_legend, text: "★ " }) : null, r.text);
      const norm = (!b.no_norm && r.norm) ? el("div", { class: "norm" }, el("span", { class: "normlabel", text: "Norm / Ref: " }), r.norm) : null;
      const extras = (r.extras || []).map(x => labelled(x.label + (x.unit && x.unit !== "Rs" ? " (" + x.unit + ")" : ""), scalarInput(uk + "." + x.k, x, ro), uk + "." + x.k));
      const obs = labelled("Observed", scalarInput(uk + ".obs", { t: "textarea", label: "Observed", rows: 1 }, ro), uk + ".obs");
      const cpn = labelled("C/P/N", scalarInput(uk + ".cpn", { t: "radio", options: CPN, label: "C/P/N" }, ro), uk + ".cpn");
      out.appendChild(itemShell(uk, pkey, r.sno, [q, norm, extras.length ? el("div", { class: "fields" }, extras) : null, el("div", { class: "fields obsrow" }, obs, cpn)], "check"));
    });
    return out;
  }

  function blockArea(b, sid, pkey, ro) {
    const out = el("div", { class: "block" });
    b.rows.forEach(r => {
      const uk = sid + "." + r.sno;
      const q = el("div", { class: "qtext", text: r.text });
      const norm = el("div", { class: "norm" }, el("span", { class: "normlabel", text: "Minimum norm: " }), r.norm);
      let body;
      if (r.repeat) {
        body = rowsEditor(uk, [
          { k: "trade_unit", label: "Trade / unit", t: "text" },
          { k: "measured", label: "Measured area / count", t: "text" },
          { k: "cpn", label: "C/P/N", t: "select", options: CPN },
        ], { ro, minRows: 1 });
      } else {
        body = el("div", { class: "fields obsrow" },
          labelled("Measured area / count", scalarInput(uk + ".measured", { t: "text", label: "Measured area / count" }, ro), uk + ".measured"),
          labelled("C/P/N", scalarInput(uk + ".cpn", { t: "radio", options: CPN, label: "C/P/N" }, ro), uk + ".cpn"));
      }
      out.appendChild(itemShell(uk, pkey, r.sno, [q, norm, body], "check"));
    });
    if (b.footnote) out.appendChild(el("p", { class: "footnote", text: b.footnote }));
    return out;
  }

  function blockGrid(b, sid, pkey, ro) {
    const uk = sid + "." + b.id;
    const nodes = [];
    let headerLabels = null;
    if (b.header_inputs) {
      headerLabels = {};
      const hdr = el("div", { class: "fields" });
      b.header_inputs.forEach(h => {
        const key = uk + ".hdr." + h.k;
        headerLabels[h.k] = D[key] || "";
        const inp = scalarInput(key, { t: h.t, label: h.label }, ro);
        inp.addEventListener("change", () => { headerLabels[h.k] = inp.value; const r = document.querySelector('.rows[data-key="' + uk + '"]'); if (r && r._redraw) r._redraw(); });
        hdr.appendChild(labelled(h.label, inp, key));
      });
      nodes.push(el("div", { class: "hdrinputs" }, el("div", { class: "muted small", text: "Fill in the session / year labels:" }), hdr));
    }
    nodes.push(rowsEditor(uk, b.columns, {
      ro, minRows: b.min_rows || 0, initialRows: b.initial_rows, fixedFirst: b.fixed_first, numbered: b.numbered, headerLabels,
    }));
    return itemShell(uk, pkey, "", nodes, "gridblock");
  }

  function blockStaffing(b, sid, pkey, ro) {
    const out = el("div", { class: "block" });
    b.posts.forEach(p => {
      const uk = sid + "." + b.id + "." + p.k;
      const fields = el("div", { class: "fields" }, b.columns.map(c => labelled(c.label, scalarInput(uk + "." + c.k, { t: c.t, label: c.label }, ro), uk + "." + c.k)));
      out.appendChild(itemShell(uk, pkey, "", [el("div", { class: "qtext" }, el("strong", { text: p.post })),
        el("div", { class: "norm" }, el("span", { class: "normlabel", text: "Norm: " }), p.norm), fields], "check"));
      if (p.k === b.trade_rows_after) {
        const tk = sid + "." + b.id + ".trades";
        const cols = [{ k: "trade", label: "Trade", t: "text" }].concat(b.columns);
        out.appendChild(itemShell(tk, pkey, "", [el("div", { class: "qtext muted", text: "Trade instructors — one row per trade:" }), rowsEditor(tk, cols, { ro, minRows: 1 })], "subrows"));
      }
    });
    return out;
  }

  function blockRegister(b, sid, pkey, ro) {
    const out = el("div", { class: "block" });
    b.rows.forEach(r => {
      const uk = sid + "." + r.sno;
      out.appendChild(itemShell(uk, pkey, r.sno, [
        el("div", { class: "qtext", text: r.text }),
        el("div", { class: "norm" }, el("span", { class: "normlabel", text: "Ref: " }), r.norm),
        el("div", { class: "fields obsrow" },
          labelled("Maintained (Y/N)", scalarInput(uk + ".maint", { t: "radio", options: ["Y", "N"] }, ro), uk + ".maint"),
          labelled("Up to date (Y/N)", scalarInput(uk + ".uptodate", { t: "radio", options: ["Y", "N"] }, ro), uk + ".uptodate"),
          labelled("Remarks", scalarInput(uk + ".remarks", { t: "text", label: "Remarks" }, ro), uk + ".remarks")),
      ], "check"));
    });
    return out;
  }

  function blockOffice(b, sid, pkey, ro) {
    const out = el("div", { class: "block" });
    b.rows.forEach(r => {
      const uk = sid + "." + r.sno;
      out.appendChild(itemShell(uk, pkey, r.sr + " " + r.sno, [
        el("div", { class: "qtext", text: r.text }),
        el("div", { class: "norm" }, el("span", { class: "normlabel", text: "Rule / Para: " }), r.norm),
        el("div", { class: "fields obsrow" },
          labelled("Available (Yes/No)", scalarInput(uk + ".avail", { t: "radio", options: ["Yes", "No"] }, ro), uk + ".avail"),
          labelled("Updated up to", scalarInput(uk + ".updated", { t: "date", label: "Updated up to" }, ro), uk + ".updated")),
        el("div", { class: "fields obsrow" },
          labelled("Deficiency observed", scalarInput(uk + ".deficiency", { t: "textarea", rows: 1 }, ro), uk + ".deficiency"),
          labelled("Action required", scalarInput(uk + ".action", { t: "textarea", rows: 1 }, ro), uk + ".action")),
      ], "check"));
    });
    return out;
  }

  function blockJ1(b, sid, pkey, ro) {
    const out = el("div", { class: "block" });
    b.rows.forEach(r => {
      const uk = sid + ".J1." + r.k;
      out.appendChild(itemShell(uk, pkey, "", [
        el("div", { class: "qtext", text: r.ground }),
        el("div", { class: "norm" }, el("span", { class: "normlabel", text: "Linked items: " }), r.linked),
        el("div", { class: "fields obsrow" },
          labelled("Found (Y/N)", scalarInput(uk + ".found", { t: "radio", options: ["Y", "N"] }, ro), uk + ".found"),
          labelled("Evidence (photo / video timestamp / document)", scalarInput(uk + ".evidence", { t: "textarea", rows: 1 }, ro), uk + ".evidence")),
      ], "check"));
    });
    return out;
  }

  function computeJ2() {
    const byBlock = {};
    UNITS.forEach(u => { if (u.key.startsWith("SA.")) (byBlock[u.block] = byBlock[u.block] || []).push(u); });
    const j2 = PARTS.find(p => p.key === "SA.J").part.blocks.find(b => b.type === "j2");
    const tot = { checked: 0, C: 0, P: 0, N: 0, NA: 0 };
    const rows = j2.rows.map(r => {
      const c = { checked: 0, C: 0, P: 0, N: 0, NA: 0 };
      r.blocks.forEach(bid => (byBlock[bid] || []).forEach(u => {
        let vals = [];
        if (u.kind === "register") {
          const m = D[u.key + ".maint"], up = D[u.key + ".uptodate"];
          if (m === "Y" && up === "Y") vals = ["C"]; else if (m === "Y" && up === "N") vals = ["P"]; else if (m === "N") vals = ["N"];
        } else if (u.kind === "area" && Array.isArray(D[u.key])) {
          vals = D[u.key].map(x => x && x.cpn);
        } else if (D[u.key + ".cpn"]) vals = [D[u.key + ".cpn"]];
        vals.forEach(v => { if (["C", "P", "N", "NA"].includes(v)) { c[v]++; c.checked++; } });
      }));
      Object.keys(tot).forEach(k => tot[k] += c[k]);
      return Object.assign({ label: r.label }, c);
    });
    rows.push(Object.assign({ label: "Total", total: true }, tot));
    return rows;
  }

  function blockJ2(b) {
    const wrap = el("div", { class: "block j2", id: "j2" });
    wrap._render = () => {
      wrap.textContent = "";
      const t = el("table", { class: "table small" },
        el("thead", null, el("tr", null, ["Part", "Items checked", "C", "P", "N", "NA"].map((h, i) => el("th", { class: i ? "num" : "", text: h })))),
        el("tbody", null, computeJ2().map(r => el("tr", { class: r.total ? "totalrow" : "" },
          el("td", { text: r.label }), ["checked", "C", "P", "N", "NA"].map(k => el("td", { class: "num", text: String(r[k]) }))))));
      wrap.appendChild(el("div", { class: "tablewrap" }, t));
      wrap.appendChild(el("p", { class: "footnote", text: "Calculated automatically from the C/P/N responses. Part I counts I1 registers as: Maintained Y & Up to date Y = C; Maintained Y & Up to date N = P; Maintained N = N." }));
    };
    wrap._render();
    return wrap;
  }
  function renderJ2() { const j = document.getElementById("j2"); if (j && j._render) j._render(); }

  function blockChoice(b, sid, pkey, ro) {
    const uk = sid + "." + b.id;
    const val = D[uk];
    const name = "c_" + uk;
    const list = el("div", { class: "choices", role: "radiogroup", dataset: { key: uk } });
    b.options.forEach((o, i) => {
      const id = name + "_" + i;
      const inp = el("input", { type: "radio", name, id, value: o, disabled: ro, checked: val === o });
      inp.addEventListener("change", () => setValue(uk, o));
      list.appendChild(el("label", { for: id, class: "choice" }, inp, el("span", { text: o })));
    });
    if (!ro) list.appendChild(el("button", { type: "button", class: "linkbtn", text: "Clear selection", onclick: () => { list.querySelectorAll("input").forEach(x => x.checked = false); setValue(uk, ""); } }));
    return itemShell(uk, pkey, "", [list, errSlot(uk)], "choiceblock");
  }

  function blockText(b, sid, pkey, ro) {
    const uk = sid + "." + b.id;
    return itemShell(uk, pkey, "", [scalarInput(uk, { t: "textarea", rows: 5, label: b.title }, ro), errSlot(uk)], "textblock");
  }

  function blockDeclaration(b, sid, pkey, ro) {
    const uk = sid + "." + b.id;
    const mkey = uk + ".members";
    const decl = el("div", { dataset: { decl: "1" } });
    decl._redraw = () => {
      decl.textContent = "";
      const members = Array.isArray(D[mkey]) ? JSON.parse(JSON.stringify(D[mkey])) : [];
      const commit = () => setValue(mkey, members, { now: true });
      members.forEach((m, i) => {
        const mine = m.user_id && m.user_id === C.user_id;
        const card = el("div", { class: "rowcard decl" + (m.declared ? " signed" : "") });
        card.appendChild(el("div", { class: "rowhead" }, el("strong", { text: "Member " + (i + 1) }),
          (!ro && !m.user_id) ? el("button", { type: "button", class: "linkbtn danger", text: "Delete row", onclick: () => { members.splice(i, 1); D[mkey] = members; commit(); decl._redraw(); } }) : null));
        const f = el("div", { class: "rowfields" });
        f.appendChild(el("div", { class: "lf" }, el("label", { class: "lfl", text: "Name" }),
          m.user_id ? el("div", { class: "fixedval", text: m.name || "" }) :
            scalarInput(mkey + i + "name", { t: "text", value: m.name }, ro, v => { m.name = v; D[mkey] = members; commit(); })));
        f.appendChild(el("div", { class: "lf" }, el("label", { class: "lfl", text: "Designation and office" }),
          scalarInput(mkey + i + "desig", { t: "text", value: m.designation }, ro || (m.user_id && !mine), v => { m.designation = v; D[mkey] = members; commit(); })));
        let sig;
        if (!m.user_id) sig = el("div", { class: "muted small", text: "No portal login — signs on the printed copy." });
        else if (mine && !ro) {
          const cb = el("input", { type: "checkbox", checked: !!m.declared });
          cb.addEventListener("change", () => {
            if (cb.checked && !confirm("Record your declaration as stated above? This acts as your signature on this inspection report.")) { cb.checked = false; return; }
            m.declared = cb.checked;
            if (cb.checked && !m.date) m.date = new Date().toISOString().slice(0, 10);
            D[mkey] = members; commit(); decl._redraw();
          });
          sig = el("label", { class: "check" }, cb, " I make this declaration");
        } else sig = el("div", { class: m.declared ? "ok" : "muted", text: m.declared ? "✔ Declared" : "Not yet declared" });
        f.appendChild(el("div", { class: "lf" }, el("label", { class: "lfl", text: "Signature" }), sig,
          m.declared && m.declared_at ? el("small", { class: "muted", text: "Recorded electronically " + m.declared_at + (m.declared_by ? " by " + m.declared_by : "") }) : null));
        f.appendChild(el("div", { class: "lf" }, el("label", { class: "lfl", text: "Date" }),
          scalarInput(mkey + i + "date", { t: "date", value: m.date }, ro || (m.user_id && !mine), v => { m.date = v; D[mkey] = members; commit(); })));
        card.appendChild(f);
        decl.appendChild(card);
      });
      if (!ro) decl.appendChild(el("button", { type: "button", class: "btn small", onclick: () => { members.push({ name: "", designation: "", declared: false }); D[mkey] = members; decl._redraw(); } }, "+ Add member without portal login"));
    };
    decl._redraw();
    const ack = el("div", { class: "ack" },
      el("p", { text: "Acknowledgement by Principal: received a copy of this inspection report on ________. Action Taken Report will be submitted by ________." }),
      el("div", { class: "fields" },
        labelled("Copy received by Principal on", scalarInput(uk + ".ack_received", { t: "date" }, ro), uk + ".ack_received"),
        labelled("Action Taken Report will be submitted by", scalarInput(uk + ".atr_due", { t: "date" }, ro), uk + ".atr_due")),
      el("p", { class: "muted small", text: "Signature and seal of Principal: attach a photo or scan of the signed acknowledgement / signed declaration page below." }));
    return itemShell(uk, pkey, "", [el("blockquote", { class: "decltext", text: b.text }), decl, ack], "declblock");
  }

  const RENDERERS = {
    particulars: blockParticulars, checklist: blockChecklist, area: blockArea, grid: blockGrid,
    staffing: blockStaffing, register: blockRegister, office: blockOffice, j1: blockJ1, j2: blockJ2,
    choice: blockChoice, text: blockText, declaration: blockDeclaration,
  };

  // ------------------------------------------------------------ parts & navigation
  const root = $("#formroot");
  const nav = $("#partnav");
  const single = MODE === "edit";
  let current = 0;

  function renderPart(p, idx) {
    const sid = p.section.id;
    const ro = !canEditPart(p.key);
    const sec = el("section", { class: "part", id: "part-" + p.key.replace(".", "-"), dataset: { part: p.key } });
    if (idx === 0 || PARTS[idx - 1].section.id !== sid) sec.appendChild(el("div", { class: "sectiontitle", text: p.section.title }));
    sec.appendChild(el("h2", { class: "parttitle", text: p.part.title }));
    if (!partApplicable(p)) {
      sec.appendChild(el("div", { class: "msg msg-info", text: "Not applicable — this part applies to Government ITIs only." }));
      return sec;
    }
    if (MODE === "edit" && ro) sec.appendChild(el("div", { class: "msg msg-info", text: "View only — this part is not assigned to you." }));
    if (p.part.blocks.some(b => b.type === "checklist" || b.type === "area")) {
      sec.appendChild(el("p", { class: "legend muted small", text: S.cpn_legend + (p.part.blocks.some(b => (b.rows || []).some(r => r.star)) ? " · " + S.star_legend : "") }));
    }
    p.part.blocks.forEach(b => {
      if (b.type === "note") { sec.appendChild(el("p", { class: "note", text: b.text })); return; }
      if (b.title && b.type !== "office") sec.appendChild(el("h3", { class: "blocktitle", text: b.title }));
      const r = RENDERERS[b.type];
      if (r) sec.appendChild(r(b, sid, p.key, ro));
    });
    if (single) {
      const prev = PARTS.slice(0, idx).reverse().find(partApplicable);
      const next = PARTS.slice(idx + 1).find(partApplicable);
      sec.appendChild(el("div", { class: "partfoot" },
        prev ? el("button", { type: "button", class: "btn", onclick: () => go(PARTS.indexOf(prev)) }, "‹ Previous") : el("span"),
        el("button", { type: "button", class: "btn", onclick: async () => { await flush(); } }, "Save draft"),
        next ? el("button", { type: "button", class: "btn primary", onclick: async () => { await flush(); go(PARTS.indexOf(next)); } }, "Save and continue ›")
          : el("a", { class: "btn primary", href: C.urls.review }, "Save and review ›")));
    }
    return sec;
  }

  function buildNav() {
    nav.textContent = "";
    const sel = el("select", { class: "partselect", "aria-label": "Go to part" });
    const list = el("ol", { class: "navlist" });
    let lastSec = null;
    PARTS.forEach((p, i) => {
      if (p.section.id !== lastSec) {
        list.appendChild(el("li", { class: "navsec", text: p.section.id === "SA" ? "Section A – Technical Evaluation" : "Section B – Office & Financial" }));
        lastSec = p.section.id;
      }
      const c = partCounts(p.key);
      const app = partApplicable(p);
      const label = (p.section.id === "SB" ? "B-" : "") + p.part.title.replace(/^Part /, "");
      const a = el("a", { href: "#part-" + p.key.replace(".", "-"), class: "navlink" + (i === current && single ? " active" : "") + (!app ? " na" : ""), dataset: { navpart: p.key } },
        el("span", { class: "navlabel", text: label }),
        el("span", { class: "navcount" + (app && c.done === c.total ? " full" : ""), text: app ? c.done + "/" + c.total : "NA" }));
      a.addEventListener("click", (e) => { if (single) { e.preventDefault(); go(i); } });
      list.appendChild(el("li", null, a));
      sel.appendChild(el("option", { value: i, text: label + (app ? " (" + c.done + "/" + c.total + ")" : " (NA)"), selected: i === current }));
    });
    sel.addEventListener("change", () => { if (single) go(Number(sel.value)); else document.getElementById("part-" + PARTS[sel.value].key.replace(".", "-")).scrollIntoView(); });
    nav.appendChild(sel);
    nav.appendChild(list);
    if (MODE === "edit") nav.appendChild(el("p", { class: "muted small navhint", text: "Entries save automatically. ● marks answered items." }));
  }

  function go(i) {
    current = i;
    try { localStorage.setItem(LS_PART, String(i)); } catch (e) { /* ignore */ }
    root.textContent = "";
    root.appendChild(renderPart(PARTS[i], i));
    buildNav();
    window.scrollTo(0, 0);
    const hash = location.hash;
    if (hash && hash.startsWith("#u-")) { const n = document.querySelector(hash); if (n) n.scrollIntoView(); }
  }

  function updateProgress() {
    const o = overall();
    const pb = $("#pbar"), pt = $("#ptext");
    if (pb) pb.style.width = o.pct + "%";
    if (pt) pt.textContent = o.pct + "% (" + o.done + "/" + o.total + ")";
    nav.querySelectorAll("[data-navpart]").forEach(a => {
      const p = PARTS.find(x => x.key === a.dataset.navpart);
      if (!partApplicable(p)) return;
      const c = partCounts(p.key);
      const cnt = a.querySelector(".navcount");
      cnt.textContent = c.done + "/" + c.total;
      cnt.classList.toggle("full", c.done === c.total);
    });
  }

  function disableAll() {
    root.querySelectorAll("input, select, textarea, button").forEach(n => { if (!n.closest(".partfoot")) n.disabled = true; });
  }

  // ------------------------------------------------------------ start
  if (single) {
    let start = 0;
    try { start = Number(localStorage.getItem(LS_PART) || 0); } catch (e) { start = 0; }
    if (!(start >= 0 && start < PARTS.length)) start = 0;
    current = start;
    buildNav();
    go(start);
  } else {
    buildNav();
    root.textContent = "";
    PARTS.forEach((p, i) => root.appendChild(renderPart(p, i)));
  }
  updateProgress();
  if (MODE === "edit") {
    const sb = $("#btn-save");
    if (sb) sb.addEventListener("click", async () => { const ok = await flush(); if (ok !== false && !Object.keys(pending).length) setState("Draft saved", "ok"); });
    const rv = $("#btn-review");
    if (rv) rv.addEventListener("click", async (e) => {
      if (Object.keys(pending).length) {
        e.preventDefault();
        const ok = await flush();
        if (Object.keys(pending).length) { alert("Some entries could not be sent to the server yet (no connection). They are kept on this device. Please review once you are online."); return; }
        location.href = rv.href;
      }
    });
    updateStateIdle();
    if (Object.keys(pending).length) flush();
  }
})();
