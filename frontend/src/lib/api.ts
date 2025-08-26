export async function streamChat(message: string, token: string, onChunk:(t:string)=>void) {
  const api = import.meta.env.VITE_API_URL as string;
  const res = await fetch(`${api}/chat/stream`, {
    method:"POST",
    headers:{ "Content-Type":"application/json", "Authorization":`Bearer ${token}` },
    body: JSON.stringify({ message })
  });
  if (!res.ok || !res.body) throw new Error("chat stream failed");
  const reader = res.body.getReader(); const dec = new TextDecoder();
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    onChunk(dec.decode(value));
  }
}
export async function saveSleepLog(payload:any, token:string) {
  const api = import.meta.env.VITE_API_URL as string;
  const res = await fetch(`${api}/sleep-log`, {
    method:"POST",
    headers:{ "Content-Type":"application/json", "Authorization":`Bearer ${token}` },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error("sleep log failed");
}
