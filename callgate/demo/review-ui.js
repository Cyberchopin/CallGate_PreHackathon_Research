'use strict';
const el = id => document.getElementById(id);
const role = document.querySelector('main').dataset.role;
const key = 'callgate-' + role;
const fragment = new URLSearchParams(location.hash.slice(1)).get('token');
if (fragment) {
  sessionStorage.setItem(key, fragment);
  history.replaceState(null, '', location.pathname);
}
const token = sessionStorage.getItem(key);
const stateNames = {UNVERIFIED:'继续听，身份尚未核实', CHALLENGED:'先核验，再操作',
  COOLING_OFF:'暂停操作，独立核验', BLOCKED:'不要分享敏感信息'};
const outcomeText = result => result.status === 'simulated_action_completed'
  ? '仅本次模拟操作已完成。没有发生真实转账。'
  : result.status === 'reviewer_denied' ? '核验者已拒绝，模拟操作未执行。' : '尚无完成结果。';
async function api(path, body) {
  if (!token) throw new Error('缺少入口凭据，请使用启动程序显示的完整链接。');
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 8000);
  let response;
  try {
    response = await fetch(path, {method:body === undefined ? 'GET' : 'POST',
      headers:{Authorization:'Bearer ' + token, 'Content-Type':'application/json'},
      ...(body === undefined ? {} : {body:JSON.stringify(body)}), cache:'no-store', signal:controller.signal});
  } catch (_) {
    throw new Error('服务未连接或响应超时。结果尚未确认，请刷新结果；系统不会自动重试批准。');
  } finally { clearTimeout(timer); }
  if (!response.ok) {
    if (response.status === 401) throw new Error('此入口凭据无效。请检查是否打开了正确角色的链接。');
    if (response.status === 409) throw new Error('当前状态不允许操作，或请求已经变化、过期、使用。请刷新核对。');
    if (response.status === 422) throw new Error('请检查目标、金额或台词格式。');
    throw new Error('确认服务不可用或结果未确认。请刷新查看，系统不会自动重试批准。');
  }
  return response.json();
}
function action(id, fn) {
  el(id).onclick = async () => {
    el(id).disabled = true;
    try { await fn(); } catch (error) { el('status').textContent = error.message; }
    finally { el(id).disabled = false; }
  };
}
if (role === 'participant') {
  action('ingest', async () => {
    const result = await api('/api/transcript', {segment_id:'s' + crypto.randomUUID(),
      text:el('transcript').value, start_ms:0, end_ms:1000, final:true});
    el('risk').textContent = stateNames[result.state] + ' · 风险参考分 ' + result.score + '/100';
    el('status').textContent = '通话内容已更新。先前的待确认请求已失效。';
  });
  action('request', async () => {
    await api('/api/request', {destination:el('destination').value, amount_cents:Number(el('amount').value)});
    el('status').textContent = '等待核验者在单独页面读取并确认。当前未执行操作。';
  });
  action('refresh', async () => {
    const result = await api('/api/status');
    el('status').textContent = result.outcome ? outcomeText(result.outcome) : result.pending
      ? '仍等待核验，未执行操作；过期请求需要重新提交。' : '没有当前确认请求，未执行操作。';
  });
} else {
  let pending = null;
  let busy = false;
  const disable = () => { el('approve').disabled = busy || !pending; el('deny').disabled = busy || !pending; };
  action('refresh', async () => {
    pending = null; disable();
    el('operation').textContent = '正在读取…'; el('expiry').textContent = '';
    const bundle = await api('/api/pending');
    if (!bundle) { el('operation').textContent = '没有待确认请求。'; return; }
    pending = bundle.request;
    el('operation').textContent = '目标：' + bundle.operation.destination + '\n金额：' +
      (bundle.operation.amount_cents / 100).toFixed(2) + ' USD\n会话：' + pending.session_id;
    el('expiry').textContent = '有效至：' + new Date(pending.expires_at * 1000).toLocaleTimeString();
    el('status').textContent = '核对金额和目标后，再明确选择。';
    disable();
  });
  for (const [id, approved] of [['approve', true], ['deny', false]]) {
    el(id).onclick = async () => {
      if (!pending || busy) return;
      busy = true; disable();
      try {
        const result = await api('/api/decide', {request_id:pending.request_id, approved});
        el('status').textContent = outcomeText(result);
      } catch (error) { el('status').textContent = error.message; }
      finally { pending = null; busy = false; disable(); }
    };
  }
}
if (token) el('status').textContent = '入口已就绪。请按页面步骤继续。';
