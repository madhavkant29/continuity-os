'use client';
import {useEffect,useState} from 'react';
import {ShieldCheck,LockKeyhole,ArrowRight,PlayCircle} from 'lucide-react';
export default function Login(){
  const [username,setUsername]=useState('');const [password,setPassword]=useState('');
  const [busy,setBusy]=useState(false);const [error,setError]=useState('');
  const [demoBusy,setDemoBusy]=useState(false);const [demoAvailable,setDemoAvailable]=useState(false);
  // Availability is public; the server independently validates demo-mode on every request.
  useEffect(()=>{void fetch('/api/auth/demo-status',{cache:'no-store'}).then(r=>r.json()).then(v=>setDemoAvailable(v.enabled===true)).catch(()=>{});},[]);
  async function enterDemo(){setDemoBusy(true);setError('');try{
    const r=await fetch('/api/auth/demo',{method:'POST',headers:{'Content-Type':'application/json'}});
    if(!r.ok){const result=await r.json();throw new Error(result.detail||'Demo unavailable');}
    window.location.assign('/');
  }catch(err){setError(err instanceof Error?err.message:'Demo unavailable');setDemoBusy(false);}}
  async function submit(e:React.FormEvent){e.preventDefault();setBusy(true);setError('');
    try{
      const res=await fetch('/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username,password})});
      if(!res.ok){const json=await res.json();throw new Error(json.detail||'Sign-in failed');}
      window.location.assign('/');
    }catch(err){setError(err instanceof Error?err.message:'Sign-in failed');setPassword('');}
    finally{setBusy(false);}
  }
  return <main className="login-viewport"><section className="login-box">
    <div className="login-mark"><ShieldCheck size={30}/></div><span className="section-tag">SECURE WORKSPACE</span>
    <h1>ContinuityOS</h1><p>Sign in to review continuity simulations, dependencies, and recovery decisions.</p>
    {demoAvailable&&<div className="judge-entry"><div className="judge-entry-header"><strong>Judging the project?</strong><span>NO SIGNUP NEEDED</span></div><p>Open your own fictional Northstar Payments workspace, already populated with employees, workflows and permissions.</p><button className="judge-entry-button" onClick={enterDemo} disabled={demoBusy||busy}><PlayCircle size={18}/>{demoBusy?'Preparing your workspace…':'Explore live demo'}<ArrowRight size={17}/></button><small>Isolated test data. No account or password required.</small></div>}
    <form onSubmit={submit} className="login-form"><label htmlFor="username">Operator</label>
    <input id="username" value={username} onChange={e=>setUsername(e.target.value)} required autoComplete="username" maxLength={100}/>
    <label htmlFor="password">Password</label><input type="password" id="password" value={password} onChange={e=>setPassword(e.target.value)} required autoComplete="current-password"/>
    {error&&<div className="alert alert-error">{error}</div>}
    <button type="submit" disabled={busy} className="primary-button"><LockKeyhole size={16}/>{busy?'Signing in…':'Sign in'}<ArrowRight size={16}/></button></form>
    <small>Operator credentials are for project administrators. Judges can use the isolated demo above.</small>
  </section></main>;
}
