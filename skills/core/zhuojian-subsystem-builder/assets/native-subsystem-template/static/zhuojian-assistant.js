// Optional cross-origin suggestions and draft handoff. Never invokes a model or an Action.
export function createAssistant({ applicationSlug, launchNonce, platformOrigin, timeoutMs = 10000 }) {
  const url = new URL(platformOrigin);
  if (url.username || url.password || url.search || url.hash || url.pathname !== '/'
    || (url.protocol !== 'https:' && !(url.protocol === 'http:' && ['localhost', '127.0.0.1'].includes(url.hostname)))) {
    throw new Error('Invalid trusted platform origin');
  }
  const origin = url.origin;
  const key = /^[a-zA-Z0-9][a-zA-Z0-9._:-]{0,255}$/;
  if (!key.test(applicationSlug || '') || !key.test(launchNonce || '')
    || !Number.isFinite(timeoutMs) || timeoutMs < 1 || timeoutMs > 30000) throw new Error('Invalid assistant bridge configuration');
  const allowedResultKeys = new Set(['type', 'version', 'application_slug', 'launch_nonce',
    'request_id', 'module_key', 'page_key', 'status', 'code']);
  const contextKeys = new Set(['route', 'entity_type', 'entity_id', 'filters', 'selection', 'data_version']);
  const suggestionKeys = new Set(['id', 'revision', 'title', 'summary', 'goal']);
  const record = value => {
    if (!value || typeof value !== 'object' || Array.isArray(value)) return false;
    const prototype = Object.getPrototypeOf(value);
    return prototype === null || Object.getPrototypeOf(prototype) === null;
  };
  const safeValue = (value, depth = 0) => {
    if (depth > 5) return false;
    if (value === null || typeof value === 'boolean') return true;
    if (typeof value === 'number') return Number.isFinite(value);
    if (typeof value === 'string') return value.length <= 4000;
    if (Array.isArray(value)) return value.length <= 200 && value.every(item => safeValue(item, depth + 1));
    return record(value) && Object.keys(value).length <= 200
      && Object.entries(value).every(([name, item]) => name.length > 0 && name.length <= 128
        && !['__proto__', 'prototype', 'constructor'].includes(name) && safeValue(item, depth + 1));
  };
  const validContext = value => record(value) && Object.keys(value).every(name => contextKeys.has(name))
    && Object.entries(value).every(([name, item]) => {
      if (name === 'filters' || name === 'selection') return record(item) && safeValue(item);
      if (name === 'data_version') return (typeof item === 'string' && item.length <= 1000)
        || (typeof item === 'number' && Number.isFinite(item));
      if (typeof item !== 'string' || item.length > 1000) return false;
      if (name === 'route') return item.startsWith('/') && !item.startsWith('//')
        && !item.includes('\\') && !/[\u0000-\u001f\u007f]/.test(item);
      return !!item && (name !== 'entity_type' || key.test(item));
    });
  const text = (value, max) => typeof value === 'string' && !!value.trim() && value.length <= max;
  const safeKey = value => typeof value === 'string' && value.length <= 120 && key.test(value);
  const validSuggestions = value => Array.isArray(value) && value.length <= 3
    && value.every(item => record(item) && Object.keys(item).every(name => suggestionKeys.has(name))
      && safeKey(item.id) && safeKey(item.revision) && text(item.title, 80)
      && text(item.summary, 400) && text(item.goal, 2000))
    && new Set(value.map(item => item.id)).size === value.length;
  const errors = {
    assistant_busy: '助手正在处理任务，请完成或取消后再试',
    draft_conflict: '助手中已有草稿或附件，请先处理，原内容已保留',
    page_context_changed: '业务页面或对象已变化，请从当前对象重新发起',
    permission_denied: '当前页面没有获授权的业务 AI 能力，请联系企业管理员',
    entry_unavailable: '平台暂时无法核对入口，请稍后重试',
    request_conflict: '请求标识冲突，请检查当前助手草稿',
    rate_limited: '请求过于频繁，请稍后重试',
    invalid_request: '业务提示格式无效，请保留原页面并检查接入',
    unsupported: '当前平台尚不支持业务提示，请使用原业务页面',
    suggestions_unavailable: '平台暂时无法核对业务提示，请保留人工操作',
    snapshot_replaced: '业务提示已被新的检查结果替换，请查看当前页面',
  };
  const suggestionRejectCodes = new Set(['page_context_changed', 'permission_denied', 'suggestions_unavailable',
    'snapshot_replaced', 'request_conflict', 'rate_limited', 'invalid_request']);
  let supported = false, suggestionsSupported = false, disposed = false, pending = null;
  const finish = (error) => {
    const request = pending;
    if (!request) return;
    pending = null;
    clearTimeout(request.timer);
    if (error) request.reject(error);
    else request.resolve({ status: request.successStatus });
  };
  const receive = event => {
    if (disposed || event.source !== window.parent || event.origin !== origin) return;
    const data = event.data;
    if (!data || typeof data !== 'object' || Array.isArray(data) || data.version !== 1
      || data.application_slug !== applicationSlug || data.launch_nonce !== launchNonce) return;
    if (data.type === 'zhuojian:host-ready') {
      supported = Array.isArray(data.capabilities) && data.capabilities.includes('assistant-open.v1');
      suggestionsSupported = Array.isArray(data.capabilities) && data.capabilities.includes('assistant-suggestions.v1');
      return;
    }
    if (!pending || data.type !== pending.resultType
      || Object.keys(data).some(name => !allowedResultKeys.has(name))
      || data.request_id !== pending.requestId || data.module_key !== pending.moduleKey
      || data.page_key !== pending.pageKey) return;
    if (pending.successStatus === 'accepted' && ((data.status === 'accepted' && data.code !== 'received')
      || (data.status === 'rejected' && !suggestionRejectCodes.has(data.code)))) return;
    if (data.status === pending.successStatus) finish();
    else if (data.status === 'rejected' && typeof data.code === 'string' && data.code.length <= 80) {
      finish(new Error(Object.hasOwn(errors, data.code) ? errors[data.code] : '未能交给助手，原有对话和业务页面已保留'));
    }
  };
  window.addEventListener('message', receive);
  const dispatch = ({ moduleKey, pageKey, fields, type, successStatus, timeoutMessage }) => {
    const requestId = crypto.randomUUID();
    const message = { type, version: 1, application_slug: applicationSlug, launch_nonce: launchNonce,
      request_id: requestId, module_key: moduleKey, page_key: pageKey, ...fields };
    try {
      if (new TextEncoder().encode(JSON.stringify(message)).byteLength > 16 * 1024) {
        return Promise.reject(new Error('业务目标或提示超过 16 KiB，请只保留当前对象的必要引用'));
      }
    } catch { return Promise.reject(new Error('业务目标或提示不是有效 JSON')); }
    // A valid withdrawal/new snapshot need not wait behind a stale snapshot's preflight.
    if (type === 'zhuojian:assistant-suggestions' && pending) finish(new Error(errors.snapshot_replaced));
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => finish(new Error(timeoutMessage)), timeoutMs);
      pending = { requestId, moduleKey, pageKey, timer, resolve, reject,
        resultType: `${type}-result`, successStatus };
      try { window.parent.postMessage(message, origin); }
      catch { finish(new Error('无法发送交接请求，业务操作未执行')); }
    });
  };
  const validPage = (moduleKey, pageKey) => typeof moduleKey === 'string' && moduleKey.length <= 120 && key.test(moduleKey)
    && typeof pageKey === 'string' && pageKey.length <= 160 && key.test(pageKey);
  return {
    supportsAssistant: () => !disposed && supported && window.parent !== window,
    supportsSuggestions: () => !disposed && suggestionsSupported && window.parent !== window,
    open({ moduleKey, pageKey, goal }) {
      if (disposed || window.parent === window || !supported) return Promise.reject(new Error('请从支持业务助手的 SaaS 页面打开；当前页面未协商此能力'));
      if (pending) return Promise.reject(new Error('正在交给助手，请勿重复点击'));
      if (!validPage(moduleKey, pageKey) || !text(goal, 2000)) return Promise.reject(new Error('业务目标或页面标识无效'));
      return dispatch({ moduleKey, pageKey, fields: { goal: goal.trim() }, type: 'zhuojian:assistant-open',
        successStatus: 'draft_ready', timeoutMessage: '未收到交接回执，请先检查助手中的草稿；不会自动重试或执行' });
    },
    suggest(input) {
      if (disposed || window.parent === window || !suggestionsSupported) return Promise.reject(new Error('当前平台未协商业务提示能力，请保留本地业务提示和人工操作'));
      if (pending && pending.successStatus !== 'accepted') return Promise.reject(new Error('正在交给助手，请勿重复发送'));
      if (!record(input) || Object.keys(input).some(name => !['moduleKey', 'pageKey', 'context', 'suggestions'].includes(name))
        || !validPage(input.moduleKey, input.pageKey) || !validContext(input.context)
        || !validSuggestions(input.suggestions)) return Promise.reject(new Error('业务提示或页面上下文无效'));
      return dispatch({ moduleKey: input.moduleKey, pageKey: input.pageKey,
        fields: { context: input.context, suggestions: input.suggestions }, type: 'zhuojian:assistant-suggestions',
        successStatus: 'accepted', timeoutMessage: '未收到业务提示回执；不会自动重试、启动助手或执行业务',
      });
    },
    dispose() {
      disposed = true;
      supported = false;
      suggestionsSupported = false;
      window.removeEventListener('message', receive);
      finish(new Error('页面已离开；请检查已有助手草稿，不会自动执行'));
    },
  };
}
