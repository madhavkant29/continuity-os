import {NextRequest,NextResponse} from 'next/server';
import {COOKIE,readSession} from '@/lib/session';
export const runtime='nodejs';
type Context={params:Promise<{path:string[]}>};
async function forward(req:NextRequest,{params}:Context){
  const principal=await readSession(req.cookies.get(COOKIE)?.value);
  if(!principal)return NextResponse.json({detail:'Authentication required'},{status:401});
  const secret=process.env.INTERNAL_API_KEY;
  const internal=process.env.BACKEND_INTERNAL_URL;
  if(!secret || !internal)return NextResponse.json({detail:'Server configuration unavailable'},{status:503});
  const segments=(await params).path;
  if(!segments.length || segments.some(x=>!x || x==='.' || x==='..' || x.includes('/')))
    return NextResponse.json({detail:'Invalid path'},{status:400});
  const upstream=new URL('/api/'+segments.map(encodeURIComponent).join('/'),internal);
  const headers:Record<string,string>={'x-internal-api-key':secret,'x-operator-id':principal.username,'x-operator-role':principal.role};
  if(principal.role==='demo'){
    if(process.env.ENABLE_JUDGE_DEMO!=='true' || process.env.APP_MODE!=='demo' || !principal.graph)return NextResponse.json({detail:'Demo access disabled'},{status:403});
    headers['x-demo-graph']=principal.graph;
  }
  const content=req.headers.get('content-type');if(content)headers['content-type']=content;
  const confirmation=req.headers.get('x-reset-confirmation');if(confirmation)headers['x-reset-confirmation']=confirmation;
  try{
    const body=req.method==='GET'?undefined:await req.text();
    if(body && body.length>16000)return NextResponse.json({detail:'Request too large'},{status:413});
    const result=await fetch(upstream,{method:req.method,headers,body,cache:'no-store',signal:AbortSignal.timeout(20000)});
    return new NextResponse(await result.text(),{status:result.status,headers:{'content-type':'application/json','cache-control':'no-store','x-content-type-options':'nosniff'}});
  }catch{return NextResponse.json({detail:'Upstream service unavailable'},{status:502});}
}
export {forward as GET,forward as POST};
