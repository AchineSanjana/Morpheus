const API_URL = import.meta.env.VITE_API_URL;

// Stream chat messages from the server
export async function streamChat(
  message: string,
  token: string,
  onChunk: (chunk: string, responsibleAIData?: any, data?: any) => void,
  conversationId?: string | null
) {
  const api = import.meta.env.VITE_API_URL as string;
  const res = await fetch(`${api}/chat/stream`, {
    method:"POST",
    headers:{ "Content-Type":"application/json", "Authorization":`Bearer ${token}` },
    body: JSON.stringify({ message, conversation_id: conversationId ?? undefined })
  });
  if (!res.ok || !res.body) throw new Error("chat stream failed");
  
  const reader = res.body.getReader(); 
  const dec = new TextDecoder();
  let buffer = "";
  
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    
    buffer += dec.decode(value, { stream: true });
    
    // Look for complete JSON objects or plain text lines in the buffer
    let newlineIndex;
    while ((newlineIndex = buffer.indexOf('\n')) !== -1) {
      const raw = buffer.slice(0, newlineIndex);
      buffer = buffer.slice(newlineIndex + 1);
      const line = raw.trim();
      try {
        // Try to parse as JSON for structured responses
        const parsed = JSON.parse(line);
        // Build a structured meta object for responsible AI
        const rai = (parsed && typeof parsed === 'object') ? {
          responsibleAIChecks: parsed.responsible_ai_checks,
          responsibleAIPassed: parsed.responsible_ai_passed,
          responsibleAIRiskLevel: parsed.responsible_ai_risk_level,
        } : undefined;
        // Pass through metadata even if text is empty
        onChunk(parsed.text || "", rai, parsed.data);
      } catch {
        if (line) {
          // If not JSON, treat as plain text and preserve newline
          onChunk(line + '\n');
        }
      }
    }
  }
  
  // Handle any remaining buffer content
  if (buffer.trim()) {
    try {
      const parsed = JSON.parse(buffer);
      const rai = (parsed && typeof parsed === 'object') ? {
        responsibleAIChecks: parsed.responsible_ai_checks,
        responsibleAIPassed: parsed.responsible_ai_passed,
        responsibleAIRiskLevel: parsed.responsible_ai_risk_level,
      } : undefined;
      onChunk(parsed.text || "", rai, parsed.data);
    } catch {
      onChunk(buffer + '\n');
    }
  }
}

// Small helper error type for richer diagnostics in UI
class HttpError extends Error {
  status: number;
  body: string;
  constructor(status: number, body: string, message?: string) {
    super(message || `HTTP ${status}`);
    this.name = "HttpError";
    this.status = status;
    this.body = body;
  }
}
// Mirrors backend/app/schemas.py SleepLogIn
export type SleepLogPayload = {
  date: string; // YYYY-MM-DD
  bedtime: string | null; // ISO datetime or null
  wake_time: string | null; // ISO datetime or null
  awakenings: number; // integer >=0
  caffeine_after3pm: boolean;
  alcohol: boolean;
  screen_time_min: number; // minutes 0-? (UI caps at 240)
  notes: string | null;
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
  if (!res.ok) {
    const text = await safeReadText(res);
    throw new HttpError(res.status, text, `Failed to fetch messages (${res.status}): ${text || res.statusText}`);
  }
  return res.json() as Promise<{ messages: Message[]; count: number }>;
}

// Conversations API
export type Conversation = { id: string; title: string; created_at: string; updated_at: string };

export async function listConversations(token: string): Promise<Conversation[]> {
  const api = import.meta.env.VITE_API_URL as string;
  const res = await fetch(`${api}/conversations`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  if (!res.ok) {
    const text = await safeReadText(res);
    throw new HttpError(res.status, text, `Failed to fetch conversations (${res.status}): ${text || res.statusText}`);
  }
  const data = await res.json();
  return (data?.conversations ?? []) as Conversation[];
}

export async function getConversationMessages(token: string, conversationId: string) {
  const api = import.meta.env.VITE_API_URL as string;
  const res = await fetch(`${api}/conversations/${conversationId}`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  if (!res.ok) {
    const text = await safeReadText(res);
    throw new HttpError(res.status, text, `Failed to fetch conversation (${res.status}): ${text || res.statusText}`);
  }
  return res.json() as Promise<{ messages: { role: 'user'|'assistant'; agent: string; content: string; created_at: string }[] }>; 
}

export async function renameConversation(token: string, conversationId: string, title: string) {
  const api = import.meta.env.VITE_API_URL as string;
  const res = await fetch(`${api}/conversations/${conversationId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify({ title })
  });
  if (!res.ok) {
    const text = await safeReadText(res);
    throw new HttpError(res.status, text, `Failed to rename conversation (${res.status}): ${text || res.statusText}`);
  }
  return res.json();
}

export async function deleteConversation(token: string, id: string) {
  const res = await fetch(`${API_URL}/conversations/${id}`, {
    method: 'DELETE',
    headers: { 'Authorization': `Bearer ${token}` }
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ message: 'Failed to delete' }));
    throw new HttpError(res.status, body);
  }
  return await res.json();
}

export async function recoverConversations(token: string) {
  const res = await fetch(`${API_URL}/conversations/recover`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` }
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ message: 'Failed to recover conversations' }));
    throw new HttpError(res.status, body);
  }
  return await res.json();
}

// Profile management types and functions
export type ProfileData = {
  id: string;
  full_name: string | null;
  username: string | null;
  avatar_url: string | null;
  created_at: string;
  updated_at: string;
};

export async function fetchProfile(userId: string, token: string): Promise<ProfileData | null> {
  try {
    const api = import.meta.env.VITE_API_URL as string;
    const res = await fetch(`${api}/profile/${userId}`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    if (!res.ok) {
      if (res.status === 404) return null;
      const errorText = await res.text();
      throw new Error(`Failed to fetch profile: ${errorText}`);
    }
    return await res.json() as ProfileData;
  } catch (error) {
    console.error("Error fetching profile:", error);
    return null;
  }
}

export async function updateProfile(userId: string, updates: Partial<ProfileData>, token: string): Promise<ProfileData> {
  const api = import.meta.env.VITE_API_URL as string;
  const res = await fetch(`${api}/profile/${userId}`, {
    method: "PUT",
    headers: { 
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}` 
    },
    body: JSON.stringify(updates)
  });
  
  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(`Failed to update profile: ${errorText}`);
  }
  
  return await res.json() as ProfileData;
}

export async function uploadAvatar(file: File, userId: string, token: string): Promise<string> {
  // Validate file on client side
  if (!file.type.startsWith('image/')) {
    throw new Error("Please select an image file.");
  }
  
  if (file.size > 5 * 1024 * 1024) {
    throw new Error("File size must be less than 5MB.");
  }

  const formData = new FormData();
  formData.append("avatar", file);
  
  const api = import.meta.env.VITE_API_URL as string;
  const res = await fetch(`${api}/profile/${userId}/avatar`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: formData
  });
  
  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(`Failed to upload avatar: ${errorText}`);
  }
  
  const data = await res.json() as { avatar_url: string };
  return data.avatar_url;
}

// Utility: safely read response text without throwing
async function safeReadText(res: Response): Promise<string> {
  try {
    return await res.text();
  } catch {
    return "";
  }
}
