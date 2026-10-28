/* Optional Firebase private cloud saves for FC27 Hub */
(()=>{
"use strict";
const K="fc27hub.v1", I="fc27hub.dismissed.v2", C="fc27hub.firebase.config", M="fc27hub.firebase.meta";
const read=k=>{try{return JSON.parse(localStorage.getItem(k)||"null")}catch{return null}};
const snapshot=()=>({state:read(K),ignored:read(I)||[]});
const digest=()=>JSON.stringify(snapshot());
let cfg=read(C),auth=null,db=null,user=null,remote=null,revision=0,automatic=false,busy=false,lastSaved="",status="Local browser only";
const msg=s=>{status=s;const n=document.querySelector("#fc27-cloud-status");if(n)n.textContent=s};
const ref=()=>db.collection("fc27_progress").doc(user.uid);
const valid=c=>!!(c&&/^AIza[\w-]+$/.test(c.apiKey||"")&&c.authDomain&&c.projectId&&c.appId);
function createPanel(){
 let p=document.getElementById("fc27-cloud-panel");
 if(!p){p=document.createElement("div");p.id="fc27-cloud-panel";document.body.append(p)}
 p.hidden=false;
 const head='<header><strong>☁ FC27 Cloud Backup</strong><button data-cloud="close">✕</button></header><p id="fc27-cloud-status"></p>';
 let body;
 if(!valid(cfg))body='<p>Paste your Firebase web app public configuration. Do not paste service-account or admin keys.</p><textarea id="fc27-cloud-config" rows="7" placeholder="Firebase web config JSON"></textarea><button data-cloud="connect">Connect project</button>';
 else if(!user)body='<p>Project: '+esc(cfg.projectId)+'</p><input id="fc27-cloud-email" type="email" placeholder="Email address"><input id="fc27-cloud-password" type="password" placeholder="Password"><button data-cloud="login">Sign in</button> <button data-cloud="signup">Create account</button><p><button data-cloud="change">Change project</button></p>';
 else body='<p>Signed in: '+esc(user.email)+'<br>Cloud revision: '+revision+'</p><button data-cloud="backup">Back up this device</button> <button data-cloud="restore" '+(remote?"":"disabled")+'>Restore cloud</button> <button data-cloud="compare">Compare versions</button> <button data-cloud="logout">Sign out</button><p><small>After a confirmed backup or restore, edits automatically sync while online. Conflicts stop synchronization instead of overwriting newer data.</small></p>';
 p.innerHTML='<section>'+head+body+'<p><small>Data always saves locally. Export JSON from Settings before switching devices or restoring a cloud copy.</small></p></section>';
 msg(status)
}
const esc=x=>String(x||"").replace(/[&<>"]/g,ch=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[ch]));
function saveMeta(){localStorage.setItem(M,JSON.stringify({project:cfg.projectId,user:user.uid,revision,hash:digest()}))}
async function check(){
 if(!user)return;
 automatic=false;
 try{const snap=await ref().get({source:"server"});remote=snap.exists?snap.data():null;revision=remote?.revision||0;
 const m=read(M);automatic=!!(m&&m.project===cfg.projectId&&m.user===user.uid&&m.revision===revision&&m.hash===digest());
 lastSaved=automatic?digest():"";
 msg(remote?"Cloud revision "+revision+". "+(automatic?"Automatic saving active.":"Select a cloud copy to restore or back up this device."):"No cloud backup yet. Back up this device to start.");createPanel()
 }catch(e){msg("Cloud read failed: "+e.message);createPanel()}
}
async function save(force=false){
 if(!user||busy)return;
 const data=snapshot();
 if(!data.state||data.state.schema!==1||!Array.isArray(data.state.groups)||!Array.isArray(data.state.logs)){msg("No valid local tracker progress to save");return}
 if(force&&remote&&!confirm("Replace your cloud backup with THIS device's progress? Export a JSON backup first."))return;
 if(!force&&!automatic)return;
 busy=true;
 try{const next=await db.runTransaction(async tx=>{
 const doc=ref(),now=await tx.get(doc),old=now.exists?now.data():null;
 if((old?.revision||0)!==revision)throw Error("Cloud conflict detected. Compare before choosing which copy to keep.");
 tx.set(doc,{owner:user.uid,revision:revision+1,payload:data,updatedAt:firebase.firestore.FieldValue.serverTimestamp()});
 return revision+1});
 revision=next;remote={revision:next,payload:data};automatic=true;lastSaved=digest();saveMeta();msg("CLOUD SAVED • revision "+revision);createPanel();
 }catch(e){automatic=false;msg("Cloud sync stopped: "+e.message+" • local progress retained");createPanel()}finally{busy=false}
}
function restore(){
 if(!remote?.payload?.state){msg("Cloud backup missing valid progress");return}
 if(!confirm("Replace this browser's progress with its cloud backup? Export a JSON backup first."))return;
 localStorage.setItem(K,JSON.stringify(remote.payload.state));
 localStorage.setItem(I,JSON.stringify(remote.payload.ignored||[]));
 automatic=true;lastSaved=digest();saveMeta();location.reload()
}
function script(src){return new Promise((ok,bad)=>{const t=document.createElement("script");t.src=src;t.onload=ok;t.onerror=()=>bad(Error("Firebase library unavailable"));document.head.appendChild(t)})}
async function init(){
 if(!valid(cfg)){msg("Configure Firebase project to enable cloud backup.");return}
 try{
 const base="https://www.gstatic.com/firebasejs/10.14.1/";
 if(!window.firebase){await script(base+"firebase-app-compat.js");await script(base+"firebase-auth-compat.js");await script(base+"firebase-firestore-compat.js")}
 const app=firebase.apps.find(a=>a.name==="fc27-hub")||firebase.initializeApp(cfg,"fc27-hub");
 auth=app.auth();db=app.firestore();
 auth.onAuthStateChanged(async u=>{user=u;automatic=false;remote=null;revision=0;if(u)await check();else{msg("Signed out. Browser progress retained.");createPanel()}});
 }catch(e){msg("Firebase connection failed: "+e.message)}
}
document.addEventListener("DOMContentLoaded",()=>{
 const css=document.createElement("style");
 css.textContent='#fc27-cloud-launch{border:1px solid #48654a;background:#21372a;color:#c4fb65;padding:9px;border-radius:9px;cursor:pointer;font-weight:800}#fc27-cloud-panel{position:fixed;inset:0;z-index:9999;display:grid;place-items:center;background:#000b;padding:15px}#fc27-cloud-panel[hidden]{display:none}#fc27-cloud-panel section{max-height:90vh;overflow:auto;width:min(550px,100%);background:#142022;border:1px solid #456349;border-radius:15px;padding:22px;color:#e8f5ec;box-shadow:0 15px 60px #0009}#fc27-cloud-panel header{display:flex;justify-content:space-between;align-items:center;font-size:20px}#fc27-cloud-panel button{border:0;border-radius:7px;background:#c4fb65;color:#111e17;cursor:pointer;font-weight:bold;padding:9px 12px;margin:4px}#fc27-cloud-panel button:disabled{opacity:.4;cursor:default}#fc27-cloud-panel input,#fc27-cloud-panel textarea{display:block;width:100%;background:#091315;color:white;border:1px solid #456349;border-radius:7px;padding:10px;margin:10px 0;font:inherit}#fc27-cloud-status{color:#d0edb8;background:#203727;padding:9px;border-radius:8px}';
 document.head.append(css);
 const btn=document.createElement("button");btn.id="fc27-cloud-launch";btn.textContent="☁ Cloud";(document.querySelector(".top-actions")||document.body).prepend(btn);
 btn.onclick=()=>createPanel();
 document.addEventListener("click",async e=>{
 const action=e.target.dataset.cloud;if(!action)return;
 if(action==="close"){document.getElementById("fc27-cloud-panel").hidden=true;return}
 if(action==="connect"){try{const c=JSON.parse(document.querySelector("#fc27-cloud-config").value);if(!valid(c))throw Error("Incomplete public Firebase config");localStorage.setItem(C,JSON.stringify(c));location.reload()}catch(err){msg(err.message)}return}
 if(action==="change"){if(confirm("Change Firebase project? Local progress stays saved.")){localStorage.removeItem(C);location.reload()}return}
 if(action==="login"||action==="signup"){const email=document.querySelector("#fc27-cloud-email").value.trim(),password=document.querySelector("#fc27-cloud-password").value;try{msg("Connecting to Firebase…");if(action==="signup")await auth.createUserWithEmailAndPassword(email,password);else await auth.signInWithEmailAndPassword(email,password)}catch(err){msg(err.message)}return}
 if(action==="backup")await save(true);
 if(action==="restore")restore();
 if(action==="compare")await check();
 if(action==="logout")await auth.signOut();
 });
 setInterval(()=>{if(automatic&&user&&!busy&&navigator.onLine&&lastSaved!==digest())save(false)},5000);
 init()
})
})();