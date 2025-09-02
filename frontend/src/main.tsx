import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
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

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    {Root}
  </StrictMode>,
)
