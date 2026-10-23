/** Optional backend URL. Blank preserves the public, zero-service synthetic demo.
 * Edit DEPLOYED_API_URL after deploying the API, or configure using Data management.
 * Never put administrator credentials in this file or GitHub.
 */
export const DEPLOYED_API_URL = '';
export function apiBase(){
  const injected=String(globalThis.INSIGHTFLOW_API_URL||'').trim();
  let saved='';
  try{saved=localStorage.getItem('insightflow_api_url')||'';}catch{}
  return (injected||DEPLOYED_API_URL||saved).replace(/\/+$/,'');
}
