"use client";
import {useCallback,useEffect,useMemo,useState} from "react";
import {
 Activity, ArrowRight, Bot, ClipboardList, Check, CheckCheck, ChevronDown,
 ChevronRight, CircleAlert, CircleCheck, ClipboardCheck, Database, FileText,
 GitBranch, LayoutDashboard, LockKeyhole, Menu, MoreHorizontal, Play,
 RotateCcw, SearchCheck, ShieldCheck, ShieldX, Sparkles, UserRoundX, UsersRound,
 Workflow as WorkflowIcon, Wrench, X
} from "lucide-react";
import GraphCanvas from "@/components/graph-canvas";
import Agent from "@/components/agent";
import KnowledgePanel from "@/components/knowledge-panel";
import {api, type AgentResponse, type Audit, type GraphView, type Overview,
 type Person,type Repair,type Simulation,type Snapshot,type Workflow} from "@/lib/api";

type View="overview"|"simulator"|"graph"|"knowledge"|"repairs"|"audit";
const sections:{id:View;name:string;icon:typeof LayoutDashboard}[]=[
 {id:"overview",name:"Overview",icon:LayoutDashboard},
 {id:"simulator",name:"Disruption lab",icon:Activity},
 {id:"graph",name:"Knowledge graph",icon:GitBranch},
 {id:"knowledge",name:"Company sources",icon:FileText},
 {id:"repairs",name:"Recovery queue",icon:Wrench},
 {id:"audit",name:"Audit history",icon:ClipboardCheck},
];
const headings:Record<View,{label:string;title:string;desc:string}>={
 overview:{label:"WORKSPACE / OVERVIEW",title:"Operational resilience, made visible.",desc:"Understand which workflows remain executable—and what needs attention before a disruption becomes an incident."},
 simulator:{label:"WORKSPACE / DISRUPTION LAB",title:"Test a failure before it happens.",desc:"Remove a key person from the operating graph, check authorization constraints, and find a policy-safe path forward."},
 graph:{label:"WORKSPACE / GRAPH EXPLORER",title:"Understand the dependencies.",desc:"Trace how workflows depend on people, skills, permissions, documented decisions, and policy constraints."},
 knowledge:{label:"WORKSPACE / COMPANY KNOWLEDGE",title:"Verify what the company knows.",desc:"Import original documents, tickets and conversations. Link them to decisions and inspect source-level citations."},
 repairs:{label:"WORKSPACE / RECOVERY",title:"Close the continuity gap.",desc:"Review proposed corrections, apply them in the sandbox, and verify a feasible assignment before closing the case."},
 audit:{label:"WORKSPACE / AUDIT",title:"Every decision leaves evidence.",desc:"An append-only view of simulation, proposal, approval, and sandbox verification events."},
};
function Status({status}:{status:string}){
 const positive=["FEASIBLE","VERIFIED","PASSED"].includes(status);
 const negative=["BLOCKED","FAILED"].includes(status);
 return <span className={`status ${positive?"status-good":negative?"status-bad":"status-warn"}`}><span className="status-dot"/>{status.replaceAll("_"," ")}</span>
}
function Empty({title,detail}:{title:string;detail:string}){return <div className="empty"><div className="empty-ring"><SearchCheck size={23}/></div><strong>{title}</strong><p>{detail}</p></div>}
function Metric({label,value,sub,icon:Icon,emphasis}:{label:string;value:string|number;sub:string;icon:typeof LayoutDashboard;emphasis?:boolean}){return <div className="metric-card"><div className="metric-top"><span>{label}</span><div className={`metric-icon ${emphasis?"emphasis":""}`}><Icon size={19}/></div></div><div className="metric-value">{value}</div><div className="metric-sub">{sub}</div></div>}
function Pill({children}:{children:React.ReactNode}){return <span className="muted-pill">{children}</span>}
export default function Page(){
 const [view,setView]=useState<View>("overview");
 const [overview,setOverview]=useState<Overview|null>(null);
 const [people,setPeople]=useState<Person[]>([]);const [audit,setAudit]=useState<Audit[]>([]);
 const [repairs,setRepairs]=useState<Repair[]>([]);const [selectedWorkflow,setSelectedWorkflow]=useState("enterprise-refund");
 const [snapshot,setSnapshot]=useState<Snapshot|null>(null);const [graph,setGraph]=useState<GraphView|null>(null);
 const [unavailable,setUnavailable]=useState<string[]>(["p02"]);const [simulation,setSimulation]=useState<Simulation|null>(null);
 const [activeRepair,setActiveRepair]=useState<Repair|null>(null);
 const [isBusy,setIsBusy]=useState(false);const [error,setError]=useState("");
 const [operator,setOperator]=useState("");const [role,setRole]=useState<"operator"|"demo">("operator");
 const [notice,setNotice]=useState("");const [focusSourceId,setFocusSourceId]=useState("");const [docTitle,setDocTitle]=useState("");const [docContent,setDocContent]=useState("");const [assistantOpen,setAssistantOpen]=useState(false);const [sidebarOpen,setSidebarOpen]=useState(false);
 const workflows=overview?.workflows||[];
 const refresh=useCallback(async()=>{
   try{const [o,p,r,a]=await Promise.all([api<Overview>("/overview"),api<Person[]>("/people"),api<Repair[]>("/repairs"),api<Audit[]>("/audit")]);
     setOverview(o);setPeople(p);setRepairs(r);setAudit(a);}
   catch(e){setError(e instanceof Error?e.message:"Could not load the dashboard");}
 },[]);
 useEffect(()=>{void refresh()},[refresh]);
 useEffect(()=>{void api<{operator:string;role:"operator"|"demo"}>("/auth/me").then(x=>{setOperator(x.operator);setRole(x.role);}).catch(()=>{});},[]);
 useEffect(()=>{
   let active=true;
   Promise.all([api<Snapshot>(`/workflows/${selectedWorkflow}`),api<GraphView>(`/workflows/${selectedWorkflow}/graph`)])
      .then(([s,g])=>{if(active){setSnapshot(s);setGraph(g);}})
      .catch(e=>{if(active)setError(e instanceof Error?e.message:"Could not load graph");});
   return()=>{active=false};
 },[selectedWorkflow]);
 const participants=useMemo(()=>{
   if(!snapshot)return [];
   const skills=new Set(snapshot.steps.map(s=>s.skill));
   return snapshot.people.filter(p=>p.skills?.some(skill=>skills.has(skill)));
 },[snapshot]);
 const selectedNames=people.filter(p=>unavailable.includes(p.id)).map(p=>p.name).join(", ");
 const navigate=(to:View)=>{
   setView(to);setSidebarOpen(false);setError("");
   if(to==="graph"){
     void api<GraphView>(`/workflows/${selectedWorkflow}/graph`).then(setGraph)
       .catch(e=>setError(e instanceof Error?e.message:"Graph refresh failed"));
   }
 };
 const chooseWorkflow=(id:string)=>{setSelectedWorkflow(id);setUnavailable([]);setSimulation(null);setActiveRepair(null);};
 async function perform<T>(fn:()=>Promise<T>,success?:string):Promise<T|null>{setIsBusy(true);setError("");setNotice("");
   try{const result=await fn();if(success)setNotice(success);await refresh();return result;}
   catch(e){setError(e instanceof Error?e.message:"An unexpected error occurred");return null;}
   finally{setIsBusy(false);}}
 async function runSimulation(){if(!selectedWorkflow)return;
   const s=await perform(()=>api<Simulation>("/simulations",{method:"POST",body:{workflow_id:selectedWorkflow,unavailable}}),"Simulation completed using current FalkorDB permissions.");
   if(s){setSimulation(s);setActiveRepair(null);}}
 async function proposeRepair(simId:string){const r=await perform(()=>api<Repair>(`/simulations/${simId}/repair`,{method:"POST"}),"Recovery proposal saved for review.");if(r)setActiveRepair(r);}
 async function approve(id:string){const r=await perform(()=>api<Repair>(`/repairs/${id}/approve`,{method:"POST",body:{}}),"Sandbox authorization correction recorded. Run a drill next.");if(r)setActiveRepair(r);}
 async function drill(id:string){const d=await perform(()=>api<{status:string}>(`/repairs/${id}/drill`,{method:"POST"}),"Sandbox drill finished; inspect verification status.");if(d){const r=await api<Repair>(`/repairs/${id}`);setActiveRepair(r);}}
 async function reset(){if(!window.confirm("Restart your synthetic workspace and delete its simulations, repairs and audit events?"))return;
   const response=await perform(()=>api("/demo/reset",{method:"POST",headers:{"x-reset-confirmation":"RESET_SYNTHETIC_DATA"}}),"Your synthetic workspace was restored to its initial state.");if(response){setSimulation(null);setActiveRepair(null);setUnavailable(["p02"]);navigate("overview");}}
 async function attachDocument(){
   if(docTitle.trim().length<3||docContent.trim().length<10)return;
   const r=await perform(()=>api(`/workflows/${selectedWorkflow}/documents`,{method:"POST",body:{title:docTitle.trim(),content:docContent.trim()}}),"Source document linked to the workflow graph.");
   if(r){setDocTitle("");setDocContent("");
     const [sn,g]=await Promise.all([api<Snapshot>(`/workflows/${selectedWorkflow}`),api<GraphView>(`/workflows/${selectedWorkflow}/graph`)]);
     setSnapshot(sn);setGraph(g);}
 }
 const h=headings[view];
 return <div className="shell">
  <div className={`mobile-dim ${sidebarOpen?"visible":""}`} onClick={()=>setSidebarOpen(false)}/>
  <aside className={`sidebar ${sidebarOpen?"sidebar-show":""}`}>
   <div className="brand"><div className="brand-mark"><span/><span/><span/><span/></div><div><strong>continuity<span>os</span></strong><small>OPERATIONAL INTELLIGENCE</small></div></div>
   <div className="side-label">WORKSPACE</div><nav aria-label="Main navigation">{sections.map(s=><button key={s.id} className={`nav-item ${view===s.id?"active":""}`} onClick={()=>navigate(s.id)}><s.icon size={18}/><span>{s.name}</span>{s.id==="repairs"&&repairs.filter(r=>r.status!=="VERIFIED").length>0&&<b>{repairs.filter(r=>r.status!=="VERIFIED").length}</b>}</button>)}</nav>
   <div className="sidebar-bottom"><div className="side-label">ENVIRONMENT</div><div className="environment"><span className="env-light"/><div><strong>Northstar Payments</strong><small>Synthetic demo dataset</small></div></div>
    <div className="sidebar-rule"/><button className="reset-button" onClick={reset}><RotateCcw size={15}/> {role==="demo"?"Restart my demo":"Reset demo data"}</button>
    <div className="sidebar-note"><ShieldCheck size={15}/> Sandbox permissions only. No live financial systems connected.</div>
   </div>
  </aside>
  <main className="main">
   <header className="topbar"><div className="topbar-left"><button className="icon-button mobile-menu" aria-label="Open menu" onClick={()=>setSidebarOpen(true)}><Menu size={19}/></button><span className="breadcrumb">Northstar Payments</span><ChevronRight size={14}/><span className="breadcrumb-current">{sections.find(s=>s.id===view)?.name}</span></div><div className="topbar-right"><span className="demo-pill"><span/> DEMO WORKSPACE</span><span className="topbar-divider"/><button className="topbar-assistant" onClick={()=>setAssistantOpen(true)}><Bot size={17}/> Ask analyst</button><a className="avatar" href="/api/auth/logout" title={`Signed in: ${operator||"Operator"} · Sign out`}>{operator?operator.split(/\s+/).slice(0,2).map(x=>x[0]).join("").toUpperCase():"OP"}</a></div></header>
   <div className="content"><div className="page-head"><div><div className="eyebrow">{h.label}</div><h1>{h.title}</h1><p>{h.desc}</p></div><button className="analyst-link" onClick={()=>setAssistantOpen(true)}><Sparkles size={16}/> Ask the analyst <ArrowRight size={15}/></button></div>
   {error&&<div className="alert alert-error"><CircleAlert size={18}/><span>{error}</span><button aria-label="Dismiss error" onClick={()=>setError("")}><X size={16}/></button></div>}
   {notice&&<div className="alert alert-success"><CircleCheck size={18}/><span>{notice}</span><button aria-label="Dismiss message" onClick={()=>setNotice("")}><X size={16}/></button></div>}
   {!overview&&<div className="loading-panel"><div className="spinner"/> Connecting to FalkorDB-backed workspace…</div>}
   {overview&&view==="overview"&&<>
    <section className="stats-grid"><Metric label="Monitored workflows" value={overview.workflows.length} sub="Across the organization" icon={WorkflowIcon}/>
      <Metric label="Mapped employees" value={overview.employees} sub={`${overview.teams} connected departments`} icon={UsersRound}/>
      <Metric label="Blocked simulations" value={overview.blocked_simulations} sub="Among recent scenario runs" icon={ShieldX} emphasis/>
      <Metric label="Open recovery reviews" value={overview.open_repairs} sub="Awaiting approval or drill" icon={ClipboardList}/></section>
    <div className="overview-grid"><section className="panel feature-panel"><div className="panel-brow"><span className="section-tag">FEATURED SCENARIO</span><Pill>01 / Operational continuity</Pill></div>
      <div className="feature-content"><div className="feature-art"><div className="feature-art-circle one"/><div className="feature-art-circle two"/><div className="feature-inner"><ShieldX size={30}/><div className="feature-dash"/><span>SIMULATE THE UNKNOWN</span></div></div>
      <div className="feature-copy"><h2>One absence. A critical workflow at risk.</h2><p>Remove the primary finance approver. Uncover a hidden separation-of-duties conflict and find the smallest approved change to restore the workflow.</p>
        <button className="primary-button" onClick={()=>{chooseWorkflow("enterprise-refund");setUnavailable(["p02"]);navigate("simulator")}}>Run featured scenario <ArrowRight size={17}/></button></div></div>
    </section><section className="panel snapshot-panel"><div className="panel-heading"><div><span className="section-tag">THE MODEL</span><h3>Connected company context</h3></div><Database size={19}/></div>
      <div className="model-lines"><div><span className="node-bullet mint"/><div><strong>People & teams</strong><small>Ownership and availability</small></div><span>{overview.employees}</span></div><div><span className="node-bullet blue"/><div><strong>Workflow tasks</strong><small>Required skills and grants</small></div><span>{overview.workflows.reduce((a,w)=>a+w.step_count,0)}</span></div><div><span className="node-bullet amber"/><div><strong>Policy constraints</strong><small>Independent approvals</small></div><span>{overview.workflows.length}</span></div><div><span className="node-bullet violet"/><div><strong>Supporting documents</strong><small>Workflow references</small></div><span>{overview.workflows.length*2}</span></div></div>
      <button className="text-action" onClick={()=>navigate("graph")}>Explore knowledge graph <ArrowRight size={15}/></button>
    </section></div>
    <section className="panel full"><div className="panel-heading"><div><span className="section-tag">OPERATIONS CATALOG</span><h3>Critical workflows</h3></div><button className="text-action" onClick={()=>navigate("simulator")}>Open disruption lab <ArrowRight size={15}/></button></div>
       <div className="table-wrap"><table className="data-table"><thead><tr><th>WORKFLOW</th><th>DEPARTMENT</th><th>CRITICALITY</th><th>STEPS</th><th></th></tr></thead><tbody>{workflows.map(w=><tr key={w.id}><td><div className="workflow-name"><div className="table-symbol"><WorkflowIcon size={16}/></div><div><strong>{w.name}</strong><small>{w.description}</small></div></div></td><td>{w.department}</td><td><span className={`priority ${w.criticality==="Critical"?"high":"medium"}`}>{w.criticality}</span></td><td>{w.step_count} stages</td><td><button className="table-link" onClick={()=>{chooseWorkflow(w.id);navigate("simulator")}}>Inspect <ArrowRight size={14}/></button></td></tr>)}</tbody></table></div>
    </section>
   </>}
   {overview&&view==="simulator"&&<>
    <div className="sim-grid"><section className="panel simulation-setup"><div className="panel-heading"><div><span className="section-tag">01 / CONFIGURE</span><h3>Disruption scenario</h3></div><Activity size={20}/></div>
      <label className="field-label" htmlFor="workflow">TARGET WORKFLOW</label><div className="select-wrap"><select id="workflow" value={selectedWorkflow} onChange={e=>chooseWorkflow(e.target.value)}>{workflows.map(w=><option value={w.id} key={w.id}>{w.name}</option>)}</select><ChevronDown size={17}/></div>
      <div className="field-label spacer-label">MAKE TEAM MEMBERS UNAVAILABLE <span>{unavailable.length} selected</span></div>
      <div className="people-picker">{participants.map(p=><button key={p.id} className={`person-option ${unavailable.includes(p.id)?"is-away":""}`} onClick={()=>setUnavailable(v=>v.includes(p.id)?v.filter(x=>x!==p.id):[...v,p.id])}><span className="mini-avatar">{p.name.split(" ").map(x=>x[0]).slice(0,2).join("")}</span><span className="person-text"><strong>{p.name}</strong><small>{p.role} · {p.team}</small></span><span className="person-check">{unavailable.includes(p.id)&&<Check size={13}/>}</span></button>)}</div>
      <div className="scenario-note"><UserRoundX size={17}/><div><strong>{unavailable.length?"Simulated absence":"Baseline assessment"}</strong><p>{unavailable.length?`${selectedNames} will be unavailable for assignment.`:"No employees excluded; evaluate current eligibility and policy."}</p></div></div>
      <button className="primary-button run-button" disabled={isBusy} onClick={runSimulation}><Play size={17} fill="currentColor"/>{isBusy?"Checking constraints…":"Run continuity test"}<ArrowRight size={17}/></button>
     </section><section className="panel workflow-setup"><div className="panel-heading"><div><span className="section-tag">DEPENDENCY CONTEXT</span><h3>Operating requirements</h3></div><button className="text-action" onClick={()=>navigate("graph")}>View graph <ArrowRight size={14}/></button></div>
       {snapshot&&<><p className="soft-description">{snapshot.workflow.description}</p><div className="step-chain">{snapshot.steps.map((s,i)=><div className="chain-item" key={s.id}><span className="step-index">{String(i+1).padStart(2,"0")}</span><div className="chain-copy"><strong>{s.name}</strong><small>Skill: {s.skill.replaceAll("-"," ")}</small><span><LockKeyhole size={12}/>{s.permission}</span></div></div>)}</div>
        <div className="constraint"><ShieldCheck size={20}/><div><strong>Separation of duties enforced</strong><p>Approval and execution steps must be assigned to different employees. The solver cannot bypass this constraint.</p></div></div>
        <div className="doc-summary"><span>GOVERNING DECISION</span><p>{snapshot.decision}</p></div></>}
     </section></div>
     <section className="panel result-panel"><div className="panel-heading"><div><span className="section-tag">02 / DIAGNOSE</span><h3>Continuity analysis</h3></div>{simulation&&<Status status={simulation.status}/>}</div>
       {!simulation?<Empty title="No simulation results yet" detail="Choose unavailable team members and run a test to trace policy-safe assignments through the company graph."/>:
       <><div className={`result-head ${simulation.feasible?"result-success":"result-failure"}`}><div className="result-icon">{simulation.feasible?<ShieldCheck size={28}/>:<ShieldX size={28}/>}</div><div><strong>{simulation.feasible?"Workflow remains executable":"Workflow is blocked"}</strong><p>{simulation.explanation}</p><small>{simulation.solver} · {simulation.optimization_proven?"Optimality verified":"Feasible candidate"} · Persistent graph record</small></div></div>
       <div className="result-columns"><div><h4>Constraint findings</h4>{simulation.blockers.length?simulation.blockers.map((b,i)=><div className="finding" key={i}><CircleAlert size={17}/><div><strong>{b.reason.replaceAll("_"," ")}</strong><p>{b.detail}</p></div></div>):<div className="finding good"><CircleCheck size={18}/><div><strong>All constraints satisfied</strong><p>At least one authorized executor assignment respects skills, valid grants and independent duties.</p></div></div>}</div>
       <div><h4>{simulation.feasible?"Valid execution assignments":"Recovery recommendation"}</h4>{simulation.feasible?<div className="assignments">{simulation.assignments.map(a=><div key={a.step_id}><span>{a.step_name}</span><strong>{a.person_name}</strong></div>)}</div>:simulation.repair?<><p className="solution-summary">A policy-compliant assignment exists if the following expired permission grants are reviewed and renewed:</p><div className="renewals">{simulation.repair.renewals.map((r,i)=><div key={i}><Wrench size={16}/><span>Renew <b>{r.permission}</b> for <b>{people.find(p=>p.id===r.person_id)?.name||r.person_id}</b></span></div>)}</div><button disabled={isBusy} className="primary-button" onClick={()=>proposeRepair(simulation.id)}>Create review proposal <ArrowRight size={16}/></button></>:<p className="solution-summary">No approved repair was found. Escalate to the process owner for staffing or policy review.</p>}</div></div>
       {activeRepair&&<div className="inline-repair"><div><strong>Recovery proposal created</strong><p>Review is {activeRepair.status.toLowerCase().replaceAll("_"," ")}. Continue in the recovery queue.</p></div><button className="outline-button" onClick={()=>navigate("repairs")}>Open recovery queue <ArrowRight size={15}/></button></div>}</>}
     </section>
   </>}
   {overview&&view==="graph"&&<><section className="panel graph-panel"><div className="panel-heading"><div><span className="section-tag">GRAPH EXPLORER / FALKORDB</span><h3>Live organizational dependencies</h3></div><div className="select-wrap compact"><select aria-label="Choose workflow" value={selectedWorkflow} onChange={e=>chooseWorkflow(e.target.value)}>{workflows.map(w=><option key={w.id} value={w.id}>{w.name}</option>)}</select><ChevronDown size={15}/></div></div>
       {graph?<GraphCanvas graph={graph}/>:<div className="loading-panel"><div className="spinner"/> Loading graph…</div>}
       {graph&&<div className="graph-legend">{["passage","document","decision","project","workflow","step","skill","permission","person"].map(t=><span key={t}><i className={`legend-${t}`}/>{t}</span>)}<span>{graph.nodes.length} nodes · {graph.edges.length} relations</span></div>}
      </section><div className="support-grid"><section className="panel"><div className="panel-heading"><div><span className="section-tag">PROVENANCE</span><h3>Connected evidence</h3></div><FileText size={18}/></div><div className="evidence-list">{graph?.documents.map(d=><div key={d}><FileText size={16}/><span>{d}</span><Pill>synthetic</Pill></div>)}</div><div className="document-import"><div className="field-label">ATTACH TEXT EVIDENCE</div><form onSubmit={e=>{e.preventDefault();attachDocument()}}><input aria-label="Document title" placeholder="Document title" value={docTitle} onChange={e=>setDocTitle(e.target.value)} maxLength={160} required minLength={3}/><textarea aria-label="Document content" placeholder="Paste a relevant internal process note…" value={docContent} onChange={e=>setDocContent(e.target.value)} maxLength={5000} required minLength={10}/><button className="outline-button" type="submit" disabled={isBusy||docTitle.trim().length<3||docContent.trim().length<10}>Link source to graph <ArrowRight size={14}/></button></form><p>Manually tagged to this workflow. Text is stored in the local demo graph.</p></div></section><section className="panel"><div className="panel-heading"><div><span className="section-tag">GOVERNANCE</span><h3>Controlling decision</h3></div><ShieldCheck size={18}/></div><div className="governance-box"><div className="governance-symbol"><ShieldCheck size={23}/></div><strong>{graph?.decision||"No decision recorded"}</strong><p>Tasks and permissions are validated against recorded graph relationships. Documents are synthetic evidence references.</p></div></section></div>
   </>}
   {overview&&view==="knowledge"&&<KnowledgePanel workflows={workflows} workflowId={selectedWorkflow} focusSourceId={focusSourceId} onWorkflowChange={id=>{setFocusSourceId("");chooseWorkflow(id)}} onChanged={()=>{void api<GraphView>(`/workflows/${selectedWorkflow}/graph`).then(setGraph);}}/>}
   {overview&&view==="repairs"&&<section className="panel queue-panel"><div className="panel-heading"><div><span className="section-tag">REMEDIATION PIPELINE</span><h3>Recovery proposals</h3></div><Pill>{repairs.length} total</Pill></div>
    {repairs.length===0?<Empty title="No recovery proposals yet" detail="Run a blocked scenario in the disruption lab, then create an explicit repair proposal."/>:<div className="repair-list">{repairs.map(r=><div key={r.id} className="repair-item"><div className="repair-top"><div className="repair-icon"><Wrench size={20}/></div><div className="repair-titles"><strong>{workflows.find(w=>w.id===r.workflow_id)?.name||r.workflow_id}</strong><small>Ref {r.id.slice(0,8).toUpperCase()}</small></div><Status status={r.status}/></div>
     <p>{r.description}</p><div className="repair-actions">{r.actions.map((a,i)=><div key={i}><LockKeyhole size={14}/><span>{a.permission} → {people.find(p=>p.id===a.person_id)?.name||a.person_id}</span></div>)}</div>
     <div className="repair-footer"><div className="repair-footnote"><ShieldCheck size={15}/> Existing expired grants only; never creates new access.</div>
       {r.status==="PENDING_APPROVAL"?<button className="primary-button" disabled={isBusy} onClick={()=>approve(r.id)}>Approve sandbox correction <ArrowRight size={15}/></button>:r.status==="APPLIED_PENDING_DRILL"?<button className="primary-button" disabled={isBusy} onClick={()=>drill(r.id)}>Run verification drill <Play size={15}/></button>:<span className="complete-label"><CheckCheck size={17}/> Simulation verified</span>}
     </div></div>)}</div>}
   </section>}
   {overview&&view==="audit"&&<section className="panel queue-panel"><div className="panel-heading"><div><span className="section-tag">SYSTEM EVENT LOG</span><h3>Traceable operational decisions</h3></div><Pill>Latest 50 events</Pill></div>
   {audit.length===0?<Empty title="No recorded events" detail="Running tests and approving sandbox actions produces an auditable graph history."/>:<div className="audit-list">{audit.map((a,i)=><div className="audit-item" key={`${a.entity_id}:${i}`}><div className={`audit-symbol ${a.kind.includes("DRILL")?"green":a.kind.includes("REPAIR")?"orange":"gray"}`}><Activity size={17}/></div><div><div className="audit-label"><strong>{a.kind.replaceAll("_"," ")}</strong><Pill>{a.actor}</Pill></div><p>{a.message}</p><small>Record: {a.entity_id}</small></div></div>)}</div>}</section>}
   <footer className="page-footer"><span>ContinuityOS · Research demonstration</span><span>FalkorDB graph context · Deterministic workflow satisfiability · Synthetic company data</span></footer>
   </div>
  </main>
  <Agent open={assistantOpen} setOpen={setAssistantOpen} workflows={workflows} onOpenCitation={(workflowId,sourceId)=>{setSelectedWorkflow(workflowId);setFocusSourceId(sourceId);setView("knowledge");}}/>
 </div>;
}
