import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';

type LayoutState = {
  fullWidthChat: boolean;
  compactMode: boolean;
  sidebarCollapsed: boolean; // applies to md+ where sidebar exists
  setFullWidthChat: (v: boolean) => void;
  setCompactMode: (v: boolean) => void;
  setSidebarCollapsed: (v: boolean) => void;
  toggleFullWidthChat: () => void;
  toggleCompactMode: () => void;
  toggleSidebarCollapsed: () => void;
};

const LayoutContext = createContext<LayoutState | undefined>(undefined);

const KEY_FULL = 'layout.fullWidthChat';
const KEY_COMPACT = 'layout.compactMode';
const KEY_SIDEBAR = 'layout.sidebarCollapsed';

export function LayoutProvider({ children }: { children: React.ReactNode }) {
  const [fullWidthChat, setFullWidthChat] = useState<boolean>(() => {
    try {
      const v = localStorage.getItem(KEY_FULL);
      // Default to true to focus on chat unless user opts out
      return v === null ? true : v === '1';
    } catch { return true; }
  });
  const [compactMode, setCompactMode] = useState<boolean>(() => {
    try { return localStorage.getItem(KEY_COMPACT) === '1'; } catch { return false; }
  });
  const [sidebarCollapsed, setSidebarCollapsed] = useState<boolean>(() => {
    try {
      const v = localStorage.getItem(KEY_SIDEBAR);
      // Default to false (visible) so sidebar shows next to chat on desktop
      return v === null ? false : v === '1';
    } catch { return false; }
  });

  useEffect(() => { try { localStorage.setItem(KEY_FULL, fullWidthChat ? '1' : '0'); } catch {} }, [fullWidthChat]);
  useEffect(() => { try { localStorage.setItem(KEY_COMPACT, compactMode ? '1' : '0'); } catch {} }, [compactMode]);
  useEffect(() => { try { localStorage.setItem(KEY_SIDEBAR, sidebarCollapsed ? '1' : '0'); } catch {} }, [sidebarCollapsed]);

  const value = useMemo<LayoutState>(() => ({
    fullWidthChat,
    compactMode,
    sidebarCollapsed,
    setFullWidthChat,
    setCompactMode,
    setSidebarCollapsed,
    toggleFullWidthChat: () => setFullWidthChat(v => !v),
    toggleCompactMode: () => setCompactMode(v => !v),
    toggleSidebarCollapsed: () => setSidebarCollapsed(v => !v),
  }), [fullWidthChat, compactMode, sidebarCollapsed]);

  return (
    <LayoutContext.Provider value={value}>{children}</LayoutContext.Provider>
  );
}

export function useLayout() {
  const ctx = useContext(LayoutContext);
  if (!ctx) throw new Error('useLayout must be used within LayoutProvider');
  return ctx;
}
