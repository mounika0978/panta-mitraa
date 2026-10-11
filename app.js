async function post(url, payload, multipart = false) {
  const options = { method: 'POST', body: multipart ? payload : JSON.stringify(payload) };
  if (!multipart) options.headers = { 'Content-Type': 'application/json' };
  const response = await fetch(url, options), data = await response.json();
  if (!response.ok) throw new Error(data.detail || 'సమస్య ఏర్పడింది.');
  return data;
}
function values(form) { return Object.fromEntries(new FormData(form).entries()); }
document.querySelector('#advisory-form').addEventListener('submit', async event => {
  event.preventDefault(); const data = values(event.currentTarget);
  ['rain_last_7_days_mm', 'forecast_rain_next_5_days_mm', 'days_without_rain'].forEach(k => data[k] = Number(data[k]));
  const result = document.querySelector('#result'); result.hidden = false; result.textContent = 'లోడ్ అవుతోంది…';
  try { const a = await post('/api/advisory', data); result.className = `risk ${a.risk}`; result.innerHTML = `<span class="pill">${a.risk.toUpperCase()} RISK</span><h3>${a.title_te}</h3><p>${a.message_te}</p><ul>${a.actions_te.map(x => `<li>${x}</li>`).join('')}</ul><small>${a.disclaimer_te}<br>${a.source}</small>`; } catch (e) { result.textContent = e.message; }
});
document.querySelector('#photo-form').addEventListener('submit', async event => { event.preventDefault(); const out = document.querySelector('#photo-result'); try { out.textContent = (await post('/api/photo', new FormData(event.currentTarget), true)).message_te; } catch (e) { out.textContent = e.message; } });
document.querySelector('#callback-form').addEventListener('submit', async event => { event.preventDefault(); const out = document.querySelector('#callback-result'); try { out.textContent = (await post('/api/callback', values(event.currentTarget))).message_te; } catch (e) { out.textContent = e.message; } });
