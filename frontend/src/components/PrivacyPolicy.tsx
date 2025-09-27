import React from "react";

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="mb-6">
      <h2 className="text-lg font-semibold mb-2 text-slate-100">{title}</h2>
      <div className="text-slate-300 leading-relaxed">{children}</div>
    </section>
  );
}

export default function PrivacyPolicy() {
  return (
    <div className="max-w-3xl mx-auto text-sm text-slate-200">
      <h1 className="text-2xl font-bold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-cyan-400">
        Privacy Policy — Morpheus Sleep AI
      </h1>
      <p className="text-slate-400 mb-6">Effective date: 2025-09-27</p>

      <Section title="Overview">
        <p>
          Morpheus Sleep AI helps users improve sleep through journaling, analysis, and gentle AI guidance.
          We collect only the data needed to provide the service, protect it with industry‑standard safeguards,
          and never sell it.
        </p>
      </Section>

      <Section title="What We Collect">
        <ul className="list-disc pl-5 space-y-2">
          <li>Account data (email, name, avatar)</li>
          <li>Profile data (full_name, username, avatar_url)</li>
          <li>Sleep logs (date, bedtime, wake_time, awakenings, caffeine_after3pm, alcohol, screen_time_min, notes)</li>
          <li>Chat messages (your questions and AI responses)</li>
          <li>Usage metadata (e.g., IP, user agent) for security</li>
          <li>Local drafts stored in your browser until you submit</li>
        </ul>
      </Section>

      <Section title="How We Use Data">
        <ul className="list-disc pl-5 space-y-2">
          <li>Provide core features and personalize guidance</li>
          <li>Generate AI responses and bedtime stories</li>
          <li>Maintain security and prevent abuse</li>
          <li>Operate, troubleshoot, and improve the service</li>
          <li>Comply with legal obligations</li>
        </ul>
        <p className="mt-2 text-slate-300">
          Legal bases: Contract, Legitimate interests, and Consent where required.
        </p>
      </Section>

      <Section title="AI Disclosures">
        <p>
          When enabled, AI features may call third‑party AI services (e.g., Google Gemini). We minimize personal
          data in prompts, sanitize inputs, and validate outputs for safety. Avoid entering sensitive personal data.
          You may request restriction of AI processing; we will use local fallbacks where feasible.
        </p>
      </Section>

      <Section title="Sharing and Disclosure">
        <p>We do not sell your data. We share data only with:</p>
        <ul className="list-disc pl-5 space-y-2">
          <li>Supabase (Auth/DB/Storage) as our processor with RLS safeguards</li>
          <li>AI provider (e.g., Gemini) to generate responses when used</li>
          <li>Service providers necessary to operate the service</li>
          <li>Authorities when required by law</li>
        </ul>
      </Section>

      <Section title="Data Retention">
        <ul className="list-disc pl-5 space-y-2">
          <li>Account/profile: retained while your account is active</li>
          <li>Sleep logs and chat: retained until you delete or close account</li>
          <li>Security logs: retained for a limited period</li>
          <li>Local drafts: stored only in your browser</li>
        </ul>
      </Section>

      <Section title="Security">
        <ul className="list-disc pl-5 space-y-2">
          <li>HTTPS/TLS and strict security headers</li>
          <li>Input sanitization, output validation, safe fallbacks</li>
          <li>Row Level Security (RLS) on Supabase</li>
          <li>Minimal PII in logs and least‑privilege access</li>
        </ul>
      </Section>

      <Section title="Your Rights">
        <p>
          You may have rights to access, correct, delete, export, or object to certain processing.
          Contact privacy@example.com to submit a request. We may need to verify your identity.
        </p>
      </Section>

      <Section title="Cookies and Local Storage">
        <p>
          Supabase stores session tokens (e.g., in local storage). The app may store UI state or drafts locally for
          convenience. We do not use third‑party advertising cookies.
        </p>
      </Section>

      <Section title="Children’s Privacy">
        <p>
          Morpheus is not directed to children under 13. If you believe a child provided personal data, contact us to remove it.
          Where required, we follow parental consent obligations.
        </p>
      </Section>

      <Section title="International Transfers">
        <p>
          Data may be processed or stored in regions where our processors operate. We use appropriate safeguards
          (e.g., SCCs) where required for cross‑border transfers.
        </p>
      </Section>

      <Section title="Changes and Contact">
        <p>We may update this policy. We will post updates with a new effective date.</p>
        <p className="mt-2">Contact: privacy@example.com</p>
      </Section>
    </div>
  );
}
