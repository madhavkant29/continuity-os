import {NextRequest, NextResponse} from 'next/server';
import {COOKIE, readSession} from './lib/session';

export async function middleware(req:NextRequest){
  const pathname=req.nextUrl.pathname;
  const expectedOrigin=process.env.PUBLIC_APP_ORIGIN||req.nextUrl.origin;
  if(pathname==='/login' || pathname==='/api/auth/login' || pathname==='/api/auth/demo' || pathname==='/api/auth/demo-status'){
    return NextResponse.next();
  }
  const principal=await readSession(req.cookies.get(COOKIE)?.value);
  if(!principal){
    if(pathname.startsWith('/api/'))return NextResponse.json({detail:'Authentication required'},{status:401});
    return NextResponse.redirect(new URL('/login',expectedOrigin));
  }
  if(pathname.startsWith('/api/') && !['GET','HEAD','OPTIONS'].includes(req.method)){
    const origin=req.headers.get('origin');
    const referer=req.headers.get('referer');
    let refOrigin='';
    try{if(referer)refOrigin=new URL(referer).origin;}catch{refOrigin='';}
    if((origin && origin!==expectedOrigin) || (!origin && refOrigin!==expectedOrigin)){
      return NextResponse.json({detail:'Cross-origin write rejected'},{status:403});
    }
  }
  const res=NextResponse.next();
  res.headers.set('Cache-Control','no-store');
  return res;
}
export const config={matcher:['/((?!_next/static|_next/image|favicon.ico|icon.svg).*)']};
