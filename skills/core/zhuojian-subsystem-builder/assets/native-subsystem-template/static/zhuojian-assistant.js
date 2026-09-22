// Optional cross-origin draft handoff. Never sends a message to a model or executes an Action.
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
  const errors = {
    assistant_busy: '助手正在处理任务，请完成或取消后再试',
    draft_conflict: '助手中已有草稿或附件，请先处理，原内容已保留',
    page_context_changed: '业务页面或对象已变化，请从当前对象重新发起',
    permission_denied: '当前页面没有获授权的业务 AI 能力，请联系企业管理员',
    entry_unavailable: '平台暂时无法核对入口，请稍后重试',
    request_conflict: '请求标识冲突，请检查当前助手草稿',
    rate_limited: '请求过于频繁，请稍后重试',
  };
  let supported = false, disposed = false, pending = null;
  const finish = (error) => {
    const request = pending;
    if (!request) return;
    pending = null;
    clearTimeout(request.timer);
    if (error) request.reject(error);
    else request.resolve({ status: 'draft_ready' });
  };
  const receive = event => {
    if (disposed || event.source !== window.parent || event.origin !== origin) return;
    const data = event.data;
    if (!data || typeof data !== 'object' || Array.isArray(data) || data.version !== 1
      || data.application_slug !== applicationSlug || data.launch_nonce !== launchNonce) return;
    if (data.type === 'zhuojian:host-ready') {
      supported = Array.isArray(data.capabilities) && data.capabilities.includes('assistant-open.v1');
      return;
    }
    if (!pending || data.type !== 'zhuojian:assistant-open-result'
      || Object.keys(data).some(name => !allowedResultKeys.has(name))
      || data.request_id !== pending.requestId || data.module_key !== pending.moduleKey
      || data.page_key !== pending.pageKey) return;
    if (data.status === 'draft_ready') finish();
    else if (data.status === 'rejected' && typeof data.code === 'string' && data.code.length <= 80) {
      finish(new Error(Object.hasOwn(errors, data.code) ? errors[data.code] : '未能交给助手，原有对话和业务页面已保留'));
    }
  };
  window.addEventListener('message', receive);
  return {
    supportsAssistant: () => !disposed && supported && window.parent !== window,
    open({ moduleKey, pageKey, goal }) {
      if (disposed || window.parent === window || !supported) return Promise.reject(new Error('请从支持业务助手的 SaaS 页面打开；当前页面未协商此能力'));
      if (pending) return Promise.reject(new Error('正在交给助手，请勿重复点击'));
      if (typeof moduleKey !== 'string' || moduleKey.length > 120 || !key.test(moduleKey)
        || typeof pageKey !== 'string' || pageKey.length > 160 || !key.test(pageKey)
        || typeof goal !== 'string' || !goal.trim() || goal.length > 2000) return Promise.reject(new Error('业务目标或页面标识无效'));
      const requestId = crypto.randomUUID();
      return new Promise((resolve, reject) => {
        const timer = setTimeout(() => finish(new Error('未收到交接回执，请先检查助手中的草稿；不会自动重试或执行')), timeoutMs);
        pending = { requestId, moduleKey, pageKey, timer, resolve, reject };
        try {
          window.parent.postMessage({ type: 'zhuojian:assistant-open', version: 1,
            application_slug: applicationSlug, launch_nonce: launchNonce, request_id: requestId,
            module_key: moduleKey, page_key: pageKey, goal: goal.trim() }, origin);
        } catch { finish(new Error('无法发送交接请求，业务操作未执行')); }
      });
    },
    dispose() {
      disposed = true;
      supported = false;
      window.removeEventListener('message', receive);
      finish(new Error('页面已离开；请检查已有助手草稿，不会自动执行'));
    },
  };
}
