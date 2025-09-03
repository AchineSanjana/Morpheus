import { createClient } from "@supabase/supabase-js";
// Disable automatic session detection from URL so we can handle recovery links
export const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL as string,
  import.meta.env.VITE_SUPABASE_ANON_KEY as string,
  {
    auth: {
      detectSessionInUrl: false,
    },
  }
);

// A second client that persists sessions to sessionStorage (cleared when the tab/window closes).
// Use this for "remember me" = false so the session is not persisted across browser restarts.
export const supabaseSession = createClient(
  import.meta.env.VITE_SUPABASE_URL as string,
  import.meta.env.VITE_SUPABASE_ANON_KEY as string,
  {
    auth: {
      detectSessionInUrl: false,
      // prefer sessionStorage for this client
      // eslint-disable-next-line @typescript-eslint/ban-ts-comment
      // @ts-ignore: sessionStorage exists in the browser
      storage: typeof window !== "undefined" ? window.sessionStorage : undefined,
    },
  }
);
