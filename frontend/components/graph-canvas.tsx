"use client";
import { useMemo, useState } from "react";
import type { GraphView } from "@/lib/api";
const columns=["passage","document","decision","project","workflow","step","skill","permission","person"];
const palette:Record<string,string>={passage:"#56818b",document:"#9a9571",project:"#5b7087",decision:"#946b72",workflow:"#1d544c",step:"#3b5c86",skill:"#a27035",permission:"#825f95",person:"#59756a"};
export default function GraphCanvas({graph}:{graph:GraphView}){
 const [selected,setSelected]=useState<string|null>(null);
 const layout=useMemo(()=>{
   const byType=columns.map(c=>graph.nodes.filter(n=>n.type===c));
   const positions:Record<string,{x:number;y:number}>={};
   byType.forEach((items,i)=>items.forEach((n,j)=>positions[n.id]={x:35+i*240,y:78+j*64}));
   const height=Math.max(470,...byType.map(items=>120+items.length*64));
   return {byType,positions,height};
 },[graph]);
 const related=new Set(graph.edges.filter(e=>e.source===selected||e.target===selected).flatMap(e=>[e.source,e.target]));
 return <div className="graph-scroller"><svg width={columns.length*240+50} height={layout.height} viewBox={`0 0 ${columns.length*240+50} ${layout.height}`} role="img" aria-label="Interactive workflow knowledge graph">
 {columns.map((t,i)=><text key={t} x={35+i*240} y="34" className="graph-column-title">{t.toUpperCase()}</text>)}
 {graph.edges.map((e,i)=>{const a=layout.positions[e.source],b=layout.positions[e.target];if(!a||!b)return null;
  const path=`M ${a.x+192} ${a.y+18} C ${a.x+222} ${a.y+18}, ${b.x-28} ${b.y+18}, ${b.x} ${b.y+18}`;
  return <path key={i} d={path} fill="none" stroke={e.label==="SEPARATE_FROM"?"#c88459":selected?(related.has(e.source)&&related.has(e.target)?"#3b8c7a":"#dce3e0"):"#b5c8c1"} strokeWidth={selected&&related.has(e.source)&&related.has(e.target)?2.8:1.2} opacity={selected&&!related.has(e.source)?0.35:0.9}/>})}
 {graph.nodes.map(n=>{const p=layout.positions[n.id];if(!p)return null;const active=selected===n.id;return <g key={n.id} onClick={()=>setSelected(active?null:n.id)} role="button" tabIndex={0} onKeyDown={e=>{if(e.key==="Enter"||e.key===" ")setSelected(active?null:n.id)}} style={{cursor:"pointer"}}>
 <rect x={p.x} y={p.y} rx="8" width="192" height="36" fill={active?"#e6f4ee":"#fff"} stroke={active?"#23745f":"#dfe6e1"} strokeWidth={active?2:1}/>
 <rect x={p.x} y={p.y+6} height="24" width="4" rx="2" fill={palette[n.type]}/>
 <text x={p.x+12} y={p.y+22} fill="#273e38" fontSize="11.5" fontWeight={active?700:500}>{n.label.length>25?n.label.slice(0,23)+"…":n.label}</text>
 <title>{n.label} ({n.type})</title></g>})}
 </svg><div className="graph-tip">Click a node to highlight its direct relationships · Scroll horizontally to explore</div></div>;
}
