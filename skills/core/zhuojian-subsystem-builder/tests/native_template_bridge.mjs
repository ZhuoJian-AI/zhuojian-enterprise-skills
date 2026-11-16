import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import vm from 'node:vm';
import { webcrypto } from 'node:crypto';

const html = (await readFile(process.argv[2], 'utf8')).replaceAll('__MODULE_KEY__', 'orders');
const inline = [...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)]
  .map(match => match[1]).find(text => text.includes('const moduleKey='));
assert.ok(inline);
const navigation = await readFile(new URL('../assets/native-subsystem-template/static/zhuojian-navigation.js', import.meta.url), 'utf8');
const origin = 'https://platform.test';
const turn = () => new Promise(resolve => setImmediate(resolve));
const deferred = () => { let resolve; const promise = new Promise(done => { resolve = done; }); return { promise, resolve }; };

async function fixture(options = {}) {
  const parentOrigin = options.parentOrigin ?? origin;
  const elements = new Map(), events = new Map(), posts = [], calls = [], sdk = deferred();
  function element() { return { value: '', files: [], dataset: {}, hidden: false, disabled: false, textContent: '',
    children: [], addEventListener() {}, setAttribute() {}, append(...items) { this.children.push(...items); },
    replaceChildren(...items) { this.children = items; }, querySelector() { return null; } }; }
  const get = id => { if (!elements.has(id)) elements.set(id, element()); return elements.get(id); };
  const parent = { postMessage: (data, target) => posts.push({ data, target }) };
  const window = { parent, addEventListener(name, fn) { if (!events.has(name)) events.set(name, new Set()); events.get(name).add(fn); },
    removeEventListener(name, fn) { events.get(name)?.delete(fn); } };
  const bootstrap = { applicationSlug: 'sample', launchNonce: 'nonce-1', platformOrigin: origin,
    actionKeys: ['orders.query'], platformAiCapabilities: [], ...options.bootstrap };
  const context = vm.createContext({ window, parent, document: { referrer: options.referrer ?? '',
    getElementById: get, createElement: element, documentElement: { setAttribute() {} },
    body: { dataset: {} }, addEventListener() {} }, location: { pathname: '/orders' },
    history: { state: {}, pushState() {}, back() {} }, URL, URLSearchParams, crypto: webcrypto,
    console: { warn() {} }, setTimeout, clearTimeout,
    async fetch(url, init) {
      calls.push({ url: String(url), init });
      if (String(url).startsWith('/api/ui/bootstrap')) return { ok: true, json: async () => bootstrap };
      if (options.pendingReads) await options.pendingReads.promise;
      const isFiles = String(url).startsWith('/api/ui/files');
      const status = isFiles ? (options.fileStatus ?? 200) : (options.queryStatus ?? 200);
      return { ok: status === 200, status, json: async () => status === 200
        ? { items: isFiles ? [] : [{ id: 'existing-record', status: 'existing', version: 1 }] }
        : { detail: 'Existing business request failed' } };
    },
    async importModule(path) {
      if (path.endsWith('zhuojian-navigation.js')) {
        if (options.navigation === 'fail') throw new Error('SDK unavailable');
        if (options.navigation === 'late') await sdk.promise;
        return { createNavigation: context.navigationFactory };
      }
      if (options.presence === 'fail') throw new Error('Optional SDK unavailable');
      if (options.presence === 'pending') return new Promise(() => {});
      return { createAssistantPresence() {} };
    },
  });
  vm.runInContext(navigation.replace('export function', 'function') + '\nthis.navigationFactory = createNavigation;', context);
  vm.runInContext(inline.replaceAll('await import(', 'await importModule('), context);
  async function emit(data, overrides = {}) {
    for (const fn of [...(events.get('message') || [])]) await fn({ source: parent, origin: parentOrigin, data, ...overrides });
  }
  const load = () => Promise.all([...(events.get('load') || [])].map(fn => fn()));
  return { context, elements, posts, calls, get, parent, emit, load, releaseSdk: sdk.resolve,
    identity: { version: 1, application_slug: 'sample', launch_nonce: 'nonce-1', module_key: 'orders', page_key: 'orders.list' } };
}

for (const referrer of ['', 'https://app.test/own-login', 'https://wrong.test/path', origin + '/home']) {
  const f = await fixture({ referrer }); await f.load(); await turn();
  const ready = f.posts.find(item => item.data.type === 'zhuojian:ready');
  assert.ok(ready, `real template must announce an interactive view with referrer ${referrer}`);
  assert.deepEqual(Object.keys(ready.data).sort(), ['application_slug', 'launch_nonce', 'type', 'version']);
  assert.ok(f.posts.every(item => item.target === origin));
  assert.equal(f.posts.find(item => item.data.type === 'zhuojian:context').data.page_key, 'orders.list');
  assert.equal(f.get('upload').hidden, true);
  assert.equal(f.get('refresh').hidden, false);
}

