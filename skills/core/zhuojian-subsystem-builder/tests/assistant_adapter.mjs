import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import vm from 'node:vm';
import { webcrypto } from 'node:crypto';

const source = await readFile(process.argv[2], 'utf8');
const messages = [], listeners = new Set();
const parent = { postMessage: (data, origin) => messages.push({ data, origin }) };
const window = { parent, addEventListener: (_, fn) => listeners.add(fn), removeEventListener: (_, fn) => listeners.delete(fn) };
const context = { window, URL, crypto: webcrypto, setTimeout, clearTimeout };
vm.runInNewContext(source.replace('export function', 'function') + '\nthis.factory = createAssistant;', context);
const origin = 'https://platform.test';
const identity = { version: 1, application_slug: 'sample', launch_nonce: 'nonce' };
const emit = (data, overrides = {}) => { for (const fn of listeners) fn({ source: parent, origin, data: { ...identity, ...data }, ...overrides }); };
const config = { applicationSlug: 'sample', launchNonce: 'nonce', platformOrigin: origin, timeoutMs: 50 };
for (const platformOrigin of ['http://evil.test', 'https://user:password@platform.test', 'https://platform.test/path', 'https://platform.test?token=secret', 'file:///tmp']) {
  assert.throws(() => context.factory({ ...config, platformOrigin }));
}
const adapter = context.factory(config);
const input = { moduleKey: 'm', pageKey: 'm.main', goal: '帮我检查当前记录的缺项' };
await assert.rejects(adapter.open(input), /未协商/);
const ready = { type: 'zhuojian:host-ready', capabilities: ['assistant-open.v1'] };
emit(ready, { origin: 'https://evil.test' }); assert.equal(adapter.supportsAssistant(), false);
emit(ready, { source: {} }); assert.equal(adapter.supportsAssistant(), false);
emit({ ...ready, launch_nonce: 'old' }); assert.equal(adapter.supportsAssistant(), false);
emit(ready); assert.equal(adapter.supportsAssistant(), true);
for (const override of [{ goal: '' }, { goal: ' ' }, { goal: 'x'.repeat(2001) }, { moduleKey: '../admin' }, { pageKey: 'x'.repeat(161) }]) {
  await assert.rejects(adapter.open({ ...input, ...override }), /无效/);
}
let finished = false;
const task = adapter.open(input).then(result => { assert.equal(result.status, 'draft_ready'); finished = true; });
await assert.rejects(adapter.open(input), /重复/);
assert.equal(messages.length, 1);
assert.equal(messages[0].origin, origin);
assert.deepEqual(Object.keys(messages[0].data).sort(), ['type', 'version', 'application_slug', 'launch_nonce', 'request_id', 'module_key', 'page_key', 'goal'].sort());
const { goal, ...request } = messages[0].data;
const result = { ...request, type: 'zhuojian:assistant-open-result', status: 'draft_ready' };
emit({ ...result, task_id: 'must-not-be-returned' });
emit({ ...result, page_key: 'other' });
emit({ ...result, launch_nonce: 'old' });
emit({ ...result, status: 'completed' }); // no false business completion
await Promise.resolve(); assert.equal(finished, false);
emit(result); await task;
emit(result); assert.equal(messages.length, 1); // replay never sends/executes anything
const rejected = adapter.open(input);
const { goal: ignoredGoal, ...next } = messages.at(-1).data;
emit({ ...next, type: result.type, status: 'rejected', code: 'draft_conflict' });
await assert.rejects(rejected, /已有草稿/);
await assert.rejects(adapter.open(input), /未收到交接回执/);
const pending = adapter.open(input); adapter.dispose();
await assert.rejects(pending, /页面已离开/);
assert.equal(listeners.size, 0); assert.equal(adapter.supportsAssistant(), false);
console.log('PASS assistant capability negotiation, origin/source/nonce, bounds, draft-only receipt, conflict, timeout, disposal');
