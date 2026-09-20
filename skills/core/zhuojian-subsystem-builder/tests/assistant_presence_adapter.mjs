import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import vm from 'node:vm';

const source = await readFile(process.argv[2], 'utf8');
const messages = [];
const listeners = new Map();
const parent = { postMessage: (data, origin) => messages.push({ data, origin }) };
const anchor = {
  isConnected: true,
  getAttribute: name => name === 'data-zhuojian-anchor' ? 'results' : null,
  getBoundingClientRect: () => ({ top: 80, left: 40, right: 340, bottom: 220, width: 300, height: 140 }),
  scrollIntoView: () => { anchor.scrolled = true; },
};
const appended = [];
const document = {
  querySelectorAll: selector => selector === '[data-zhuojian-anchor]' ? [anchor] : [],
  createElement: tag => ({
    tag, dataset: {}, style: {}, textContent: '', isConnected: true,
    setAttribute() {}, append(...children) { this.children = children; }, remove() { this.removed = true; },
  }),
  body: { append: element => appended.push(element) },
};
const window = {
  parent,
  innerWidth: 390,
  innerHeight: 700,
  matchMedia: () => ({ matches: false }),
  addEventListener(type, handler) {
    if (!listeners.has(type)) listeners.set(type, new Set());
    listeners.get(type).add(handler);
  },
  removeEventListener(type, handler) { listeners.get(type)?.delete(handler); },
  setTimeout,
  clearTimeout,
};
const context = { window, document, URL, Set, Array, Number, Object, setTimeout, clearTimeout };
vm.runInNewContext(
  source.replace('export function', 'function') + '\nthis.factory = createAssistantPresence;',
  context,
);
const origin = 'https://platform.test';
const identity = {
  version: 1,
  application_slug: 'sample',
  launch_nonce: 'launch-01234567',
};
const emit = (data, overrides = {}) => {
  for (const handler of listeners.get('message') || []) {
    handler({ source: parent, origin, data: { ...identity, ...data }, ...overrides });
  }
};
const adapter = context.factory({
  applicationSlug: 'sample',
  launchNonce: 'launch-01234567',
  platformOrigin: origin,
  moduleKey: 'orders',
  pageKey: 'orders.main',
  anchorKeys: ['results', 'missing'],
  durationMs: 20,
});
assert.equal(adapter.supportsAssistantPresence(), false);
emit({ type: 'zhuojian:host-ready', capabilities: ['assistant-presence.v1'] }, { origin: 'https://evil.test' });
assert.equal(messages.length, 0);
emit({ type: 'zhuojian:host-ready', capabilities: ['assistant-presence.v1'] });
assert.equal(adapter.supportsAssistantPresence(), true);
assert.deepEqual(Array.from(messages.at(-1).data.anchor_keys), ['results']);

const request = {
  type: 'zhuojian:assistant-presence',
  request_id: 'assistant-request-0001',
  module_key: 'orders',
  page_key: 'orders.main',
  anchor_key: 'results',
  phase: 'acting',
  label: '正在查询订单',
};
emit({ ...request, selector: '#secret' });
assert.equal(messages.at(-1).data.type, 'zhuojian:assistant-presence-ready');
emit(request);
assert.equal(messages.at(-1).data.status, 'shown');
assert.equal(messages.at(-1).data.anchor_key, 'results');
assert.equal(appended.length, 1);
assert.equal(appended[0].style.pointerEvents, 'none');
emit({ ...request, request_id: 'assistant-request-0002', anchor_key: 'missing' });
assert.equal(messages.at(-1).data.status, 'missing');
emit({ ...request, request_id: 'assistant-request-0003', launch_nonce: 'stale' });
assert.notEqual(messages.at(-1).data.request_id, 'assistant-request-0003');
adapter.dispose();
assert.equal(listeners.get('message').size, 0);
assert.equal(appended[0].removed, true);
console.log('PASS assistant presence identity, registration, no selectors, overlay, fallback, cleanup');
