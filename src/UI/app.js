(() => {
  'use strict';
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const DEFAULT_API = 'http://127.0.0.1:8000';

  const store = {
    get(k, d) { try { return localStorage.getItem(k) || d; } catch { return d; } },
    set(k, v) { try { localStorage.setItem(k, v); } catch {} }
  };

  const state = { api: store.get('sr_api', DEFAULT_API), page: 1, limit: 10, sort_by: '', order: 'asc',
                  course: '', total: 0, students: [], editing: null, deleting: null, loading: false };

  /* ---------- helpers ---------- */
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[c]));
  const grade = m => m >= 90 ? 'S' : m >= 80 ? 'A' : m >= 70 ? 'B' : m >= 60 ? 'C' : m >= 50 ? 'D' : 'F';
  const gradeColor = { S:'#5de0c6', A:'#7b93ff', B:'#a98fff', C:'#ffc46b', D:'#ffa66b', F:'#ff6b81' };

  function toast(msg, type = 'info') {
    const t = document.createElement('div');
    t.className = 'toast ' + type; t.textContent = msg;
    $('#toasts').appendChild(t);
    setTimeout(() => { t.style.transition = 'opacity .3s'; t.style.opacity = 0; setTimeout(() => t.remove(), 300); }, 3800);
  }

  function errText(body, status) {
    const d = body && body.detail;
    if (typeof d === 'string') return d;
    if (Array.isArray(d)) return d.map(e => `${(e.loc || []).slice(1).join('.') || 'input'}: ${e.msg}`).join('\n');
    return `Request failed (${status}).`;
  }

  async function api(path, opts = {}) {
    let res;
    try {
      res = await fetch(state.api.replace(/\/+$/, '') + path, {
        ...opts, headers: { 'Content-Type': 'application/json', ...(opts.headers || {}) }
      });
    } catch {
      setConn(false);
      throw new Error('Cannot reach the API at ' + state.api + '. Check that the server is running and CORS is enabled.');
    }
    setConn(true);
    let body = null;
    try { body = await res.json(); } catch {}
    if (!res.ok) { const e = new Error(errText(body, res.status)); e.status = res.status; throw e; }
    return body;
  }

  function setConn(ok) {
    $('#dot').className = 'dot ' + (ok ? 'on' : 'off');
    $('#connText').textContent = ok ? 'Connected' : 'Offline';
  }

  /* ---------- list ---------- */
  function skeleton() {
    $('#empty').hidden = true;
    $('#rows').innerHTML = Array.from({ length: Math.min(state.limit, 5) }, () =>
      `<tr class="skel">${'<td><div></div></td>'.repeat(7)}</tr>`).join('');
  }

  async function load() {
    state.loading = true; skeleton();
    const q = new URLSearchParams({ page: state.page, limit: state.limit, order: state.order });
    if (state.sort_by) q.set('sort_by', state.sort_by);
    if (state.course.trim()) q.set('course', state.course.trim());
    try {
      const data = await api('/students?' + q);
      state.total = data.total_students; state.students = data.students;
      const pages = Math.max(1, Math.ceil(state.total / state.limit));
      if (state.page > pages) { state.page = pages; return load(); }
      render();
    } catch (e) {
      state.students = []; state.total = 0; render(e.message);
      toast(e.message, 'error');
    } finally { state.loading = false; }
  }

  function render(error) {
    const rows = $('#rows'), empty = $('#empty');
    if (!state.students.length) {
      rows.innerHTML = ''; empty.hidden = false;
      const filtered = state.course.trim();
      empty.innerHTML = error
        ? `<h3>Can’t load students</h3><p>${esc(error)}</p><button class="btn" id="retry" type="button">Try again</button>`
        : `<h3>${filtered ? 'No students match' : 'No students yet'}</h3><p>${filtered ? 'Try a different course name or clear the filter.' : 'Add your first student to start building the record.'}</p><button class="btn primary" id="emptyAdd" type="button">Add student</button>`;
      $('#retry')?.addEventListener('click', load);
      $('#emptyAdd')?.addEventListener('click', () => openForm());
    } else {
      empty.hidden = true;
      rows.innerHTML = state.students.map(s => {
        const g = grade(s.marks);
        return `<tr data-id="${esc(s.id)}">
          <td data-label="ID" class="id">${esc(s.id)}</td>
          <td class="cell-name"><div class="name">${esc(s.name)}</div><div class="mail">${esc(s.email)}</div></td>
          <td data-label="Course"><span class="tag">${esc(s.course)}</span></td>
          <td data-label="Age">${esc(s.age)}</td>
          <td data-label="Marks"><div class="marks"><span>${esc(s.marks)}</span><div class="bar"><i style="width:${s.marks}%;background:${gradeColor[g]}"></i></div></div></td>
          <td data-label="Grade"><span class="grade g-${g}">${g}</span></td>
          <td><div class="row-actions">
            <button class="btn sm" data-act="edit" type="button">Edit</button>
            <button class="btn sm danger" data-act="del" type="button">Delete</button></div></td>
        </tr>`;
      }).join('');
    }
    stats(); pager(); arrows();
  }

  function stats() {
    const m = state.students.map(s => s.marks);
    $('#sTotal').textContent = state.total;
    $('#sAvg').textContent = m.length ? (m.reduce((a, b) => a + b, 0) / m.length).toFixed(1) : '–';
    $('#sTop').textContent = m.length ? Math.max(...m) : '–';
    const counts = {}; m.forEach(x => { const g = grade(x); counts[g] = (counts[g] || 0) + 1; });
    $('#dist').innerHTML = Object.keys(gradeColor).filter(g => counts[g])
      .map(g => `<i title="Grade ${g}: ${counts[g]}" style="flex:${counts[g]};background:${gradeColor[g]}"></i>`).join('');
  }

  function pager() {
    const pages = Math.max(1, Math.ceil(state.total / state.limit));
    const from = state.total ? (state.page - 1) * state.limit + 1 : 0;
    const to = Math.min(state.page * state.limit, state.total);
    $('#pageInfo').textContent = state.total ? `Showing ${from}–${to} of ${state.total} · Page ${state.page} of ${pages}` : 'No results';
    $('#prev').disabled = state.page <= 1;
    $('#next').disabled = state.page >= pages;
  }

  function arrows() {
    $$('.arr').forEach(a => {
      const on = a.dataset.arr === state.sort_by;
      a.classList.toggle('act', on);
      a.textContent = on && state.order === 'desc' ? '▼' : '▲';
    });
    $('#fSort').value = state.sort_by; $('#fOrder').value = state.order;
  }

  /* ---------- form ---------- */
  const form = $('#form'), formDlg = $('#formDlg');
  const fields = ['id', 'name', 'age', 'email', 'course', 'marks'];

  function showErr(name, msg) {
    const el = form.elements[name]; if (!el) return;
    el.classList.toggle('bad', !!msg);
    el.parentElement.querySelector('.err').textContent = msg || '';
  }

  function openForm(student) {
    state.editing = student || null;
    form.reset(); fields.forEach(f => showErr(f, '')); $('#formError').hidden = true;
    $('#formTitle').textContent = student ? 'Edit student' : 'Add student';
    $('#formSub').textContent = student ? `Editing ${student.id}. Only changed fields are sent.` : 'All fields are required.';
    $('#formSave').textContent = student ? 'Save changes' : 'Save student';
    fields.forEach(f => form.elements[f].value = student ? student[f] : '');
    form.elements.id.disabled = !!student;
    formDlg.showModal();
    (student ? form.elements.name : form.elements.id).focus();
  }

  function validate(v) {
    const e = {}, ed = !!state.editing;
    if (!ed && !v.id.trim()) e.id = 'Enter an ID.';
    if (v.name.trim().length < 2 || v.name.trim().length > 50) e.name = 'Use 2–50 characters.';
    else if (!/^[A-Za-z ]+$/.test(v.name.trim())) e.name = 'Letters and spaces only.';
    if (!(+v.age > 0 && +v.age <= 100) || !Number.isInteger(+v.age)) e.age = 'Enter a whole number from 1 to 100.';
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v.email.trim())) e.email = 'Enter a valid email.';
    if (v.course.trim().length < 3 || v.course.trim().length > 50) e.course = 'Use 3–50 characters.';
    if (v.marks === '' || !Number.isInteger(+v.marks) || +v.marks < 0 || +v.marks > 100) e.marks = 'Enter a whole number from 0 to 100.';
    return e;
  }

  form.addEventListener('submit', async ev => {
    ev.preventDefault();
    const v = Object.fromEntries(fields.map(f => [f, form.elements[f].value]));
    const errs = validate(v);
    fields.forEach(f => showErr(f, errs[f]));
    $('#formError').hidden = true;
    if (Object.keys(errs).length) { form.elements[Object.keys(errs)[0]].focus(); return; }

    const payload = { name: v.name.trim(), age: +v.age, email: v.email.trim(), course: v.course.trim(), marks: +v.marks };
    const btn = $('#formSave'); btn.disabled = true; const label = btn.textContent; btn.textContent = 'Saving…';
    try {
      if (state.editing) {
        const changes = Object.fromEntries(Object.entries(payload).filter(([k, val]) => {
          const old = state.editing[k];
          return k === 'name' ? val.toLowerCase() !== String(old).toLowerCase() : val !== old;
        }));
        if (!Object.keys(changes).length) { formDlg.close(); toast('No changes to save.'); return; }
        await api('/update_student/' + encodeURIComponent(state.editing.id), { method: 'PUT', body: JSON.stringify(changes) });
        toast('Student updated.', 'ok');
      } else {
        await api('/create_student', { method: 'POST', body: JSON.stringify({ id: v.id.trim(), ...payload }) });
        toast('Student added.', 'ok');
      }
      formDlg.close(); load();
    } catch (e) {
      const box = $('#formError'); box.textContent = e.message; box.hidden = false;
    } finally { btn.disabled = false; btn.textContent = label; }
  });

  /* ---------- events ---------- */
  $('#btnNew').onclick = () => openForm();
  $('#formCancel').onclick = () => formDlg.close();
  $('#btnReset').onclick = () => {
    Object.assign(state, { page: 1, sort_by: '', order: 'asc', course: '' });
    $('#fCourse').value = ''; load();
  };

  let t;
  $('#fCourse').addEventListener('input', e => { clearTimeout(t); t = setTimeout(() => { state.course = e.target.value; state.page = 1; load(); }, 350); });
  $('#fSort').onchange = e => { state.sort_by = e.target.value; state.page = 1; load(); };
  $('#fOrder').onchange = e => { state.order = e.target.value; state.page = 1; load(); };
  $('#fLimit').onchange = e => { state.limit = +e.target.value; state.page = 1; load(); };
  $('#prev').onclick = () => { if (state.page > 1) { state.page--; load(); } };
  $('#next').onclick = () => { state.page++; load(); };

  $$('th [data-sort]').forEach(b => b.onclick = () => {
    const f = b.dataset.sort;
    if (state.sort_by === f) state.order = state.order === 'asc' ? 'desc' : 'asc';
    else { state.sort_by = f; state.order = 'asc'; }
    state.page = 1; load();
  });

  $('#rows').addEventListener('click', e => {
    const btn = e.target.closest('[data-act]'); if (!btn) return;
    const s = state.students.find(x => x.id === btn.closest('tr').dataset.id); if (!s) return;
    if (btn.dataset.act === 'edit') openForm(s);
    else {
      state.deleting = s;
      $('#delText').textContent = `${s.name} (${s.id}) will be removed permanently.`;
      $('#delDlg').showModal();
    }
  });

  $('#delCancel').onclick = () => $('#delDlg').close();
  $('#delConfirm').onclick = async () => {
    const btn = $('#delConfirm'); btn.disabled = true;
    try {
      await api('/delete_student/' + encodeURIComponent(state.deleting.id), { method: 'DELETE' });
      $('#delDlg').close(); toast('Student deleted.', 'ok');
      if (state.students.length === 1 && state.page > 1) state.page--;
      load();
    } catch (e) { toast(e.message, 'error'); }
    finally { btn.disabled = false; }
  };

  async function lookup() {
    const id = $('#lookupId').value.trim();
    if (!id) { $('#lookupId').focus(); return; }
    try {
      const s = await api('/student/' + encodeURIComponent(id));
      $('#lookupId').value = ''; openForm(s);
    } catch (e) { toast(e.message, 'error'); }
  }
  $('#btnLookup').onclick = lookup;
  $('#lookupId').addEventListener('keydown', e => { if (e.key === 'Enter') lookup(); });

  $('#btnApi').onclick = () => { $('#apiUrl').value = state.api; $('#apiDlg').showModal(); };
  $('#apiCancel').onclick = () => $('#apiDlg').close();
  $('#apiSave').onclick = () => {
    state.api = $('#apiUrl').value.trim() || DEFAULT_API; store.set('sr_api', state.api);
    $('#apiDlg').close(); state.page = 1; load();
  };

  // close dialogs on backdrop click
  $$('dialog').forEach(d => d.addEventListener('click', e => { if (e.target === d) d.close(); }));

  arrows(); load();
})();
