import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { LayoutProvider } from './lib/LayoutContext';
import ResetPassword from './components/ResetPassword'

function shouldShowReset() {
  try {
    const u = new URL(window.location.href);
    // If the provider appended type=recovery or there's an access_token in the hash/search
    if (u.searchParams.get('type') === 'recovery') return true;
    if (u.searchParams.get('access_token')) return true;
    if (u.hash && u.hash.includes('access_token')) return true;
  } catch (e) {}
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
