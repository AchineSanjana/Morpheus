import { useState } from "react";
import { saveSleepLog } from "../lib/api";
import { supabase } from "../lib/supabaseClient";

export function SleepLogForm() {
  const [date,setDate]=useState<string>(new Date().toISOString().slice(0,10));
  const [bedtime,setBedtime]=useState<string>(""); const [wake,setWake]=useState<string>("");
  const [awakenings,setAwaken]=useState<number>(0); const [caffeine,setCaffeine]=useState(false);
  const [alcohol,setAlcohol]=useState(false); const [screen,setScreen]=useState<number>(0);
  const [notes,setNotes]=useState("");
  async function submit(e:React.FormEvent){
    e.preventDefault();
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) return alert("Sign in first.");
    await saveSleepLog({
      date, bedtime: bedtime||null, wake_time: wake||null,
      awakenings, caffeine_after3pm: caffeine, alcohol,
      screen_time_min: screen, notes: notes||null
    }, session.access_token);
    alert("Saved! Ask me to analyze your last 7 days.");
  }
  return (
    <form onSubmit={submit} className="bg-zinc-900 p-3 rounded mb-3 grid grid-cols-2 gap-2">
      <input className="bg-zinc-800 p-2 rounded" type="date" value={date} onChange={e=>setDate(e.target.value)} />
      <input className="bg-zinc-800 p-2 rounded" type="datetime-local" value={bedtime} onChange={e=>setBedtime(e.target.value)} placeholder="Bedtime" />
      <input className="bg-zinc-800 p-2 rounded" type="datetime-local" value={wake} onChange={e=>setWake(e.target.value)} placeholder="Wake time" />
      <input className="bg-zinc-800 p-2 rounded" type="number" value={awakenings} onChange={e=>setAwaken(parseInt(e.target.value||"0"))} placeholder="# awakenings" />
      <label className="flex items-center gap-2"><input type="checkbox" checked={caffeine} onChange={e=>setCaffeine(e.target.checked)} /> Caffeine after 3pm</label>
      <label className="flex items-center gap-2"><input type="checkbox" checked={alcohol} onChange={e=>setAlcohol(e.target.checked)} /> Alcohol</label>
      <input className="bg-zinc-800 p-2 rounded" type="number" value={screen} onChange={e=>setScreen(parseInt(e.target.value||"0"))} placeholder="Screen time (min)" />
      <textarea className="col-span-2 bg-zinc-800 p-2 rounded" value={notes} onChange={e=>setNotes(e.target.value)} placeholder="notes..." />
      <button className="col-span-2 bg-emerald-600 hover:bg-emerald-500 p-2 rounded">Save last night</button>
    </form>
  );
}
