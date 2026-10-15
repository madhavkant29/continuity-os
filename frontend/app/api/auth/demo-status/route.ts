import {NextResponse} from 'next/server';
export async function GET(){
  return NextResponse.json({enabled:process.env.APP_MODE==='demo' && process.env.ENABLE_JUDGE_DEMO==='true'},
    {headers:{'Cache-Control':'no-store'}});
}
