import { useState, useEffect } from 'react';
import { supabase } from '../lib/supabaseClient';

// Types for responsible AI data
interface ResponsibleAIStatus {
  enabled: boolean;
  version: string;
  features: {
    fairness_checks: boolean;
    transparency_tracking: boolean;
    ethical_data_handling: boolean;
    bias_detection: boolean;
    inclusive_language: boolean;
  };
  status: string;
}

interface ResponsibleAICheck {
  passed: boolean;
  risk_level: string;
  category: string;
  message: string;
  suggestions: string[];
  metadata: Record<string, any>;
}

// Data Usage Notice Component
export function DataUsageNotice() {
  return (
    <div className="text-sm text-zinc-300 p-4 bg-zinc-800/50 rounded-xl border border-zinc-700/50 mb-4">
      <div className="flex items-center gap-2 mb-3">
        <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
        </svg>
        <h3 className="font-semibold text-zinc-100">Your Data Privacy</h3>
      </div>
      <ul className="space-y-2 text-zinc-300">
        <li className="flex items-start gap-2">
          <span className="text-green-400 mt-0.5">•</span>
          <span>Sleep logs stored securely with encryption for personalized advice</span>
        </li>
        <li className="flex items-start gap-2">
          <span className="text-green-400 mt-0.5">•</span>
          <span>No data shared with third parties or used for advertising</span>
        </li>
        <li className="flex items-start gap-2">
          <span className="text-green-400 mt-0.5">•</span>
          <span>You can export or delete your data anytime</span>
        </li>
        <li className="flex items-start gap-2">
          <span className="text-green-400 mt-0.5">•</span>
          <span>AI analysis happens locally, not sent to external APIs</span>
        </li>
        <li className="flex items-start gap-2">
          <span className="text-green-400 mt-0.5">•</span>
          <span>All data isolated to your account with Row Level Security</span>
        </li>
      </ul>
    </div>
  );
}

