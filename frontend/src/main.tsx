import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { LayoutProvider } from './lib/LayoutContext';
import ResetPassword from './components/ResetPassword'

function shouldShowReset() {
  try {
    const u = new URL(window.location.href);
    
    // Check URL parameters from both search and hash
    const searchParams = u.searchParams;
    const hashParams = new URLSearchParams(u.hash.startsWith('#') ? u.hash.substring(1) : '');
    
    // Get type from either search or hash
    const typeFromSearch = searchParams.get('type');
    const typeFromHash = hashParams.get('type');
    const type = typeFromSearch || typeFromHash;
    
    // Only show reset password page for actual password recovery
    // Email confirmations should redirect to main app
    if (type === 'recovery') {
      // Check if this is a password reset (has access_token) or just email confirmation
      const hasAccessToken = searchParams.get('access_token') || hashParams.get('access_token');
      if (hasAccessToken) {
        return true; // This is a password reset with token
      }
    }
    
    // For email confirmations (type=signup or no access_token), go to main app
    if (type === 'signup' || type === 'email_change') {
      return false; // Let the main app handle email confirmations
    }
    
    // Fallback: if there's an access_token without type, it's likely a password reset
    if (searchParams.get('access_token') || hashParams.get('access_token')) {
      return true;
    }
    
  } catch (e) {
    console.error('Error parsing URL for reset detection:', e);
  }
  return false;
}

const Root = shouldShowReset() ? <ResetPassword /> : <App />;

// Enable performance-lite mode automatically on low-end devices or when user prefers reduced motion
const rootClasses: string[] = []
try {
  // Prefer reduced motion => disable heavy animations
  if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    rootClasses.push('perf-lite')
  }
  // Device memory hint (not supported everywhere)
  // @ts-ignore
  const mem = navigator.deviceMemory as number | undefined
  if (typeof mem === 'number' && mem <= 4) {
    rootClasses.push('perf-lite')
  }
} catch {}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <div className={rootClasses.join(' ')}>
      <LayoutProvider>
        {Root}
      </LayoutProvider>
    </div>
  </StrictMode>,
)
