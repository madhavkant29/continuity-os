/** Short-lived, signed operator session. No session metadata is stored in the business graph. */
export const COOKIE = 'continuity_session';
export type Principal = {username: string; role: 'operator' | 'demo'; graph: string | null};
export const DEMO_GRAPH_PATTERN = /^continuity_judge_[a-f0-9]{24}$/;

const encoder = new TextEncoder();
function encodeBase64(input: Uint8Array):string {
  return btoa(Array.from(input, c => String.fromCharCode(c)).join('')).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');
}
function decodeBase64(input:string):Uint8Array<ArrayBuffer> {
  const base = input.replace(/-/g,'+').replace(/_/g,'/');
  const raw = atob(base.padEnd(Math.ceil(base.length / 4) * 4, '='));
  return Uint8Array.from(raw, c => c.charCodeAt(0));
}
async function key():Promise<CryptoKey> {
  const secret=process.env.FRONTEND_SESSION_SECRET;
  if(!secret || secret.length<48) throw new Error('FRONTEND_SESSION_SECRET not configured');
  return crypto.subtle.importKey('raw',encoder.encode(secret),{name:'HMAC',hash:'SHA-256'},false,['sign','verify']);
}
export async function makeSession(username:string,role:'operator'|'demo'='operator',graph:string|null=null):Promise<string> {
  if(role==='demo' && (!graph || !DEMO_GRAPH_PATTERN.test(graph)))throw new Error('Invalid demo graph');
  if(role==='operator' && graph)throw new Error('Operator cannot select a demo graph');
  // Short-lived session expiration is a security control; not persisted or displayed as a timestamp.
  const payload=encoder.encode(JSON.stringify({u:username,r:role,g:graph,e:Math.floor(Date.now()/1000)+8*60*60}));
  const body=encodeBase64(payload);
  const sig=await crypto.subtle.sign('HMAC',await key(),encoder.encode(body));
  return `${body}.${encodeBase64(new Uint8Array(sig))}`;
}
export async function readSession(value?:string):Promise<Principal|null> {
  if(!value || value.length>2048)return null;
  const parts=value.split('.');if(parts.length!==2)return null;
  try{
    const trusted=await crypto.subtle.verify('HMAC',await key(),decodeBase64(parts[1]),encoder.encode(parts[0]));
    if(!trusted)return null;
    const data=JSON.parse(new TextDecoder().decode(decodeBase64(parts[0])));
    if(typeof data.u!=='string' || !data.u || typeof data.e!=='number' || data.e<=Math.floor(Date.now()/1000))return null;
    if(data.r!=='operator' && data.r!=='demo')return null;
    if(data.r==='demo' && (typeof data.g!=='string' || !DEMO_GRAPH_PATTERN.test(data.g)))return null;
    if(data.r==='operator' && data.g!==null)return null;
    return {username:data.u,role:data.r,graph:data.g};
  }catch{return null;}
}