for (const platformOrigin of [origin, 'https://allowed-alias.test']) {
  const f = await fixture({ parentOrigin: platformOrigin, bootstrap: { platformOrigin }, referrer: 'https://wrong.test/' });
  await f.load(); await turn();
  assert.ok(f.posts.some(item => item.data.type === 'zhuojian:ready'));
  assert.ok(f.posts.every(item => item.target === platformOrigin), 'the exact server-bound alias, not a canonical constant, receives Bridge messages');
}

for (const platformOrigin of ['', 'http://platform.test', 'https://platform.test/path',
  'https://platform.test/?x=1', 'https://user:pass@platform.test', 'https://platform.test/#hash']) {
  const f = await fixture({ referrer: origin + '/home', bootstrap: { platformOrigin } }); await f.load();
  assert.equal(f.posts.length, 0, 'referrer never replaces an invalid trusted bootstrap origin');
  assert.equal(f.calls.length, 1);
}

for (const options of [{ navigation: 'fail', presence: 'fail' }, { navigation: 'late', presence: 'pending' }]) {
  const pendingReads = deferred(), f = await fixture({ ...options, pendingReads });
  await f.load();
  assert.ok(f.posts.some(item => item.data.type === 'zhuojian:ready'), 'ready is interactive view, not all-read success');
  if (options.navigation === 'late') {
    const before = f.posts.filter(item => item.data.type === 'zhuojian:ready').length;
    f.releaseSdk(); await turn();
    assert.equal(f.posts.filter(item => item.data.type === 'zhuojian:ready').length, before + 1);
  }
  pendingReads.resolve(); await turn();
}

for (const actionKeys of [['orders.create'], [], ['orders.update']]) {
  const f = await fixture({ bootstrap: { actionKeys } }); await f.load(); await turn();
  assert.equal(f.calls.length, 1, 'a legitimate non-query page must not execute a query to initialize');
  assert.ok(f.posts.some(item => item.data.type === 'zhuojian:ready'));
  assert.equal(f.get('upload').hidden, !actionKeys.includes('orders.create'));
  assert.equal(f.get('refresh').hidden, true);
}
for (const options of [{ fileStatus: 404 }, { fileStatus: 403 }, { queryStatus: 500 }]) {
  const f = await fixture(options); await f.load(); await turn();
  assert.ok(f.posts.some(item => item.data.type === 'zhuojian:ready'), 'an independent read failure must render its error without a parent mask');
  assert.equal(f.get(options.queryStatus ? 'status' : 'file-status').className, 'error');
}

const f = await fixture({ referrer: 'https://wrong.test' }); await f.load(); await turn();
const refresh = { ...f.identity, type: 'zhuojian:refresh', request_id: 'refresh-0001' };
for (const [data, overrides] of [
  [refresh, { source: {} }], [refresh, { origin: 'https://wrong.test' }],
  [{ ...refresh, application_slug: 'other' }], [{ ...refresh, launch_nonce: 'stale' }],
  [{ ...refresh, module_key: 'other' }], [{ ...refresh, page_key: 'orders.other' }],
  [{ ...refresh, unexpected: true }], [{ ...refresh, request_id: '../invalid' }],
]) { const before = f.calls.length; await f.emit(data, overrides); assert.equal(f.calls.length, before); }
await f.emit(refresh);
assert.equal(f.posts.at(-1).data.status, 'completed');
assert.equal(f.posts.at(-1).data.request_id, refresh.request_id);
const after = f.calls.length; await f.emit(refresh); assert.equal(f.calls.length, after, 'refresh replay remains idempotent');

for (const [index, id] of ['file', 'platform-ai-instruction', 'platform-ai-text', 'platform-ai-files'].entries()) {
  const input = f.get(id); if (id.endsWith('file') || id.endsWith('files')) input.files = [{ name: 'unsaved.txt' }]; else input.value = 'unsaved input';
  const before = f.calls.length;
  await f.emit({ ...refresh, request_id: `dirty-000${index}` });
  assert.equal(f.posts.at(-1).data.status, 'deferred');
  assert.equal(f.calls.length, before);
  await f.get('refresh').onclick(); assert.equal(f.calls.length, before);
  await f.emit({ type: 'zhuojian:prepare-leave', version: 1, application_slug: 'sample', launch_nonce: 'nonce-1', request_id: `leave-000${index}` });
  assert.equal(f.posts.at(-1).data.dirty, true);
  input.files = []; input.value = '';
}
vm.runInContext('currentAiDraft = { existing: true };', f.context);
await f.emit({ ...refresh, request_id: 'draft-0001' }); assert.equal(f.posts.at(-1).data.status, 'deferred');
console.log('PASS real native template: trusted bootstrap without referrer; strict scope; optional/late SDK; query-only/non-query/no-files/read-error readiness; dirty refresh/leave');
