import React,{useState} from "react";
import {createRoot} from "react-dom/client";
import "./style.css";

function App(){
 const [q,setQ]=useState(""),[msgs,setMsgs]=useState([]);
 const ask=async()=>{
  if(!q.trim())return;
  const user=q;setQ("");setMsgs(m=>[...m,{role:"user",text:user}]);
  const r=await fetch((import.meta.env.VITE_API_URL||"http://localhost:8000")+"/api/chat",
   {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message:user})});
  const d=await r.json();setMsgs(m=>[...m,{role:"ai",text:d.answer,intent:d.intent}]);
 };
 return <div className="app">
  <aside><div className="brand">✦ Jain AI</div><p className="tag">Explore. Understand. Connect.</p>
   <div className="nav">◉ New conversation<br/>◇ Jain concepts<br/>◇ Stories & history<br/>◇ Scriptures<br/>◇ Places & temples</div>
   <div className="bottom">Built for the next generation of Jain learners.</div>
  </aside>
  <main><header><div><h1>Discover Jainism</h1><p>Ask anything. Learn with clarity.</p></div><div className="pill">AI Knowledge Guide</div></header>
   <section className="chat">{msgs.length===0?<div className="hero"><div className="orb">✦</div>
    <h2>What would you like to discover?</h2><p>Ask about Tirthankaras, Jain philosophy, scriptures, places, stories, stavan and more.</p>
    <div className="suggestions">{["Why is Mahavira important?","Explain Anekantavada simply","Tell me about Shatrunjaya","What is Navkar Mantra?"].map(x=><button onClick={()=>setQ(x)}>{x}</button>)}</div>
   </div>:msgs.map((m,i)=><div className={"msg "+m.role} key={i}><div className="avatar">{m.role==="ai"?"✦":"You"}</div><div><div className="bubble">{m.text}</div>{m.intent&&<small>Jain AI • {m.intent.replaceAll("_"," ")}</small>}</div></div>)}</section>
   <div className="composer"><textarea value={q} onChange={e=>setQ(e.target.value)} onKeyDown={e=>{if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();ask()}}} placeholder="Ask anything about Jainism..."/><button onClick={ask}>↑</button></div>
   <footer>AI can make mistakes. Verify important details with approved Jain sources.</footer>
  </main>
 </div>
}
createRoot(document.getElementById("root")).render(<App/>);
