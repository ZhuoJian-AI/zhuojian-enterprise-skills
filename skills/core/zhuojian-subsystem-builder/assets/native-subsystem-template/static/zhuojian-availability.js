/* Standalone-only status. The SaaS host owns embedded availability UX. */
(() => {
  if (window.parent !== window || !/^https?:$/.test(location.protocol)) return;
  let lastState = 'healthy';
  let dismissed = null;
  let recoveredTimer = null;
  let checking = false;
  let banner = null;

  function hide() {
    banner?.remove();
    banner = null;
  }

  function show(state) {
    if (state === 'healthy') {
      if (lastState !== 'healthy') show('recovered');
      else hide();
      lastState = 'healthy';
      return;
    }
    if (state !== 'recovered') lastState = state;
    if (dismissed === state) return;
    window.clearTimeout(recoveredTimer);
    hide();
    banner = document.createElement('div');
    banner.className = 'zj-availability';
    banner.dataset.kind = state;
    banner.setAttribute('role', 'status');
    const message = document.createElement('span');
    message.className = 'zj-availability__message';
    message.textContent = state === 'maintenance'
      ? '当前业务系统正在维护，其他平台功能仍可使用。请勿重复提交。'
      : state === 'unavailable'
        ? '当前业务系统暂不可用。已填写的内容不会自动清除或重交。'
        : '当前业务系统已恢复，可以继续使用。';
    banner.append(message);
    if (state !== 'recovered') {
      const retry = document.createElement('button');
      retry.type = 'button';
      retry.textContent = '检测恢复';
      retry.addEventListener('click', () => { void check(); });
      banner.append(retry);
    }
    const close = document.createElement('button');
    close.type = 'button';
    close.setAttribute('aria-label', '关闭状态提示');
    close.textContent = '×';
    close.addEventListener('click', () => { dismissed = state; hide(); });
    banner.append(close);
    document.body.append(banner);
    if (state === 'recovered') recoveredTimer = window.setTimeout(hide, 5_000);
  }

  async function check() {
    if (checking) return;
    checking = true;
    try {
      const response = await fetch('/health', { cache: 'no-store', signal: AbortSignal.timeout(4_000) });
      if (response.ok) { dismissed = null; show('healthy'); return; }
      if (response.status === 503 && response.headers.get('Retry-After')?.match(/^[1-9][0-9]*$/)) {
        const body = await response.json().catch(() => null);
        if (body && body.code === 'SUBSYSTEM_MAINTENANCE') { show('maintenance'); return; }
      }
      show('unavailable');
    } catch {
      show('unavailable');
    } finally {
      checking = false;
    }
  }

  window.addEventListener('DOMContentLoaded', () => {
    void check();
    window.setInterval(() => { if (!document.hidden) void check(); }, 15_000);
    document.addEventListener('visibilitychange', () => { if (!document.hidden) void check(); });
  });
})();
