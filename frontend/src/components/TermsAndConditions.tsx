import React from 'react';

const TermsAndConditions: React.FC = () => {
  return (
    <div className="prose prose-slate max-w-none text-slate-300 prose-headings:text-slate-100 prose-a:text-cyan-400 prose-strong:text-slate-200">
      <h1 className="text-2xl font-bold mb-6 text-slate-100">Terms and Conditions</h1>
      <p className="text-sm text-slate-400 mb-6">
        <strong>Last updated:</strong> {new Date().toLocaleDateString()}
      </p>

      <section className="mb-6">
        <h2 className="text-xl font-semibold mb-3 text-slate-100">1. Acceptance of Terms</h2>
        <p className="mb-3">
          By accessing and using Morpheus ("the Service"), an AI-powered sleep improvement application, 
          you accept and agree to be bound by the terms and provision of this agreement. If you do not 
          agree to abide by the above, please do not use this service.
        </p>
      </section>

      <section className="mb-6">
        <h2 className="text-xl font-semibold mb-3 text-slate-100">2. Description of Service</h2>
        <p className="mb-3">
          Morpheus is an AI-powered platform designed to provide sleep improvement insights, coaching, 
          and recommendations. The Service includes but is not limited to:
        </p>
        <ul className="list-disc pl-6 mb-3">
          <li>Sleep pattern analysis and tracking</li>
          <li>Personalized sleep coaching and recommendations</li>
          <li>AI-generated content and insights about sleep improvement</li>
          <li>Educational content and resources</li>
          <li>Progress tracking and reporting features</li>
        </ul>
      </section>

      <section className="mb-6">
        <h2 className="text-xl font-semibold mb-3 text-slate-100">3. Medical Disclaimer</h2>
        <div className="bg-amber-900/20 border border-amber-700/50 rounded-lg p-4 mb-3">
          <p className="mb-2">
            <strong className="text-amber-400">IMPORTANT:</strong> Morpheus is not a medical device 
            and does not provide medical advice, diagnosis, or treatment.
          </p>
          <ul className="list-disc pl-6">
            <li>The Service is intended for informational and educational purposes only</li>
            <li>Content provided should not replace professional medical advice</li>
            <li>Always consult with qualified healthcare professionals for medical concerns</li>
            <li>If you have sleep disorders or medical conditions, seek professional medical care</li>
            <li>In case of medical emergencies, contact emergency services immediately</li>
          </ul>
        </div>
      </section>

      <section className="mb-6">
        <h2 className="text-xl font-semibold mb-3 text-slate-100">4. User Accounts and Responsibilities</h2>
        <p className="mb-3">To use certain features of the Service, you must create an account. You agree to:</p>
        <ul className="list-disc pl-6 mb-3">
          <li>Provide accurate, current, and complete information during registration</li>
          <li>Maintain and update your account information to keep it accurate</li>
          <li>Maintain the security of your password and accept responsibility for all activities under your account</li>
          <li>Notify us immediately of any unauthorized use of your account</li>
          <li>Not share your account credentials with others</li>
        </ul>
      </section>

      <section className="mb-6">
        <h2 className="text-xl font-semibold mb-3 text-slate-100">5. Data Collection and Privacy</h2>
        <p className="mb-3">
          Your privacy is important to us. Our collection and use of personal information is governed by our 
          Privacy Policy, which is incorporated into these Terms by reference. By using the Service, you consent to:
        </p>
        <ul className="list-disc pl-6 mb-3">
          <li>Collection of sleep-related data you provide</li>
          <li>Processing of this data to provide personalized recommendations</li>
          <li>Storage of your information in accordance with our Privacy Policy</li>
          <li>Use of anonymized data for service improvement and research purposes</li>
        </ul>
      </section>

      <section className="mb-6">
        <h2 className="text-xl font-semibold mb-3 text-slate-100">6. AI-Generated Content</h2>
        <p className="mb-3">
          Morpheus uses artificial intelligence to generate content and recommendations. You acknowledge that:
        </p>
        <ul className="list-disc pl-6 mb-3">
          <li>AI-generated content may not always be accurate or appropriate for your specific situation</li>
          <li>The Service continuously learns and improves, but may sometimes provide incorrect information</li>
          <li>You should use your own judgment when following AI recommendations</li>
          <li>We do not guarantee the accuracy, completeness, or usefulness of AI-generated content</li>
        </ul>
      </section>

      <section className="mb-6">
        <h2 className="text-xl font-semibold mb-3 text-slate-100">7. Prohibited Uses</h2>
        <p className="mb-3">You may not use the Service:</p>
        <ul className="list-disc pl-6 mb-3">
          <li>For any unlawful purpose or to solicit others to unlawful acts</li>
          <li>To violate any international, federal, provincial, or state regulations, rules, laws, or local ordinances</li>
          <li>To infringe upon or violate our intellectual property rights or the intellectual property rights of others</li>
          <li>To harass, abuse, insult, harm, defame, slander, disparage, intimidate, or discriminate</li>
          <li>To submit false or misleading information</li>
          <li>To upload or transmit viruses or any other type of malicious code</li>
          <li>To attempt to gain unauthorized access to our systems or user accounts</li>
        </ul>
      </section>

      <section className="mb-6">
        <h2 className="text-xl font-semibold mb-3 text-slate-100">8. Intellectual Property Rights</h2>
        <p className="mb-3">
          The Service and its original content, features, and functionality are and will remain the exclusive 
          property of Morpheus and its licensors. The Service is protected by copyright, trademark, and other laws. 
          Our trademarks and trade dress may not be used in connection with any product or service without our prior written consent.
        </p>
      </section>

      <section className="mb-6">
        <h2 className="text-xl font-semibold mb-3 text-slate-100">9. Termination</h2>
        <p className="mb-3">
          We may terminate or suspend your account and bar access to the Service immediately, without prior notice 
          or liability, under our sole discretion, for any reason whatsoever, including but not limited to a breach 
          of the Terms. You may also terminate your account at any time by contacting us.
        </p>
      </section>

      <section className="mb-6">
        <h2 className="text-xl font-semibold mb-3 text-slate-100">10. Limitation of Liability</h2>
        <p className="mb-3">
          To the maximum extent permitted by applicable law, in no event shall Morpheus, its affiliates, agents, 
          directors, employees, suppliers, or licensors be liable for any indirect, punitive, incidental, special, 
          consequential, or exemplary damages, including without limitation damages for loss of profits, goodwill, 
          use, data, or other intangible losses, arising out of or relating to the use of, or inability to use, the Service.
        </p>
      </section>

      <section className="mb-6">
        <h2 className="text-xl font-semibold mb-3 text-slate-100">11. Disclaimer of Warranties</h2>
        <p className="mb-3">
          The Service is provided on an "AS IS" and "AS AVAILABLE" basis. Use of the Service is at your own risk. 
          To the maximum extent permitted by applicable law, we disclaim all warranties, whether express or implied, 
          including but not limited to implied warranties of merchantability, fitness for a particular purpose, 
          and non-infringement.
        </p>
      </section>

      <section className="mb-6">
        <h2 className="text-xl font-semibold mb-3 text-slate-100">12. Governing Law</h2>
        <p className="mb-3">
          These Terms shall be interpreted and governed by the laws of the jurisdiction in which the Service is operated, 
          without regard to its conflict of law provisions. Our failure to enforce any right or provision of these Terms 
          will not be considered a waiver of those rights.
        </p>
      </section>

      <section className="mb-6">
        <h2 className="text-xl font-semibold mb-3 text-slate-100">13. Changes to Terms</h2>
        <p className="mb-3">
          We reserve the right, at our sole discretion, to modify or replace these Terms at any time. If a revision 
          is material, we will try to provide at least 30 days' notice prior to any new terms taking effect. What 
          constitutes a material change will be determined at our sole discretion.
        </p>
      </section>

      <section className="mb-6">
        <h2 className="text-xl font-semibold mb-3 text-slate-100">14. Age Restrictions</h2>
        <p className="mb-3">
          The Service is intended for users who are at least 18 years old. If you are under 18, you may only use 
          the Service with the involvement and consent of a parent or guardian.
        </p>
      </section>

      <section className="mb-6">
        <h2 className="text-xl font-semibold mb-3 text-slate-100">15. Contact Information</h2>
        <p className="mb-3">
          If you have any questions about these Terms and Conditions, please contact us through the application 
          or via the contact information provided in our Privacy Policy.
        </p>
      </section>

      <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-4 mt-8">
        <p className="text-sm text-slate-400">
          By creating an account and using Morpheus, you acknowledge that you have read, understood, and agree 
          to be bound by these Terms and Conditions.
        </p>
      </div>
    </div>
  );
};

export default TermsAndConditions;