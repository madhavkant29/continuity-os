import {NextRequest,NextResponse} from 'next/server';
import {COOKIE,readSession} from '@/lib/session';
export async function GET(req:NextRequest){
  const principal=await readSession(req.cookies.get(COOKIE)?.value);
  if(!principal)return NextResponse.json({detail:'Authentication required'},{status:401});
  return NextResponse.json({operator:principal.username,role:principal.role},{headers:{'Cache-Control':'no-store'}});
}
