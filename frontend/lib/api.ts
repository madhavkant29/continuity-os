const BASE = "";
export type Workflow = {id:string;name:string;department:string;criticality:string;description:string;step_count:number};
export type Person = {id:string;name:string;team:string;role:string;active?:boolean;skills?:string[];permissions?:Record<string,string>};
export type Step = {id:string;short_id:string;name:string;position:number;skill:string;permission:string};
export type Snapshot={workflow:Workflow;steps:Step[];separation:string[][];people:Person[];documents:string[];decision:string};
export type Assignment={step_id:string;step_name:string;person_id:string;person_name:string};
export type Renewal={person_id:string;permission:string;type:string;cost:number};
export type Solution={feasible:boolean;assignments:Assignment[];renewals:Renewal[];blockers:{step_id:string|null;reason:string;detail:string}[];mode:string;solver:string;optimization_proven:boolean};
export type Simulation=Solution&{id:string;workflow_id:string;workflow_name:string;status:"BLOCKED"|"FEASIBLE";unavailable:string[];repair:Solution|null;explanation:string};
export type Repair={id:string;simulation_id:string;workflow_id:string;status:"PENDING_APPROVAL"|"APPLIED_PENDING_DRILL"|"VERIFIED";actions:Renewal[];expected_assignments:Assignment[];description:string;approved_by?:string;last_drill_id?:string};
export type Audit={kind:string;message:string;actor:string;entity_id:string};
export type Overview={organization:string;employees:number;teams:number;workflows:Workflow[];simulations:Simulation[];repairs:Repair[];blocked_simulations:number;open_repairs:number};
export type GraphView={nodes:{id:string;label:string;type:string}[];edges:{source:string;target:string;label:string}[];documents:string[];decision:string};
export type KnowledgeSource={id:string;kind:"DOCUMENT"|"TICKET"|"CONVERSATION";title:string;reference:string;review_status:string;current:boolean;passage_count:number;excerpt:string};
export type Passage={id:string;locator:string;line:number;quote:string};
export type SourceDetail=KnowledgeSource&{workflow_id:string;content:string;passages:Passage[]};
export type AgentResponse={tool:string;answer:string;sources:{type:string;id:string;label:string;passage_id?:string;locator?:string;quote?:string;review_status?:string}[];trace:{step:string;detail:string}[];disclaimer:string};

export async function api<T>(path:string, opts?:{method?:string;body?:unknown;headers?:Record<string,string>}):Promise<T>{
  let r:Response;
  try {
    r=await fetch(`${BASE}/api${path}`, {method:opts?.method||"GET",headers:{...(opts?.body?{"Content-Type":"application/json"}:{}),...(opts?.headers||{})},
      body:opts?.body?JSON.stringify(opts.body):undefined, cache:"no-store"});
  } catch { throw new Error("Server unavailable. Please retry or contact your administrator."); }
  if(!r.ok){let d:unknown;try{d=await r.json()}catch{}
    throw new Error(typeof d==="object" && d!==null && "detail" in d ? String((d as {detail:string}).detail) : `Request failed (${r.status})`);
  }
  return r.json();
}
