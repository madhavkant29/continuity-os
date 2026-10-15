import assert from 'node:assert/strict';
import test from 'node:test';
import {makeSession,readSession} from '../lib/session.ts';
process.env.FRONTEND_SESSION_SECRET='unit-test-only-secret-that-is-long-enough-to-pass-validation-and-sign';
test('valid operator session authenticates and rejects tampering',async()=>{
 const session=await makeSession('Operator One');
 assert.deepEqual(await readSession(session),{username:'Operator One',role:'operator',graph:null});
 assert.equal(await readSession(session.slice(0,-2)+'zz'),null);
 assert.equal(await readSession('bogus'),null);
 assert.equal(await readSession(''),null);
});
test('misconfigured sessions fail closed',async()=>{
 const saved=process.env.FRONTEND_SESSION_SECRET;
 process.env.FRONTEND_SESSION_SECRET='short';
 await assert.rejects(()=>makeSession('operator'));
 process.env.FRONTEND_SESSION_SECRET=saved;
});
test('session expires and is rejected',async()=>{
 const original=Date.now;
 try{
   const session=await makeSession('Operator One');
   Date.now=()=>original()+9*60*60*1000;
   assert.equal(await readSession(session),null);
 }finally{Date.now=original;}
});

test('separate signed judge sessions target different graph namespaces',async()=>{
 const a='continuity_judge_aaaaaaaaaaaaaaaaaaaaaaaa';
 const b='continuity_judge_bbbbbbbbbbbbbbbbbbbbbbbb';
 const sa=await makeSession('Demo Judge','demo',a);
 const sb=await makeSession('Demo Judge','demo',b);
 assert.equal((await readSession(sa)).graph,a);
 assert.equal((await readSession(sb)).graph,b);
 assert.notEqual(sa,sb);
 await assert.rejects(()=>makeSession('Demo Judge','demo','continuity_demo'));
 await assert.rejects(()=>makeSession('Admin','operator',a));
});
test('signed session role cannot be changed to operator',async()=>{
 const s=await makeSession('Demo Judge','demo','continuity_judge_cccccccccccccccccccccccc');
 const [payload,signature]=s.split('.');
 const decoded=JSON.parse(Buffer.from(payload,'base64url').toString());
 decoded.r='operator';decoded.g=null;
 const forged=Buffer.from(JSON.stringify(decoded)).toString('base64url')+'.'+signature;
 assert.equal(await readSession(forged),null);
});
