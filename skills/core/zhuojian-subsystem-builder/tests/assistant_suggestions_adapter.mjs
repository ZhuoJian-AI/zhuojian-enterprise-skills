import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import vm from 'node:vm';
import { webcrypto } from 'node:crypto';

const source = await readFile(process.argv[2], 'utf8');
const messages = [], listeners = new Set();
const parent = { postMessage: (data, origin) => messages.push({ data: structuredClone(data), origin }) };
const window = { parent, addEventListener: (_, fn) => listeners.add(fn), removeEventListener: (_, fn) => listeners.delete(fn) };
const sandbox = { window, URL, TextEncoder, crypto: webcrypto, setTimeout, clearTimeout };
vm.runInNewContext(source.replace('export function', 'function') + '\nthis.factory = createAssistant;', sandbox);
const origin = 'https://platform.test';
const identity = { version: 1, application_slug: 'sample', launch_nonce: 'nonce' };
const emit = (data, overrides = {}) => { for (const fn of listeners) fn({ source: parent, origin, data: { ...identity, ...data }, ...overrides }); };
const ready = { type: 'zhuojian:host-ready', capabilities: ['assistant-open.v1', 'assistant-suggestions.v1'] };
const config = { applicationSlug: 'sample', launchNonce: 'nonce', platformOrigin: origin, timeoutMs: 500 };
const adapter = sandbox.factory(config);
const item = { id: 'record-missing-field', revision: 'evidence-7', title: '这条记录还有缺项',
  summary: '当前记录的检查结果包含未补齐字段，可先核对依据。', goal: '请核对当前记录缺项并给出补齐建议，先不要修改。' };
const input = { moduleKey: 'm', pageKey: 'm.detail', context: { route: '/records/1',
  entity_type: 'record', entity_id: '1', filters: { season: 'test' }, selection: { ids: ['1'] }, data_version: 7 }, suggestions: [item] };
await assert.rejects(adapter.suggest(input), /未协商/);
emit({ ...ready, capabilities: ['assistant-open.v1'] });
assert.equal(adapter.supportsAssistant(), true);
assert.equal(adapter.supportsSuggestions(), false);
await assert.rejects(adapter.suggest(input), /未协商/);
for (const overrides of [{ origin: 'https://evil.test' }, { source: {} }]) emit(ready, overrides);
emit({ ...ready, launch_nonce: 'old' }); emit({ ...ready, application_slug: 'another' });
assert.equal(adapter.supportsSuggestions(), false);
emit(ready); assert.equal(adapter.supportsSuggestions(), true);

const invalidContexts = [null, [], { route: '//evil.test' }, { route: '/x\\y' }, { route: '/x\ny' },
  { route: 'https://evil.test/' }, { route: '/' + 'x'.repeat(1000) }, { entity_type: 'bad/key' },
  { entity_id: 123 }, { entity_id: 'x'.repeat(1001) }, { selection: ['1'] }, { filters: null },
  { entity_type: '' }, { entity_id: '' },
  { filters: { x: undefined } }, { filters: { x: Infinity } }, { data_version: NaN },
  { filters: { x: Array(201).fill('x') } }, { filters: { x: 'x'.repeat(4001) } },
  { filters: JSON.parse('{"__proto__":{"x":1}}') }, { filters: { a: { b: { c: { d: { e: { f: 'too deep' } } } } } } },
  { filters: new Date() }, { data_version: null }, { data_version: undefined }, { model: 'fake' }];
for (const context of invalidContexts) await assert.rejects(adapter.suggest({ ...input, context }), /无效/);
for (const override of [{ id: '' }, { id: 'x'.repeat(121) }, { revision: '../v2' }, { revision: 'x'.repeat(121) },
  { title: ' ' }, { title: 'x'.repeat(81) }, { summary: '' }, { summary: 'x'.repeat(401) },
  { goal: 'x'.repeat(2001) }, { goal: '' }, { url: 'https://evil.test' }, { autoSend: true },
  { approval: 'approved' }, { model: 'override' }]) {
  await assert.rejects(adapter.suggest({ ...input, suggestions: [{ ...item, ...override }] }), /无效/);
}
for (const suggestions of [null, {}, [item, item], [1], [item, item, item, item]]) {
  await assert.rejects(adapter.suggest({ ...input, suggestions }), /无效/);
}
await assert.rejects(adapter.suggest({ ...input, autoSend: true }), /无效/);
assert.equal(messages.length, 0);
// Valid per-field values may still exceed the whole UTF-8 envelope.
await assert.rejects(adapter.suggest({ ...input, suggestions: ['a', 'b', 'c'].map(id => ({ ...item, id, goal: '文'.repeat(2000) })) }), /16 KiB/);

