// Public bridge adapter. No host DOM, internal SaaS route, credentials or arbitrary URLs.
export function createNavigation({ applicationSlug, launchNonce, platformOrigin, entryUrl, isDirty = () => false,
  timeoutMs = 30000, onFailure = () => {}, onAccepted = () => {} }) {
  const origin = new URL(platformOrigin).origin;
  if (new URL(origin).protocol !== 'https:' && !['localhost', '127.0.0.1'].includes(new URL(origin).hostname)) {
    throw new Error('Invalid trusted platform origin');
  }
  const key = /^[a-zA-Z0-9][a-zA-Z0-9._:-]{0,255}$/;
  const pending = new Map();
  const errors = { permission_denied: '当前账号没有目标页面权限，请联系企业管理员',
    target_unavailable: '目标模块或页面不存在或不可访问', unsupported: '目标不支持平台内嵌导航',
    platform_unavailable: '平台暂时不可用，请保留当前页面稍后重试', target_timeout: '目标页面加载超时，原页面已保留',
    leave_timeout: '离开检查超时，原页面已保留', cancelled: '已取消切换，草稿保留',
    stale_navigation: '页面已变化，旧请求已取消', rate_limited: '请求过于频繁，请稍后重试', navigation_busy: '正在切换页面，请勿重复操作' };
  let supported = false;
  let disposed = false;
  const post = data => window.parent.postMessage({ ...data, version: 1,
    application_slug: applicationSlug, launch_nonce: launchNonce }, origin);
  const receive = event => {
    if (disposed || event.source !== window.parent || event.origin !== origin) return;
    const data = event.data;
    if (!data || data.version !== 1 || data.application_slug !== applicationSlug || data.launch_nonce !== launchNonce) return;
    if (data.type === 'zhuojian:host-ready') {
      supported = Array.isArray(data.capabilities) && data.capabilities.includes('navigation.v1');
    } else if (data.type === 'zhuojian:prepare-leave' && typeof data.request_id === 'string' && key.test(data.request_id)) {
      // A failing or async dirty check must never imply that the page is clean.
      let dirty = true;
      try { dirty = isDirty() !== false; } catch { /* preserve the page */ }
      post({ type: 'zhuojian:leave-result', request_id: data.request_id, dirty });
    } else if (data.type === 'zhuojian:navigate-result') {
      const request = pending.get(data.request_id);
      if (!request || request.moduleKey !== data.module_key || request.pageKey !== data.page_key) return;
      if (data.status === 'pending') return;
      if (data.status === 'accepted') { onAccepted(); return; }
      if (!['completed', 'failed', 'rejected'].includes(data.status)) return;
      clearTimeout(request.timer); pending.delete(data.request_id);
      if (data.status === 'completed') request.resolve({ status: 'completed' });
      else { const error = new Error(errors[data.error] || '导航失败，原页面已保留'); request.reject(error); onFailure(error); }
    }
  };
  window.addEventListener('message', receive);
  return {
    supportsNavigation: () => supported,
    navigate(moduleKey, pageKey) {
      if (disposed || typeof moduleKey !== 'string' || typeof pageKey !== 'string'
        || moduleKey.length > 120 || pageKey.length > 160 || !key.test(moduleKey) || !key.test(pageKey)) return Promise.reject(new Error('目标页面标识无效'));
      if (window.parent === window) {
        if (isDirty() && !window.confirm('放弃未保存内容并切换？取消将保留当前页面。')) return Promise.reject(new Error('已取消切换'));
        if (!entryUrl) return Promise.reject(new Error('平台未提供独立导航入口，请从平台打开目标模块'));
        const url = new URL(entryUrl);
        if (url.origin !== origin) return Promise.reject(new Error('平台入口来源不匹配'));
        url.searchParams.set('module', moduleKey); url.searchParams.set('page', pageKey);
        window.location.assign(url.href);
        return Promise.resolve({ status: 'accepted' });
      }
      if (!supported) return Promise.reject(new Error('平台尚未声明导航能力，请使用已有平台导航或联系平台维护人员'));
      if (pending.size) return Promise.reject(new Error('正在切换页面，请勿重复点击'));
      const requestId = crypto.randomUUID();
      return new Promise((resolve, reject) => {
        const timer = setTimeout(() => { pending.delete(requestId); const error = new Error('导航超时，请检查当前页面后重试'); reject(error); onFailure(error); }, timeoutMs);
        pending.set(requestId, { resolve, reject, timer, moduleKey, pageKey });
        post({ type: 'zhuojian:navigate', request_id: requestId, module_key: moduleKey, page_key: pageKey });
      });
    },
    dispose() {
      disposed = true; window.removeEventListener('message', receive);
      for (const request of pending.values()) { clearTimeout(request.timer); request.reject(new Error('页面已离开')); }
      pending.clear();
    },
  };
}
