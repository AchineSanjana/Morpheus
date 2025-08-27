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
type SleepLogPayload = {
  // Define the expected fields for the sleep log payload
  // Example:
  // date: string;
  // duration: number;
  // quality: string;
  [key: string]: unknown; // Replace or extend with actual fields
};

export async function saveSleepLog(payload: SleepLogPayload, token: string) {
  const api = import.meta.env.VITE_API_URL as string;
  const res = await fetch(`${api}/sleep-log`, {
    method:"POST",
    headers:{ "Content-Type":"application/json", "Authorization":`Bearer ${token}` },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error("sleep log failed");
}

type Message = {
  id: string;
  text: string;
  createdAt: string;
  // add other fields as needed
};

export async function fetchMessages(token: string, opts?: { limit?: number; before?: string; after?: string }) {
  const api = import.meta.env.VITE_API_URL as string;
  const params = new URLSearchParams();
  if (opts?.limit) params.set("limit", String(opts.limit));
  if (opts?.before) params.set("before", opts.before);
  if (opts?.after) params.set("after", opts.after);
  const res = await fetch(`${api}/messages?${params.toString()}`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  if (!res.ok) throw new Error("failed to fetch messages");
  return res.json() as Promise<{ messages: Message[]; count: number }>;
}
