import {randomBytes} from 'node:crypto';
import {NextRequest, NextResponse} from 'next/server';
import {COOKIE,makeSession} from '@/lib/session';

export const runtime='nodejs';

// Each judge receives an independent, synthetic FalkorDB graph.
// The same-origin gate prevents other sites from initiating demo sessions.
const requests=new Map<string,{count:number;until:number}>();
export async function POST(req:NextRequest){
  const expectedOrigin=process.env.PUBLIC_APP_ORIGIN||req.nextUrl.origin;
  if(req.headers.get('origin')!==expectedOrigin)
    return NextResponse.json({detail:'Invalid origin'},{status:403});
  if(process.env.APP_MODE!=='demo' || process.env.ENABLE_JUDGE_DEMO!=='true')
    return NextResponse.json({detail:'Judge demo disabled'},{status:404});
  const addr=req.headers.get('x-real-ip')||'anonymous';
  const now=Date.now();
  const current=requests.get(addr);
  if(current && current.until>now && current.count>=5)
    return NextResponse.json({detail:'Demo session limit reached. Please contact the team.'},{status:429});
  if(requests.size>2000)requests.clear();
  requests.set(addr,{count:current && current.until>now?current.count+1:1,until:now+60*60*1000});
  const base=process.env.BACKEND_INTERNAL_URL;
  const key=process.env.INTERNAL_API_KEY;
  if(!base || !key)return NextResponse.json({detail:'Server not configured'},{status:503});
  const graph='continuity_judge_'+randomBytes(12).toString('hex');
  try{
    const response=await fetch(new URL('/api/demo/bootstrap',base),{
      method:'POST',headers:{'x-internal-api-key':key,'x-operator-role':'demo','x-demo-graph':graph},
      cache:'no-store',signal:AbortSignal.timeout(20000)
    });
    if(!response.ok)return NextResponse.json({detail:'Demo initialization failed'},{status:503});
    const session=await makeSession('Demo Judge','demo',graph);
    const result=NextResponse.json({ok:true,operator:'Demo Judge',role:'demo'});
    result.cookies.set(COOKIE,session,{httpOnly:true,sameSite:'strict',secure:process.env.COOKIE_SECURE==='true',path:'/',maxAge:8*60*60});
    result.headers.set('Cache-Control','no-store');
    return result;
  }catch{
    return NextResponse.json({detail:'Demo workspace unavailable'},{status:503});
  }
}
