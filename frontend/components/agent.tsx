"use client";
import {useState} from "react";
import {Bot, Send, X, ExternalLink} from "lucide-react";
import {api, type AgentResponse, type Workflow} from "@/lib/api";
export default function Agent({workflows, open, setOpen, onOpenCitation}:{workflows:Workflow[];open:boolean;setOpen:(v:boolean)=>void;onOpenCitation?:(workflowId:string,sourceId:string)=>void}){
 const [workflow,setWorkflow]=useState("enterprise-refund");
 const [text,setText]=useState(""); const [busy,setBusy]=useState(false); const [error,setError]=useState("");
 const [messages,setMessages]=useState<{q:string;response:AgentResponse;workflow_id:string}[]>([]);
 async function ask(question?:string){const q=(question??text).trim();if(q.length<3||busy)return;setBusy(true);setError("");setText("");
 try{const workflow_id=workflow;const response=await api<AgentResponse>("/agent/ask",{method:"POST",body:{workflow_id,message:q}});setMessages(prev=>[...prev,{q,response,workflow_id}]);}
 catch(e){setError(e instanceof Error?e.message:"Agent unavailable");}finally{setBusy(false);}}
 if(!open)return null;
 return <div className="agent-overlay" onClick={()=>setOpen(false)}><aside className="agent-panel" onClick={e=>e.stopPropagation()}>
 <div className="agent-head"><div className="agent-brand"><div className="agent-icon"><Bot size={20}/></div><div><strong>Continuity Analyst</strong><small>Graph-grounded analysis + safe simulations</small></div></div><button className="icon-button" onClick={()=>setOpen(false)} aria-label="Close analyst"><X size={18}/></button></div>
 <div className="agent-select"><label htmlFor="agent-workflow">Workflow context</label><select id="agent-workflow" value={workflow} onChange={e=>setWorkflow(e.target.value)}>{workflows.map(w=><option key={w.id} value={w.id}>{w.name}</option>)}</select></div>
 <div className="agent-content">
 {messages.length===0&&<div className="agent-welcome"><div className="agent-round"><Bot size={24}/></div><h3>Ask about operational resilience.</h3><p>Answers are assembled from live FalkorDB relationships and constraint checks, with explicit source records.</p>
 {["Run and save an Ava Shah absence check","Who can approve the refund?","Which documents support this workflow?"].map(s=><button className="prompt" key={s} onClick={()=>ask(s)}>{s}<ExternalLink size={13}/></button>)}
 </div>}
 {messages.map((m,i)=><div key={i} className="agent-exchange"><div className="user-bubble">{m.q}</div><div className="assistant-bubble"><p>{m.response.answer}</p><div className="agent-sources"><strong>Evidence trail</strong>{m.response.sources.map((s,j)=><div key={j} className="source-chip"><strong>{s.type}: {s.label}</strong>{s.locator&&<code>{s.locator}</code>}{s.quote&&<q>{s.quote}</q>}{s.review_status==='PENDING_REVIEW'&&<small>Unverified import</small>}{s.locator&&onOpenCitation&&<button className="text-action" onClick={()=>{onOpenCitation(m.workflow_id,s.id);setOpen(false)}}>Inspect original passage <ExternalLink size={12}/></button>}</div>)}</div><details><summary>Tool trace: {m.response.tool}</summary>{m.response.trace.map((t,j)=><p className="trace" key={j}>{t.step} — {t.detail}</p>)}</details></div></div>)}
 {busy&&<div className="assistant-bubble">Querying the company graph…</div>}{error&&<div className="error-message">{error}</div>}
 </div><form className="agent-compose" onSubmit={e=>{e.preventDefault();ask()}}><input aria-label="Ask the analyst" placeholder="Ask about people, permissions, risks…" value={text} onChange={e=>setText(e.target.value)} maxLength={500}/><button className="primary-button" type="submit" disabled={busy||text.trim().length<3} aria-label="Send message"><Send size={17}/></button></form>
 <div className="agent-foot">Simulation records may be saved to your synthetic graph · No external actions</div>
 </aside></div>;
}
