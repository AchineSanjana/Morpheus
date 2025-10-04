export async function streamChat(
  message: string, 
  token: string, 
  onChunk: (chunk: string, responsibleAIData?: any, data?: any) => void
) {
  const api = import.meta.env.VITE_API_URL as string;
  const res = await fetch(`${api}/chat/stream`, {
    method:"POST",
    headers:{ "Content-Type":"application/json", "Authorization":`Bearer ${token}` },
    body: JSON.stringify({ message })
  });
  if (!res.ok || !res.body) throw new Error("chat stream failed");
  
  const reader = res.body.getReader(); 
  const dec = new TextDecoder();
  let buffer = "";
  
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    
    buffer += dec.decode(value, { stream: true });
    
    // Look for complete JSON objects in the buffer
    let newlineIndex;
    while ((newlineIndex = buffer.indexOf('\n')) !== -1) {
      const line = buffer.slice(0, newlineIndex).trim();
      buffer = buffer.slice(newlineIndex + 1);
      
      if (line) {
        try {
          // Try to parse as JSON for structured responses
          const parsed = JSON.parse(line);
          if (parsed.text) {
            onChunk(parsed.text, parsed.responsible_ai_checks, parsed.data);
          } else {
            onChunk(line);
          }
        } catch {
          // If not JSON, treat as plain text
          onChunk(line);
        }
      }
    }
  }
  
  // Handle any remaining buffer content
  if (buffer.trim()) {
    try {
      const parsed = JSON.parse(buffer);
      if (parsed.text) {
        onChunk(parsed.text, parsed.responsible_ai_checks, parsed.data);
      } else {
        onChunk(buffer);
      }
    } catch {
      onChunk(buffer);
    }
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
  if (!res.ok) throw new Error("failed to fetch messages");
  return res.json() as Promise<{ messages: Message[]; count: number }>;
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
