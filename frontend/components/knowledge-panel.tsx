"use client";
import {useCallback,useEffect,useState} from 'react';
import {CheckCircle2,FileText,MessageSquare,Ticket,BookOpen,RefreshCw,ShieldCheck} from 'lucide-react';
import {api,type Workflow,type KnowledgeSource,type SourceDetail} from '@/lib/api';

const kinds=['DOCUMENT','TICKET','CONVERSATION'] as const;
const icons={DOCUMENT:FileText,TICKET:Ticket,CONVERSATION:MessageSquare};
export default function KnowledgePanel({workflows,workflowId,onWorkflowChange,onChanged,focusSourceId}:{workflows:Workflow[],workflowId:string,onWorkflowChange:(id:string)=>void,onChanged:()=>void,focusSourceId?:string}){
 const [items,setItems]=useState<KnowledgeSource[]>([]);
 const [detail,setDetail]=useState<SourceDetail|null>(null);
 const [kind,setKind]=useState<typeof kinds[number]>('DOCUMENT');
 const [title,setTitle]=useState('');const [reference,setReference]=useState('');const [content,setContent]=useState('');
 const [filter,setFilter]=useState('ALL');const [busy,setBusy]=useState(false);
 const [error,setError]=useState('');const [note,setNote]=useState('');
 const load=useCallback(async()=>{try{setItems(await api<KnowledgeSource[]>(`/workflows/${encodeURIComponent(workflowId)}/sources`));}catch(e){setError(String(e));}},[workflowId]);
 useEffect(()=>{setDetail(null);void load();},[load]);
 useEffect(()=>{if(focusSourceId){void api<SourceDetail>(`/sources/${encodeURIComponent(focusSourceId)}`).then(setDetail).catch(e=>setError(String(e)));}},[focusSourceId,workflowId]);
 async function openSource(id:string){setError('');try{setDetail(await api<SourceDetail>(`/sources/${encodeURIComponent(id)}`));}catch(e){setError(String(e));}}
 async function submit(e:React.FormEvent){e.preventDefault();if(busy)return;setBusy(true);setError('');setNote('');
  try{const created=await api<SourceDetail>(`/workflows/${encodeURIComponent(workflowId)}/sources`,{method:'POST',body:{kind,title,reference,content}});
   setTitle('');setReference('');setContent('');setNote('Source imported as pending review. It is not an authoritative policy until reviewed.');await load();await openSource(created.id);onChanged();
  }catch(e){setError(e instanceof Error?e.message:'Cannot import source');}finally{setBusy(false);}}
 async function verify(){if(!detail||busy||!window.confirm('Confirm that this source belongs to the workflow and can be cited as reviewed evidence?'))return;
  setBusy(true);setError('');try{const updated=await api<SourceDetail>(`/sources/${encodeURIComponent(detail.id)}/verify`,{method:'POST',body:{}});
    setDetail(updated);setNote('Reviewed source association saved in FalkorDB.');await load();onChanged();
   }catch(e){setError(e instanceof Error?e.message:'Review failed');}finally{setBusy(false);}}
 const filtered=items.filter(s=>s.current&&(filter==='ALL'||s.kind===filter));
 return <div className="knowledge-layout">
  <section className="panel knowledge-list">
   <div className="panel-heading"><div><span className="section-tag">EVIDENCE REGISTRY</span><h3>Documents, tickets and conversations</h3></div><button className="text-action" onClick={()=>void load()}><RefreshCw size={15}/> Refresh</button></div>
   <p className="soft-description">Each source is connected to its project, workflow and governing decision. Open a record to see original line-level citations.</p>
   <div className="knowledge-filters"><select aria-label="Workflow to inspect" value={workflowId} onChange={e=>onWorkflowChange(e.target.value)}>{workflows.map(w=><option key={w.id} value={w.id}>{w.name}</option>)}</select><select aria-label="Filter sources by type" value={filter} onChange={e=>setFilter(e.target.value)}><option value="ALL">All source types</option>{kinds.map(k=><option key={k} value={k}>{k.toLowerCase()}</option>)}</select></div>
   <div className="knowledge-entries">{filtered.map(s=>{const Icon=icons[s.kind];return <button key={s.id} className={`knowledge-entry ${detail?.id===s.id?'selected':''}`} onClick={()=>void openSource(s.id)}><Icon size={18}/><span><strong>{s.title}</strong><small>{s.reference||s.kind} · {s.passage_count} citations</small></span><span className={s.review_status==='PENDING_REVIEW'?'source-pending':'source-ok'}>{s.review_status==='PENDING_REVIEW'?'Review needed':'Reviewed'}</span></button>})}
   {!filtered.length&&<p className="soft-description">No matching sources. Import a source below.</p>}</div>
   <div className="knowledge-import"><h3>Add company knowledge</h3><p className="soft-description">Use fictional data in the public demo. Text imports are stored as immutable source versions with line citations.</p>
    <form onSubmit={submit}><label>Source type<select value={kind} onChange={e=>setKind(e.target.value as typeof kinds[number])}>{kinds.map(k=><option key={k} value={k}>{k.toLowerCase()}</option>)}</select></label>
    <label>Title<input value={title} onChange={e=>setTitle(e.target.value)} minLength={3} maxLength={160} required placeholder="e.g. Incident escalation SOP"/></label>
    <label>External reference (optional)<input value={reference} onChange={e=>setReference(e.target.value)} maxLength={120} placeholder="e.g. TICKET-204 or channel/thread"/></label>
    <label>Original source text<textarea value={content} onChange={e=>setContent(e.target.value)} minLength={10} maxLength={10000} required rows={6} placeholder="Paste process notes, ticket details or a conversation transcript. Preserve original line breaks for citations."/></label>
    <button className="primary-button" disabled={busy||title.trim().length<3||content.trim().length<10} type="submit"><BookOpen size={16}/> {busy?'Saving…':'Import source'}</button></form>
   </div>
  </section>
  <section className="panel knowledge-detail"><div className="panel-heading"><div><span className="section-tag">SOURCE-TO-DECISION TRACE</span><h3>Evidence inspector</h3></div><ShieldCheck size={19}/></div>
   {detail?<><div className="knowledge-detail-head"><strong>{detail.title}</strong><span>{detail.kind} · {detail.reference||'Manual reference'}</span><span className={detail.review_status==='PENDING_REVIEW'?'source-pending':'source-ok'}>{detail.review_status.replaceAll('_',' ')}</span></div>
   {!detail.current&&<p className="source-warning">This version was superseded. Its citations are preserved, but it cannot be reviewed as current.</p>}
   {detail.review_status==='PENDING_REVIEW'&&detail.current&&<div className="review-box"><p>Imported text is not treated as verified company policy. Confirm the source association before using it as reviewed evidence.</p><button className="outline-button" disabled={busy} onClick={verify}><CheckCircle2 size={16}/> Review source association</button></div>}
   <p className="soft-description">Every citation below points to an exact line stored in FalkorDB. The original text is reproduced without AI summarization.</p>
   <div className="passage-list">{detail.passages.map(p=><div className="passage" key={p.id}><code>{p.locator}</code><p>{p.quote}</p><button onClick={()=>void navigator.clipboard?.writeText(`${detail.title} [${p.locator}]: ${p.quote}`)} className="text-action">Copy citation</button></div>)}</div></>:<div className="knowledge-empty">Choose any source to inspect its original passages and review status.</div>}
   {error&&<div className="alert alert-error">{error}</div>}{note&&<div className="alert alert-success">{note}</div>}
  </section>
 </div>;
}
