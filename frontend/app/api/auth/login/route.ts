import {NextRequest,NextResponse} from 'next/server';
import {scryptSync,timingSafeEqual} from 'node:crypto';
import {COOKIE,makeSession} from '@/lib/session';
export const runtime='nodejs';
// Process-local throttling is defense in depth; reverse proxy must enforce distributed rate limiting.
const failures=new Map<string,{count:number;until:number}>();
export async function POST(req:NextRequest){
  const origin=req.headers.get('origin');
  if(origin && origin!==(process.env.PUBLIC_APP_ORIGIN||req.nextUrl.origin))return NextResponse.json({detail:'Invalid origin'},{status:403});
  const addr=req.headers.get('x-real-ip')||'login';
  const now=Date.now();
  const recent=failures.get(addr);
  if(recent && recent.count>=8 && recent.until>now)return NextResponse.json({detail:'Too many attempts'},{status:429});
  let body:{username?:unknown;password?:unknown};
  try{if(Number(req.headers.get('content-length')||'0')>4096)throw new Error();body=await req.json();}catch{return NextResponse.json({detail:'Malformed login request'},{status:400});}
  const user=process.env.APP_LOGIN_USER;
  const expected=process.env.APP_LOGIN_PASSWORD_HASH;
  if(!user || !expected) return NextResponse.json({detail:'Login is not configured'},{status:503});
  const [salt,stored]=expected.split(':');
  let ok=false;
  if(typeof body.username==='string' && typeof body.password==='string' && body.password.length<=256 && salt && stored){
    try{
      const calculated=scryptSync(body.password,Buffer.from(salt,'hex'),64);
      const saved=Buffer.from(stored,'hex');
      ok=saved.length===calculated.length && timingSafeEqual(saved,calculated) && body.username===user;
    }catch{ok=false;}
  }
  if(!ok){
    const next=recent && recent.until>now?recent.count+1:1;
    if(failures.size>2000)failures.clear();
    failures.set(addr,{count:next,until:now+15*60*1000});
    return NextResponse.json({detail:'Invalid credentials'},{status:401});
  }
  failures.delete(addr);
  const session=await makeSession(user);
  const res=NextResponse.json({ok:true});
  res.cookies.set(COOKIE,session,{httpOnly:true,sameSite:'strict',secure:process.env.COOKIE_SECURE==='true',path:'/',maxAge:8*60*60});
  res.headers.set('Cache-Control','no-store');
  return res;
}
