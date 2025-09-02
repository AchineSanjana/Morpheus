import { useCallback, useEffect, useMemo, useState } from "react";
import { saveSleepLog } from "../lib/api";
import { supabase } from "../lib/supabaseClient";

/**
 * Improved usability:
 * - Explicit labels & helper text for accessibility
 * - Inline validation + status feedback instead of alert()
 * - Shows computed sleep duration when both times provided
 * - Prevents submit while saving; error handling
 * - Quick-set buttons for Bedtime / Wake (Now / +7h)
 * - Numeric inputs sanitized; slider for screen time
 */
export function SleepLogForm() {
  const todayIso = useMemo(()=>new Date().toISOString().slice(0,10), []);
  const [date,setDate]=useState<string>(todayIso);
  const [bedtime,setBedtime]=useState<string>("");
  const [wake,setWake]=useState<string>("");
  const [awakenings,setAwaken]=useState<number>(0);
  const [caffeine,setCaffeine]=useState(false);
  const [alcohol,setAlcohol]=useState(false);
  const [screen,setScreen]=useState<number>(0);
  const [notes,setNotes]=useState("");
  const [saving,setSaving]=useState(false);
  const [status,setStatus]=useState<{type:"idle"|"success"|"error";msg?:string}>({type:"idle"});
  const [showAdvanced,setShowAdvanced]=useState(false);
  const [restored,setRestored]=useState(false);

  const DRAFT_KEY = "sleepLogDraft_v1";

  // Restore draft on mount
  useEffect(()=>{
    try {
      const raw = localStorage.getItem(DRAFT_KEY);
      if(!raw) return;
      const draft = JSON.parse(raw);
      // Only offer restore if date matches today or yesterday (still relevant)
      if(draft.date && [todayIso, new Date(Date.now()-86400000).toISOString().slice(0,10)].includes(draft.date)) {
        // ask user implicitly once by setting a status suggesting restore
        setStatus(s=> s.type === "idle" ? {type:"idle", msg:"Draft available — click Restore."} : s);
        (window as any)._sleepDraft = draft; // ephemeral storage for restore action
      }
    } catch {/* ignore */}
  // eslint-disable-next-line react-hooks/exhaustive-deps
  },[]);

  function restoreDraft(){
    try {
      const draft = (window as any)._sleepDraft; if(!draft) return;
      setDate(draft.date||todayIso); setBedtime(draft.bedtime||""); setWake(draft.wake||"");
      setAwaken(draft.awakenings||0); setCaffeine(!!draft.caffeine_after3pm); setAlcohol(!!draft.alcohol); setScreen(draft.screen_time_min||0); setNotes(draft.notes||"");
      setRestored(true); setStatus({type:"success", msg:"Draft restored."});
      delete (window as any)._sleepDraft;
    } catch {}
  }

  // Persist draft (debounced via effect dependencies grouping)
  useEffect(()=>{
    const draft = {date, bedtime, wake, awakenings, caffeine_after3pm: caffeine, alcohol, screen_time_min: screen, notes};
    try { localStorage.setItem(DRAFT_KEY, JSON.stringify(draft)); } catch {}
  },[date,bedtime,wake,awakenings,caffeine,alcohol,screen,notes]);

  const parseDurationH = useCallback(()=>{
    if(!bedtime || !wake) return null;
    // helper: parse a datetime-local value (YYYY-MM-DDTHH:MM) as local Date
    const parseLocal = (s:string)=>{
      const m = s.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/);
      if(!m) return new Date(s);
      const y = +m[1], mo = +m[2]-1, d = +m[3], hh = +m[4], mm = +m[5];
      return new Date(y,mo,d,hh,mm,0,0);
    };
    try {
      const b = parseLocal(bedtime);
      let w = parseLocal(wake);
      if (w.getTime() <= b.getTime()) { // crossed midnight / next day
        w = new Date(w.getTime() + 24*60*60*1000);
      }
      const diffH = (w.getTime()-b.getTime())/3.6e6;
      if (diffH < 0 || diffH > 24) return null;
      return Math.round(diffH*10)/10;
    } catch { return null; }
  },[bedtime,wake]);
  const durationH = parseDurationH();
  const durationLabel = useMemo(()=>{
    if(durationH==null) return null;
    if(durationH < 6) return {text:`${durationH} h (short)`, color:"text-rose-400"};
    if(durationH <= 9) return {text:`${durationH} h (optimal range)`, color:"text-emerald-400"};
    return {text:`${durationH} h (long)`, color:"text-amber-400"};
  },[durationH]);

  function setNowAsBed() {
  const now = new Date();
  const pad=(n:number)=>n.toString().padStart(2,'0');
  setBedtime(`${now.getFullYear()}-${pad(now.getMonth()+1)}-${pad(now.getDate())}T${pad(now.getHours())}:${pad(now.getMinutes())}`);
  }
  function setNowAsWake() {
  const now = new Date();
  const pad=(n:number)=>n.toString().padStart(2,'0');
  setWake(`${now.getFullYear()}-${pad(now.getMonth()+1)}-${pad(now.getDate())}T${pad(now.getHours())}:${pad(now.getMinutes())}`);
  }
  function setWakePlus(hours:number){
  if(!bedtime) return;
  const m = bedtime.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/);
  if(!m) return;
  const y=+m[1], mo=+m[2]-1, d=+m[3], hh=+m[4], mm=+m[5];
  const b = new Date(y,mo,d,hh,mm,0,0);
  const w = new Date(b.getTime()+hours*3600*1000);
  const pad=(n:number)=>n.toString().padStart(2,'0');
  setWake(`${w.getFullYear()}-${pad(w.getMonth()+1)}-${pad(w.getDate())}T${pad(w.getHours())}:${pad(w.getMinutes())}`);
  }

  const canSubmit = !!date && !saving; // we allow partial times – analytics code handles nulls

  async function submit(e:React.FormEvent){
    e.preventDefault();
    setStatus({type:"idle"});
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) {
      setStatus({type:"error", msg:"Please sign in first."});
      return;
    }
    // simple validation (optional times, but if both present ensure sane duration)
    if (bedtime && wake && (durationH == null || durationH < 2 || durationH > 14)) {
      setStatus({type:"error", msg:"Check times — duration looks unrealistic."});
      return;
    }
    try {
      setSaving(true);
      await saveSleepLog({
        date,
        bedtime: bedtime||null,
        wake_time: wake||null,
        awakenings: awakenings||0,
        caffeine_after3pm: caffeine,
        alcohol,
        screen_time_min: screen||0,
        notes: notes||null
      }, session.access_token);
  setStatus({type:"success", msg:"Saved. Ask: analyze my last 7 days."});
      // Optionally keep values; don't clear date. Clear times to avoid duplicate entry.
      setBedtime(""); setWake(""); setAwaken(0); setCaffeine(false); setAlcohol(false); setScreen(0); setNotes("");
  try { localStorage.removeItem(DRAFT_KEY); } catch {}
    } catch (err:any) {
      setStatus({type:"error", msg: err?.message || "Save failed"});
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="relative">
      {/* Background gradient overlay */}
      <div className="absolute inset-0 bg-gradient-to-br from-violet-500/10 via-transparent to-emerald-500/10 rounded-2xl blur-xl"></div>
      
      <form onSubmit={submit} className="relative bg-gradient-to-br from-zinc-900/95 to-zinc-800/95 backdrop-blur-sm border border-zinc-700/50 p-6 rounded-2xl mb-6 space-y-6 shadow-2xl shadow-black/20" aria-describedby="sleep-form-status">
        {/* Header */}
        <div className="flex items-center gap-3 pb-2 border-b border-zinc-700/50">
          <div className="w-8 h-8 bg-gradient-to-br from-violet-500 to-emerald-500 rounded-full flex items-center justify-center text-white text-sm font-bold">💤</div>
          <h2 className="text-lg font-semibold bg-gradient-to-r from-violet-400 to-emerald-400 bg-clip-text text-transparent">Log Last Night</h2>
        </div>

        <div className="grid sm:grid-cols-3 gap-4">
          <label className="flex flex-col gap-2 text-sm group">
            <span className="font-medium text-zinc-200 flex items-center gap-2">
              📅 Date<span className="text-rose-400">*</span>
            </span>
            <input required className="bg-zinc-800/80 border border-zinc-600/50 p-3 rounded-xl transition-all duration-200 focus:border-violet-400 focus:bg-zinc-800 focus:ring-2 focus:ring-violet-400/20 focus:outline-none" type="date" value={date} onChange={e=>setDate(e.target.value)} />
          </label>
          <label className="flex flex-col gap-2 text-sm group sm:col-span-1">
            <span className="font-medium text-zinc-200 flex items-center justify-between">
              <span className="flex items-center gap-2">🌙 Bedtime</span>
              <button type="button" onClick={setNowAsBed} className="text-xs text-emerald-400 hover:text-emerald-300 transition-colors px-2 py-1 rounded-md hover:bg-emerald-400/10">Now</button>
            </span>
            <input className="bg-zinc-800/80 border border-zinc-600/50 p-3 rounded-xl transition-all duration-200 focus:border-violet-400 focus:bg-zinc-800 focus:ring-2 focus:ring-violet-400/20 focus:outline-none" type="datetime-local" value={bedtime} onChange={e=>setBedtime(e.target.value)} />
          </label>
          <label className="flex flex-col gap-2 text-sm group sm:col-span-1">
            <span className="font-medium text-zinc-200 flex items-center justify-between">
              <span className="flex items-center gap-2">☀️ Wake time</span>
              <div className="flex gap-1">
                <button type="button" onClick={setNowAsWake} className="text-xs text-emerald-400 hover:text-emerald-300 transition-colors px-2 py-1 rounded-md hover:bg-emerald-400/10">Now</button>
                {bedtime && <button type="button" onClick={()=>setWakePlus(7)} className="text-xs text-emerald-400 hover:text-emerald-300 transition-colors px-2 py-1 rounded-md hover:bg-emerald-400/10">+7h</button>}
                {bedtime && <button type="button" onClick={()=>setWakePlus(8)} className="text-xs text-emerald-400 hover:text-emerald-300 transition-colors px-2 py-1 rounded-md hover:bg-emerald-400/10">+8h</button>}
              </div>
            </span>
            <input className="bg-zinc-800/80 border border-zinc-600/50 p-3 rounded-xl transition-all duration-200 focus:border-violet-400 focus:bg-zinc-800 focus:ring-2 focus:ring-violet-400/20 focus:outline-none" type="datetime-local" value={wake} onChange={e=>setWake(e.target.value)} />
          </label>
        </div>      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex flex-col xs:flex-row gap-4">
          <label className="flex flex-col gap-2 text-sm w-full max-w-[12rem] group">
            <span className="font-medium text-zinc-200 flex items-center gap-2">🔢 Awakenings</span>
            <input className="bg-zinc-800/80 border border-zinc-600/50 p-3 rounded-xl transition-all duration-200 focus:border-violet-400 focus:bg-zinc-800 focus:ring-2 focus:ring-violet-400/20 focus:outline-none" type="number" min={0} value={awakenings} onChange={e=>setAwaken(parseInt(e.target.value||"0"))} />
          </label>
          {durationLabel && (
            <div className={`text-sm font-medium sm:self-end sm:mb-1 px-3 py-2 rounded-xl bg-zinc-800/50 border border-zinc-600/30 ${durationLabel.color} flex items-center gap-2`}>
              ⏰ {durationLabel.text}
            </div>
          )}
        </div>
        <button type="button" onClick={()=>setShowAdvanced(s=>!s)} className="flex items-center gap-2 text-sm text-emerald-400 hover:text-emerald-300 transition-colors px-3 py-2 rounded-xl hover:bg-emerald-400/10 border border-emerald-400/20">
          {showAdvanced ? "⬆️ Hide" : "⬇️ Show"} lifestyle fields
        </button>
      </div>

      {showAdvanced && (
        <div className="grid sm:grid-cols-3 gap-4 items-end animate-in slide-in-from-top-2 duration-300">
          <label className="flex items-center gap-3 text-sm p-3 rounded-xl bg-zinc-800/50 border border-zinc-600/30 hover:bg-zinc-800/70 transition-colors cursor-pointer" title="Any caffeine (coffee, tea, energy drink) consumed after 3pm?">
            <input type="checkbox" className="h-5 w-5 rounded accent-emerald-500" checked={caffeine} onChange={e=>setCaffeine(e.target.checked)} />
            <span className="text-zinc-200">☕ Caffeine after 3pm</span>
          </label>
          <label className="flex items-center gap-3 text-sm p-3 rounded-xl bg-zinc-800/50 border border-zinc-600/30 hover:bg-zinc-800/70 transition-colors cursor-pointer" title="Alcohol consumed in the evening?">
            <input type="checkbox" className="h-5 w-5 rounded accent-emerald-500" checked={alcohol} onChange={e=>setAlcohol(e.target.checked)} />
            <span className="text-zinc-200">🍷 Alcohol</span>
          </label>
          <div className="text-xs text-zinc-400 sm:col-span-1 flex items-center gap-2">
            💡 These factors help coaching personalize advice.
          </div>
        </div>
      )}

      <div className="space-y-3">
        <label className="flex flex-col gap-3 text-sm w-full group">
          <div className="flex items-center justify-between">
            <span className="font-medium text-zinc-200 flex items-center gap-2">📱 Screen time before bed</span>
            <span className="text-sm font-medium text-emerald-400 bg-emerald-400/10 px-3 py-1 rounded-full">{screen} min</span>
          </div>
          <div className="relative">
            <input 
              aria-label="Screen time before bed in minutes" 
              type="range" 
              min={0} 
              max={240} 
              step={5} 
              value={screen} 
              onChange={e=>setScreen(parseInt(e.target.value||"0"))} 
              className="w-full h-2 bg-zinc-700 rounded-lg appearance-none cursor-pointer slider touch-pan-x
                         [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:h-5 [&::-webkit-slider-thumb]:w-5 
                         [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-gradient-to-r [&::-webkit-slider-thumb]:from-violet-500 [&::-webkit-slider-thumb]:to-emerald-500
                         [&::-webkit-slider-thumb]:cursor-pointer [&::-webkit-slider-thumb]:shadow-lg [&::-webkit-slider-thumb]:transition-transform
                         [&::-webkit-slider-thumb]:hover:scale-110 [&::-moz-range-thumb]:h-5 [&::-moz-range-thumb]:w-5 
                         [&::-moz-range-thumb]:rounded-full [&::-moz-range-thumb]:bg-gradient-to-r [&::-moz-range-thumb]:from-violet-500 [&::-moz-range-thumb]:to-emerald-500
                         [&::-moz-range-thumb]:cursor-pointer [&::-moz-range-thumb]:border-0" 
            />
            <div className="absolute top-3 left-0 right-0 flex justify-between text-xs text-zinc-500 pointer-events-none">
              <span>0</span>
              <span>60</span>
              <span>120</span>
              <span>240</span>
            </div>
          </div>
        </label>
        {screen > 90 && (
          <div className="flex items-start gap-2 p-3 bg-amber-500/10 border border-amber-500/20 rounded-xl">
            <span className="text-amber-400">⚠️</span>
            <p className="text-xs text-amber-300 leading-relaxed">Consider reducing screen exposure &gt;90 min before bed for better sleep quality.</p>
          </div>
        )}
      </div>

      <label className="flex flex-col gap-3 text-sm group">
        <span className="font-medium text-zinc-200 flex items-center gap-2">
          📝 Notes <span className="text-xs text-zinc-500 font-normal">(optional)</span>
        </span>
        <textarea 
          rows={3} 
          className="bg-zinc-800/80 border border-zinc-600/50 p-3 rounded-xl resize-y transition-all duration-200 focus:border-violet-400 focus:bg-zinc-800 focus:ring-2 focus:ring-violet-400/20 focus:outline-none" 
          value={notes} 
          onChange={e=>setNotes(e.target.value)} 
          placeholder="Illness, stressors, naps, exercise, etc." 
        />
      </label>

      {/* Duration moved near awakenings with classification */}

      <div className="flex flex-wrap items-center gap-3 pt-2">
        <button 
          disabled={!canSubmit} 
          className="bg-gradient-to-r from-violet-600 to-emerald-600 disabled:from-zinc-600 disabled:to-zinc-600 disabled:cursor-not-allowed hover:from-violet-500 hover:to-emerald-500 px-6 py-3 rounded-xl text-sm font-medium transition-all duration-200 shadow-lg hover:shadow-xl disabled:shadow-none transform hover:scale-105 disabled:scale-100 flex items-center gap-2"
        >
          {saving ? (
            <>
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
              Saving...
            </>
          ) : (
            <>
              💾 Save night
            </>
          )}
        </button>
        <button 
          type="button" 
          onClick={()=>{setBedtime("");setWake("");setAwaken(0);setCaffeine(false);setAlcohol(false);setScreen(0);setNotes("");setStatus({type:"idle"});}} 
          className="text-sm text-zinc-400 hover:text-zinc-200 px-3 py-2 rounded-xl hover:bg-zinc-700/50 transition-all duration-200"
        >
          🔄 Reset
        </button>
        {status.type === "idle" && (window as any)._sleepDraft && !restored && (
          <button 
            type="button" 
            onClick={restoreDraft} 
            className="text-sm text-emerald-400 hover:text-emerald-300 px-3 py-2 rounded-xl hover:bg-emerald-400/10 transition-all duration-200 border border-emerald-400/20"
          >
            📋 Restore draft
          </button>
        )}
        <div id="sleep-form-status" aria-live="polite" className="text-sm font-medium">
          {status.type === "success" && (
            <div className="flex items-center gap-2 text-emerald-400 bg-emerald-400/10 px-3 py-2 rounded-xl border border-emerald-400/20">
              ✅ {status.msg}
            </div>
          )}
          {status.type === "error" && (
            <div className="flex items-center gap-2 text-rose-400 bg-rose-400/10 px-3 py-2 rounded-xl border border-rose-400/20">
              ❌ {status.msg}
            </div>
          )}
        </div>
      </div>
    </form>
    </div>
  );
}