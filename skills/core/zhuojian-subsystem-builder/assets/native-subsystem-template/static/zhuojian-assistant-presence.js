// Child-owned assistant presence adapter. The host sends only registered semantic keys;
// it never receives selectors, coordinates, DOM nodes, credentials or arbitrary CSS.
export function createAssistantPresence({
  applicationSlug,
  launchNonce,
  platformOrigin,
  moduleKey,
  pageKey,
  anchorKeys,
  durationMs = 6000,
}) {
  const origin = new URL(platformOrigin).origin;
  const parsedOrigin = new URL(origin);
  if (parsedOrigin.protocol !== 'https:' && !['localhost', '127.0.0.1'].includes(parsedOrigin.hostname)) {
    throw new Error('Invalid trusted platform origin');
  }
  const keyPattern = /^[a-zA-Z0-9][a-zA-Z0-9._:-]{0,255}$/;
  const phases = new Set(['navigating', 'acting', 'verifying', 'completed', 'failed']);
  const configuredAnchors = [...new Set(Array.isArray(anchorKeys) ? anchorKeys : [])]
    .filter(key => typeof key === 'string' && keyPattern.test(key))
    .slice(0, 100);
  if (!keyPattern.test(applicationSlug) || !keyPattern.test(launchNonce)
    || !keyPattern.test(moduleKey) || !keyPattern.test(pageKey) || !configuredAnchors.length) {
    throw new Error('Invalid assistant presence identity or anchors');
  }

  let disposed = false;
  let supported = false;
  let activeElement = null;
  let hideTimer = 0;
  let overlay = null;
  let cursor = null;
  let label = null;

  const post = data => window.parent.postMessage({
    ...data,
    version: 1,
    application_slug: applicationSlug,
    launch_nonce: launchNonce,
    module_key: moduleKey,
    page_key: pageKey,
  }, origin);

  const registeredElement = anchorKey => Array.from(
    document.querySelectorAll('[data-zhuojian-anchor]'),
  ).find(element => element.getAttribute('data-zhuojian-anchor') === anchorKey) || null;

  const availableAnchors = () => configuredAnchors.filter(anchorKey => registeredElement(anchorKey));

  const ensureOverlay = () => {
    if (overlay) return;
    overlay = document.createElement('div');
    overlay.dataset.zhuojianAssistantPresence = 'true';
    overlay.setAttribute('aria-hidden', 'true');
    Object.assign(overlay.style, {
      position: 'fixed', pointerEvents: 'none', zIndex: '2147483600', display: 'none',
      border: '2px solid var(--zhuojian-ai-presence-color, #635bff)', borderRadius: '12px',
      boxShadow: '0 0 0 5px color-mix(in srgb, var(--zhuojian-ai-presence-color, #635bff) 16%, transparent)',
      transition: 'top 180ms ease, left 180ms ease, width 180ms ease, height 180ms ease, opacity 180ms ease',
    });
    cursor = document.createElement('div');
    cursor.textContent = 'AI';
    Object.assign(cursor.style, {
      position: 'absolute', right: '8px', top: '8px', display: 'grid', placeItems: 'center',
      width: '32px', height: '32px', borderRadius: '999px', color: '#fff', font: '700 12px/1 system-ui',
      background: 'var(--zhuojian-ai-presence-color, #635bff)',
      boxShadow: '0 8px 22px rgba(15, 23, 42, .22)',
    });
    label = document.createElement('span');
    Object.assign(label.style, {
      position: 'fixed', left: 'max(12px, env(safe-area-inset-left))',
      bottom: 'max(12px, env(safe-area-inset-bottom))', maxWidth: 'calc(100vw - 24px)',
      overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', padding: '6px 9px',
      borderRadius: '8px', color: '#fff', background: 'rgba(15, 23, 42, .88)',
      font: '600 12px/1.35 system-ui', boxShadow: '0 8px 22px rgba(15, 23, 42, .16)',
    });
    overlay.append(cursor, label);
    document.body.append(overlay);
  };

  const positionOverlay = () => {
    if (!overlay || !activeElement || !activeElement.isConnected) return;
    const rect = activeElement.getBoundingClientRect();
    const inset = 5;
    const viewportWidth = Math.max(1, window.innerWidth);
    const viewportHeight = Math.max(1, window.innerHeight);
    const left = Math.min(Math.max(2, rect.left - inset), Math.max(2, viewportWidth - 30));
    const top = Math.min(Math.max(2, rect.top - inset), Math.max(2, viewportHeight - 30));
    const availableWidth = Math.max(1, viewportWidth - left - 2);
    const availableHeight = Math.max(1, viewportHeight - top - 2);
    Object.assign(overlay.style, {
      top: `${top}px`,
      left: `${left}px`,
      width: `${Math.min(Math.max(28, rect.width + inset * 2), availableWidth)}px`,
      height: `${Math.min(Math.max(28, rect.height + inset * 2), availableHeight)}px`,
    });
  };

  const hide = () => {
    if (hideTimer) window.clearTimeout(hideTimer);
    hideTimer = 0;
    activeElement = null;
    if (overlay) overlay.style.display = 'none';
  };

  const show = (element, text, phase) => {
    ensureOverlay();
    activeElement = element;
    label.textContent = text;
    cursor.textContent = phase === 'completed' ? '✓' : phase === 'failed' ? '!' : 'AI';
    overlay.style.opacity = phase === 'completed' ? '.76' : '1';
    const rect = element.getBoundingClientRect();
    const outside = rect.bottom < 0 || rect.top > window.innerHeight || rect.right < 0 || rect.left > window.innerWidth;
    if (outside) element.scrollIntoView({
      block: 'center', inline: 'nearest',
      behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth',
    });
    overlay.style.display = 'block';
    positionOverlay();
    if (hideTimer) window.clearTimeout(hideTimer);
    hideTimer = window.setTimeout(hide, Math.max(1500, Math.min(Number(durationMs) || 6000, 15000)));
  };

  const respond = (request, status) => post({
    type: 'zhuojian:assistant-presence-result',
    request_id: request.request_id,
    anchor_key: request.anchor_key,
    status,
  });

  const receive = event => {
    if (disposed || event.source !== window.parent || event.origin !== origin) return;
    const data = event.data;
    if (!data || typeof data !== 'object' || Array.isArray(data)
      || data.version !== 1 || data.application_slug !== applicationSlug || data.launch_nonce !== launchNonce) return;
    if (data.type === 'zhuojian:host-ready') {
      supported = Array.isArray(data.capabilities) && data.capabilities.includes('assistant-presence.v1');
      if (supported) post({
        type: 'zhuojian:assistant-presence-ready',
        anchor_keys: availableAnchors(),
      });
      return;
    }
    if (data.type !== 'zhuojian:assistant-presence' || !supported) return;
    const allowedKeys = new Set([
      'type', 'version', 'application_slug', 'launch_nonce', 'request_id',
      'module_key', 'page_key', 'anchor_key', 'phase', 'label',
    ]);
    if (Object.keys(data).some(key => !allowedKeys.has(key))
      || data.module_key !== moduleKey || data.page_key !== pageKey
      || typeof data.request_id !== 'string' || !keyPattern.test(data.request_id)
      || typeof data.anchor_key !== 'string' || !configuredAnchors.includes(data.anchor_key)
      || typeof data.phase !== 'string' || !phases.has(data.phase)
      || typeof data.label !== 'string' || !data.label.trim() || data.label.length > 160) return;
    const element = registeredElement(data.anchor_key);
    if (!element) {
      respond(data, 'missing');
      return;
    }
    show(element, data.label.trim(), data.phase);
    respond(data, 'shown');
  };

  window.addEventListener('message', receive);
  window.addEventListener('scroll', positionOverlay, true);
  window.addEventListener('resize', positionOverlay);
  return {
    supportsAssistantPresence: () => supported,
    availableAnchors,
    dispose() {
      disposed = true;
      hide();
      window.removeEventListener('message', receive);
      window.removeEventListener('scroll', positionOverlay, true);
      window.removeEventListener('resize', positionOverlay);
      overlay?.remove();
      overlay = null;
    },
  };
}