const receipt = (request, status = 'accepted', code = 'received') => ({
  type: 'zhuojian:assistant-suggestions-result', ...identity, request_id: request.request_id,
  module_key: request.module_key, page_key: request.page_key, status, code,
});
let settled = false;
const task = adapter.suggest(input).then(result => { assert.equal(result.status, 'accepted'); settled = true; });
await assert.rejects(adapter.open({ moduleKey: 'm', pageKey: 'm.detail', goal: '检查' }), /重复/);
const request = messages.at(-1).data;
assert.equal(messages.at(-1).origin, origin);
assert.equal(request.type, 'zhuojian:assistant-suggestions');
assert.deepEqual(request.context, input.context);
assert.deepEqual(request.suggestions, [item]);
assert.deepEqual(Object.keys(request).sort(), ['type', 'version', 'application_slug', 'launch_nonce',
  'request_id', 'module_key', 'page_key', 'context', 'suggestions'].sort());
for (const override of [{ request_id: 'wrong-id' }, { page_key: 'other' }, { module_key: 'other' },
  { launch_nonce: 'old' }, { application_slug: 'other' }, { task_id: 'unexpected' },
  { status: 'draft_ready' }, { status: 'completed' }, { code: 'business_completed' },
  { status: 'rejected', code: 'invented_code' }]) emit({ ...receipt(request), ...override });
emit(receipt(request), { origin: 'https://evil.test' }); emit(receipt(request), { source: {} });
await Promise.resolve(); assert.equal(settled, false);
emit(receipt(request)); await task;
emit(receipt(request)); assert.equal(messages.length, 1); // No automatic open, Run, or business write.

const stale = adapter.suggest(input);
const staleRejected = assert.rejects(stale, /替换/);
const oldRequest = messages.at(-1).data;
let withdrawn = false;
const withdrawal = adapter.suggest({ ...input, suggestions: [] }).then(() => { withdrawn = true; });
await staleRejected;
emit(receipt(oldRequest)); await Promise.resolve(); assert.equal(withdrawn, false);
assert.deepEqual(messages.at(-1).data.suggestions, []);
emit(receipt(messages.at(-1).data)); await withdrawal;

const open = adapter.open({ moduleKey: 'm', pageKey: 'm.detail', goal: '检查' });
await assert.rejects(adapter.suggest(input), /重复/);
const opened = messages.at(-1).data;
emit({ ...identity, type: 'zhuojian:assistant-open-result', request_id: opened.request_id,
  module_key: 'm', page_key: 'm.detail', status: 'draft_ready' });
await open;

const clear = adapter.suggest({ moduleKey: 'm', pageKey: 'm.detail', context: {}, suggestions: [] });
assert.deepEqual(messages.at(-1).data.context, {});
assert.deepEqual(messages.at(-1).data.suggestions, []);
emit(receipt(messages.at(-1).data)); assert.equal((await clear).status, 'accepted');
const rejectionText = { page_context_changed: /已变化/, permission_denied: /没有获授权/,
  suggestions_unavailable: /暂时无法/, snapshot_replaced: /替换/, request_conflict: /冲突/,
  rate_limited: /频繁/, invalid_request: /格式无效/ };
for (const [code, matcher] of Object.entries(rejectionText)) {
  const rejected = adapter.suggest(input);
  emit(receipt(messages.at(-1).data, 'rejected', code));
  await assert.rejects(rejected, matcher);
}
// Different items can legitimately share the same evidence version.
const three = adapter.suggest({ ...input, suggestions: ['a', 'b', 'c'].map(id => ({ ...item, id })) });
emit(receipt(messages.at(-1).data)); await three;
const pending = adapter.suggest(input); adapter.dispose();
await assert.rejects(pending, /页面已离开/);
assert.equal(adapter.supportsSuggestions(), false); assert.equal(listeners.size, 0);

const timeoutAdapter = sandbox.factory({ ...config, timeoutMs: 10 }); emit(ready);
const beforeTimeout = messages.length;
await assert.rejects(timeoutAdapter.suggest(input), /未收到业务提示回执/);
assert.equal(messages.length, beforeTimeout + 1); timeoutAdapter.dispose();
window.parent = window;
const standalone = sandbox.factory(config); emit(ready);
assert.equal(standalone.supportsSuggestions(), false);
await assert.rejects(standalone.suggest(input), /未协商/); standalone.dispose();
console.log('PASS actual suggestions adapter: capability isolation, trusted identity, exact context/item bounds, UTF-8 envelope, strict receipts, withdrawal, no auto-run, timeout, disposal');
