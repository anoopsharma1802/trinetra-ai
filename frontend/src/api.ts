const API=import.meta.env.VITE_API_BASE_URL||'http://localhost:8000/api/v1';

const get=async(p:string)=>{
  const r=await fetch(API+p);
  if(!r.ok) throw Error(String(r.status));
  return r.json();
};

export const api={
  cameras:()=>get('/cameras'),
  events:()=>get('/vehicles/events'),
  analytics:()=>get('/analytics/summary'),
  alerts:()=>get('/alerts'),
  trajectory:(plate:string)=>get(`/vehicles/${plate}/trajectory`)
};
