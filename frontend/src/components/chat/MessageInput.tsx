// React import not required for JSX in React 17+

type Props = {
  value: string;
  onChange: (v: string) => void;
  onSend: () => void;
  loading: boolean;
  onStop?: () => void;
  compactMode: boolean;
  suggestions?: string[];
};

export function MessageInput({ value, onChange, onSend, loading, onStop, compactMode, suggestions = [] }: Props) {
  return (
    <div className={`${compactMode ? 'p-3' : 'p-4'} border-t border-slate-700/50 bg-slate-900/50 pb-safe`}>
      <div className="flex gap-3">
        <div className="flex-1 relative">
          <input
            className={`w-full bg-slate-800/80 border border-slate-600/50 ${compactMode ? 'p-2.5 pr-10 rounded-lg text-[13px]' : 'p-3 pr-12 rounded-xl text-sm'} transition-all duration-200 focus:border-indigo-400 focus:bg-slate-800 focus:ring-2 focus:ring-indigo-400/20 focus:outline-none`}
            placeholder="Ask for analysis, plan, or explanation..."
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                onSend();
              }
            }}
            disabled={loading}
          />
          {value && (
            <button
              onClick={() => onChange("")}
              className={`absolute ${compactMode ? 'right-2' : 'right-3'} top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200 transition-colors`}
            >
              ✕
            </button>
          )}
        </div>
        {loading ? (
          <button
            onClick={() => onStop?.()}
            className={`bg-rose-600 hover:bg-rose-500 ${compactMode ? 'px-4 py-2 rounded-lg text-[13px]' : 'px-6 py-3 rounded-xl text-sm'} font-medium transition-all duration-200 shadow-lg hover:shadow-xl transform hover:scale-105 flex items-center gap-2`}
          >
            <span>Stop</span>
          </button>
        ) : (
          <button
            disabled={!value.trim()}
            onClick={onSend}
            className={`bg-gradient-to-r from-indigo-600 to-cyan-600 disabled:from-slate-600 disabled:to-slate-600 disabled:cursor-not-allowed hover:from-indigo-500 hover:to-cyan-500 ${compactMode ? 'px-4 py-2 rounded-lg text-[13px]' : 'px-6 py-3 rounded-xl text-sm'} font-medium transition-all duration-200 shadow-lg hover:shadow-xl disabled:shadow-none transform hover:scale-105 disabled:scale-100 flex items-center gap-2`}
          >
            <span className={compactMode ? 'text-[13px]' : ''}>Send</span>
            <span className={`${compactMode ? 'text-[11px]' : 'text-xs'} opacity-70`}>↵</span>
          </button>
        )}
      </div>

      <div className={`flex flex-wrap gap-2 ${compactMode ? 'mt-2' : 'mt-3'}`}>
        {suggestions.map((s, i) => (
          <button
            key={i}
            onClick={() => onChange(s)}
            disabled={loading}
            className={`${compactMode ? 'text-[11px] px-2.5 py-1 rounded-md' : 'text-xs px-3 py-1 rounded-lg'} text-cyan-400 hover:text-cyan-300 bg-cyan-400/10 hover:bg-cyan-400/20 border border-cyan-400/20 transition-colors disabled:opacity-50`}
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}
