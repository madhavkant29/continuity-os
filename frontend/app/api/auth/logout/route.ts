import {NextResponse} from 'next/server';
import {COOKIE} from '@/lib/session';
export async function GET(req:Request){
  const res=NextResponse.redirect(new URL('/login',process.env.PUBLIC_APP_ORIGIN||req.url));
  res.cookies.set(COOKIE,'',{path:'/',maxAge:0,httpOnly:true,sameSite:'strict'});
  res.headers.set('Cache-Control','no-store');
  return res;
}