// AI Transparency Card Component
export function AITransparencyCard() {
  const [showDetails, setShowDetails] = useState(false);

  return (
    <div className="text-sm p-4 bg-blue-900/20 rounded-xl border border-blue-700/30 mb-4">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-2xl">🤖</span>
        <h3 className="font-semibold text-blue-100">AI Transparency</h3>
      </div>
      
      <div className="text-blue-200 space-y-2 mb-3">
        <p>Our AI uses evidence-based sleep science principles (CBT-I - Cognitive Behavioral Therapy for Insomnia).</p>
        <p>Recommendations are based solely on your personal sleep patterns and established sleep research.</p>
      </div>

      <button
        onClick={() => setShowDetails(!showDetails)}
        className="text-blue-400 hover:text-blue-300 underline text-sm"
      >
        {showDetails ? 'Hide details' : 'Learn more about our AI approach'}
      </button>

      {showDetails && (
        <div className="mt-3 p-3 bg-blue-900/30 rounded-lg border border-blue-700/20">
          <h4 className="font-medium text-blue-100 mb-2">How Our AI Works:</h4>
          <ul className="space-y-1 text-xs text-blue-200">
            <li>• <strong>Coach Agent:</strong> Provides sleep hygiene advice based on CBT-I protocols</li>
            <li>• <strong>Analyst Agent:</strong> Identifies patterns in your sleep data over time</li>
            <li>• <strong>Information Agent:</strong> Answers questions using peer-reviewed sleep research</li>
            <li>• <strong>Safety System:</strong> Flags concerning symptoms and recommends professional help</li>
            <li>• <strong>No Bias Training:</strong> Our system is designed to provide inclusive advice regardless of demographics</li>
          </ul>
          
          <div className="mt-3 p-2 bg-yellow-900/30 rounded border border-yellow-700/30">
            <p className="text-yellow-200 text-xs">
              <strong>Important:</strong> This is educational guidance, not medical care. For persistent sleep issues, consult a healthcare professional.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

// User Rights Component
export function UserRightsPanel() {
  const [showRights, setShowRights] = useState(false);

  const handleDataExport = async () => {
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) {
        alert('Please sign in to export your data');
        return;
      }

      const response = await fetch(`${import.meta.env.VITE_API_URL}/profile/export`, {
        headers: {
          'Authorization': `Bearer ${session.access_token}`
        }
      });

      if (!response.ok) {
        throw new Error('Export failed');
      }

      const data = await response.json();
      
      // Create and download JSON file
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `morpheus-data-export-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      alert('Your data has been exported successfully!');
    } catch (error) {
      console.error('Export error:', error);
      alert('Failed to export data. Please try again.');
    }
  };

  const handleDataCorrection = async () => {
    const details = prompt('Please describe what data you would like to correct:');
    if (!details) return;

    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) {
        alert('Please sign in to request data correction');
        return;
      }

      const response = await fetch(`${import.meta.env.VITE_API_URL}/profile/correction-request`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        },
        body: JSON.stringify({
          correction_details: details,
          requested_by: session.user.email
        })
      });

      if (!response.ok) {
        throw new Error('Correction request failed');
      }

      const result = await response.json();
      alert(`Data correction request submitted successfully! Request ID: ${result.request_id}\n\nYour request will be processed within 30 days.`);
    } catch (error) {
      console.error('Correction request error:', error);
      alert('Failed to submit correction request. Please try again.');
    }
  };

  const handleAccountDeletion = async () => {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) {
      alert('Please sign in to delete your account');
      return;
    }

    const confirmText = `To permanently delete your account and all data, please type your email: ${session.user.email}`;
    const emailConfirmation = prompt(confirmText);
    
    if (emailConfirmation !== session.user.email) {
      alert('Email confirmation did not match. Account deletion cancelled.');
      return;
    }

    const finalConfirm = window.confirm(
      'FINAL CONFIRMATION: This will permanently delete your account and ALL data including:\n\n' +
      '• Your sleep logs\n' +
      '• Chat history\n' +
      '• Profile information\n' +
      '• All personal data\n\n' +
      'This action CANNOT be undone. Continue?'
    );

    if (!finalConfirm) return;

    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/profile/delete-account`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        },
        body: JSON.stringify({
          confirm_deletion: true,
          email: session.user.email
        })
      });

      if (!response.ok) {
        throw new Error('Account deletion failed');
      }

      await response.json();
      alert('Your account and all data have been permanently deleted. You will be signed out now.');
      
      // Sign out the user
      await supabase.auth.signOut();
      window.location.reload();
      
    } catch (error) {
      console.error('Account deletion error:', error);
      alert('Failed to delete account. Please contact support if this persists.');
    }
  };

  return (
    <div className="text-sm">
      <button
        onClick={() => setShowRights(!showRights)}
        className="flex items-center gap-2 text-zinc-400 hover:text-zinc-200 mb-3"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span>Your Data Rights</span>
        <svg className={`w-4 h-4 transition-transform ${showRights ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="m19 9-7 7-7-7" />
        </svg>
      </button>

      {showRights && (
        <div className="space-y-3 p-3 bg-zinc-800/30 rounded-lg border border-zinc-700/30">
          <div className="space-y-2">
            <button
              onClick={handleDataExport}
              className="w-full text-left p-2 bg-zinc-700/50 hover:bg-zinc-700 rounded transition-colors"
            >
              <div className="font-medium text-zinc-200">📋 Export My Data</div>
              <div className="text-xs text-zinc-400">Download all your sleep logs and profile data</div>
            </button>

            <button
              onClick={handleDataCorrection}
              className="w-full text-left p-2 bg-zinc-700/50 hover:bg-zinc-700 rounded transition-colors"
            >
              <div className="font-medium text-zinc-200">✏️ Correct My Data</div>
              <div className="text-xs text-zinc-400">Request corrections to your stored information</div>
            </button>

            <button
              onClick={handleAccountDeletion}
              className="w-full text-left p-2 bg-red-900/30 hover:bg-red-900/50 rounded transition-colors border border-red-700/30"
            >
              <div className="font-medium text-red-200">🗑️ Delete My Account</div>
              <div className="text-xs text-red-300">Permanently delete all your data</div>
            </button>
          </div>

          <div className="text-xs text-zinc-400 border-t border-zinc-700 pt-2">
            <p>Under data protection laws, you have the right to:</p>
            <ul className="mt-1 space-y-0.5 ml-3">
              <li>• Access your personal data</li>
              <li>• Correct inaccurate data</li>
              <li>• Delete your data (right to be forgotten)</li>
              <li>• Data portability</li>
              <li>• Object to processing</li>
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}

// Fairness Statement Component
export function FairnessStatement() {
  return (
    <div className="text-xs text-zinc-400 p-3 bg-zinc-800/30 rounded-lg border border-zinc-700/30">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-purple-400">⚖️</span>
        <h4 className="font-medium text-zinc-300">Our Commitment to Fairness</h4>
      </div>
      <p className="mb-2">
        Morpheus is designed to provide inclusive sleep advice that works for people of all backgrounds, 
        ages, lifestyles, and circumstances.
      </p>
      <ul className="space-y-1 ml-3">
        <li>• No discrimination based on demographics</li>
        <li>• Culturally sensitive sleep recommendations</li>
        <li>• Accommodates different work schedules and lifestyles</li>
        <li>• Regular bias testing and algorithm auditing</li>
      </ul>
    </div>
  );
}

// Enhanced Responsible AI Status Component
export function ResponsibleAIStatus() {
  const [status, setStatus] = useState<ResponsibleAIStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const { data: { session } } = await supabase.auth.getSession();
        if (!session) return;

        const response = await fetch('/api/responsible-ai/status', {
          headers: {
            'Authorization': `Bearer ${session.access_token}`,
            'Content-Type': 'application/json'
          }
        });

        if (response.ok) {
          const data = await response.json();
          setStatus(data);
        } else {
          setError('Failed to fetch responsible AI status');
        }
      } catch (err) {
        setError('Error connecting to responsible AI service');
      } finally {
        setLoading(false);
      }
    };

    fetchStatus();
  }, []);

  if (loading) {
    return (
      <div className="text-sm text-zinc-400 p-4 bg-zinc-800/50 rounded-xl border border-zinc-700/50">
        <div className="flex items-center gap-2">
          <div className="animate-spin w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full"></div>
          <span>Loading responsible AI status...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-sm text-amber-400 p-4 bg-amber-900/20 rounded-xl border border-amber-700/30">
        <div className="flex items-center gap-2">
          <span className="text-amber-400">⚠️</span>
          <span>{error}</span>
        </div>
      </div>
    );
  }

  if (!status) return null;

  return (
    <div className="text-sm p-4 bg-green-900/20 rounded-xl border border-green-700/30 mb-4">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-green-400">✓</span>
        <h3 className="font-semibold text-green-100">Responsible AI Active</h3>
        <span className="text-xs text-green-300 bg-green-900/30 px-2 py-1 rounded">
          v{status.version}
        </span>
      </div>
      
      <div className="grid grid-cols-2 gap-2 text-xs text-green-200">
        <div className="flex items-center gap-2">
          <span className={status.features.fairness_checks ? "text-green-400" : "text-red-400"}>
            {status.features.fairness_checks ? "✓" : "✗"}
          </span>
          <span>Fairness Checks</span>
        </div>
        <div className="flex items-center gap-2">
          <span className={status.features.transparency_tracking ? "text-green-400" : "text-red-400"}>
            {status.features.transparency_tracking ? "✓" : "✗"}
          </span>
          <span>Transparency Tracking</span>
        </div>
        <div className="flex items-center gap-2">
          <span className={status.features.ethical_data_handling ? "text-green-400" : "text-red-400"}>
            {status.features.ethical_data_handling ? "✓" : "✗"}
          </span>
          <span>Ethical Data Handling</span>
        </div>
        <div className="flex items-center gap-2">
          <span className={status.features.bias_detection ? "text-green-400" : "text-red-400"}>
            {status.features.bias_detection ? "✓" : "✗"}
          </span>
          <span>Bias Detection</span>
        </div>
      </div>
      
      <div className="mt-3 text-xs text-green-300">
        Status: <span className="font-medium">{status.status}</span>
      </div>
    </div>
  );
}

// Response Analysis Component - Shows responsible AI check results
export function ResponseAnalysis({ responsibleAIChecks }: { responsibleAIChecks?: Record<string, ResponsibleAICheck> }) {
  const [showDetails, setShowDetails] = useState(false);

  if (!responsibleAIChecks) return null;

  const overall = responsibleAIChecks.overall;
  const riskLevel = overall?.risk_level || 'unknown';
  const passed = overall?.passed ?? true;

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'low': return 'text-green-400 bg-green-900/20 border-green-700/30';
      case 'medium': return 'text-yellow-400 bg-yellow-900/20 border-yellow-700/30';
      case 'high': return 'text-orange-400 bg-orange-900/20 border-orange-700/30';
      case 'critical': return 'text-red-400 bg-red-900/20 border-red-700/30';
      default: return 'text-gray-400 bg-gray-900/20 border-gray-700/30';
    }
  };

  const getRiskIcon = (level: string) => {
    switch (level) {
      case 'low': return '✓';
      case 'medium': return '⚠️';
      case 'high': return '🔶';
      case 'critical': return '🚨';
      default: return '?';
    }
  };

  return (
    <div className={`text-xs p-3 rounded-lg border ${getRiskColor(riskLevel)} mb-2`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span>{getRiskIcon(riskLevel)}</span>
          <span className="font-medium">
            AI Safety Check: {passed ? 'Passed' : 'Issues Detected'}
          </span>
          <span className="text-xs opacity-75">
            Risk: {riskLevel}
          </span>
        </div>
        <button
          onClick={() => setShowDetails(!showDetails)}
          className="text-xs opacity-60 hover:opacity-100 transition-opacity"
        >
          {showDetails ? 'Hide' : 'Details'}
        </button>
      </div>

      {showDetails && (
        <div className="mt-3 space-y-2">
          {Object.entries(responsibleAIChecks).map(([checkType, check]) => {
            if (checkType === 'overall') return null;
            
            return (
              <div key={checkType} className="border-t border-current/20 pt-2">
                <div className="flex items-center gap-2 mb-1">
                  <span className={check.passed ? 'text-green-400' : 'text-red-400'}>
                    {check.passed ? '✓' : '✗'}
                  </span>
                  <span className="font-medium capitalize">
                    {checkType.replace('_', ' ')}
                  </span>
                </div>
                <p className="opacity-80 text-xs ml-4">{check.message}</p>
                {check.suggestions.length > 0 && (
                  <ul className="ml-4 mt-1 space-y-1">
                    {check.suggestions.map((suggestion, index) => (
                      <li key={index} className="text-xs opacity-70">
                        • {suggestion}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// Data Control Panel Component
export function DataControlPanel() {
  const [exportLoading, setExportLoading] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const handleExportData = async () => {
    setExportLoading(true);
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) return;

      // This would call your backend to export user data
      const response = await fetch('/api/user/export-data', {
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `morpheus-sleep-data-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error('Export failed:', error);
    } finally {
      setExportLoading(false);
    }
  };

  const handleDeleteData = async () => {
    setDeleteLoading(true);
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) return;

      // This would call your backend to delete user data
      const response = await fetch('/api/user/delete-data', {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        // Redirect to home or show success message
        window.location.href = '/';
      }
    } catch (error) {
      console.error('Delete failed:', error);
    } finally {
      setDeleteLoading(false);
      setShowDeleteConfirm(false);
    }
  };

  return (
    <div className="text-sm p-4 bg-zinc-800/50 rounded-xl border border-zinc-700/50">
      <div className="flex items-center gap-2 mb-4">
        <span className="text-blue-400">🛡️</span>
        <h3 className="font-semibold text-zinc-100">Your Data Rights</h3>
      </div>
      
      <div className="space-y-3">
        <div className="flex items-center justify-between py-2 border-b border-zinc-700/50">
          <div>
            <p className="text-zinc-200 font-medium">Export Your Data</p>
            <p className="text-xs text-zinc-400">Download all your sleep data and logs</p>
          </div>
          <button
            onClick={handleExportData}
            disabled={exportLoading}
            className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-3 py-1 rounded text-xs transition-colors"
          >
            {exportLoading ? 'Exporting...' : 'Export'}
          </button>
        </div>
        
        <div className="flex items-center justify-between py-2">
          <div>
            <p className="text-zinc-200 font-medium">Delete Your Data</p>
            <p className="text-xs text-zinc-400">Permanently remove all your data from our systems</p>
          </div>
          <button
            onClick={() => setShowDeleteConfirm(true)}
            className="bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white px-3 py-1 rounded text-xs transition-colors"
          >
            Delete
          </button>
        </div>
      </div>

      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-zinc-800 border border-zinc-700 rounded-xl p-6 max-w-md mx-4">
            <h3 className="text-lg font-semibold text-zinc-100 mb-4">Confirm Data Deletion</h3>
            <p className="text-zinc-300 mb-6">
              Are you sure you want to permanently delete all your sleep data? This action cannot be undone.
            </p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setShowDeleteConfirm(false)}
                className="bg-zinc-600 hover:bg-zinc-700 text-white px-4 py-2 rounded text-sm transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteData}
                disabled={deleteLoading}
                className="bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white px-4 py-2 rounded text-sm transition-colors"
              >
                {deleteLoading ? 'Deleting...' : 'Delete All Data'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}