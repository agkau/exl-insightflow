/** Pure format and arithmetic helpers shared by the application and tests. */
export const fmt=(n)=>Number(n||0).toLocaleString('en-IN',{maximumFractionDigits:0});
export const pct=(n,d=1)=>(100*(Number(n)||0)).toFixed(d)+'%';
export const money=(n)=>{const abs=Math.abs(n);return (n<0?'-':'')+'₹'+(abs>=1e7?(abs/1e7).toFixed(2)+' Cr':abs>=1e5?(abs/1e5).toFixed(1)+' L':abs>=1e3?(abs/1e3).toFixed(0)+' K':fmt(abs));};
export const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));export const sum=(a,k)=>a.reduce((p,x)=>p+Number(x[k]||0),0);export const ratio=(a,b)=>b?a/b:0;
export const dateMinus=(ds,n)=>{const d=new Date(ds+'T00:00:00Z');d.setUTCDate(d.getUTCDate()-n);return d.toISOString().slice(0,10)};
export const pdelta=(v,b,direction=1)=>(v-b)*100*direction;export const fpp=(v)=>((v>=0?'+':'')+v.toFixed(1)+' pp');
