import { useNavigate } from 'react-router-dom';
import { ChevronRight } from 'lucide-react';

function TermsOfService() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gray-950 text-white relative overflow-hidden">
      {/* Radial gradient light effect in center */}
      <div 
        className="absolute inset-0 pointer-events-none" 
        style={{
          background: 'radial-gradient(circle at center, rgba(147, 51, 234, 0.15) 0%, transparent 50%)'
        }}
      />
      
      {/* Back Button - Centered */}
      <div className="flex mx-auto max-w-4xl px-4 pt-6 md:pt-8 relative z-10">
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
        >
          <ChevronRight className="w-5 h-5 rotate-180" />
          <span className="text-sm md:text-base">Back</span>
        </button>
      </div>

      {/* Content Container */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 md:px-8 pb-12 md:pb-20 relative z-10">
        {/* Header */}
        <div className="mb-8 md:mb-12 mt-4">
          <h1 className="text-2xl sm:text-4xl md:text-5xl lg:text-4xl font-bold mb-4">
            kgen21.com — Terms of Service
          </h1>
          <p className="text-gray-400 text-sm md:text-base">
            Last Updated: December 10, 2025
          </p>
        </div>

        {/* Content Card */}
        <div className="bg-gray-900/70 backdrop-blur-sm rounded-2xl p-6 sm:p-8 md:p-10 space-y-6 md:space-y-8 shadow-2xl border border-gray-800/50">
          {/* Introduction */}
          <div className="space-y-4 text-sm sm:text-base leading-relaxed">
            <p>
              Welcome to kgen21 ("kgen21", "we", "us", or "our").
            </p>
            <p>
              These Terms of Service ("Terms") govern your access to and use of kgen21.com,
              including all related applications, dashboards, APIs, integrations, and services
              (collectively, the "Service").
            </p>
            <p>
              By creating an account, accessing, or using the Service, you agree to be bound by
              these Terms. If you do not agree, you must not use the Service.
            </p>
          </div>

          {/* Section 1 */}
          <section className="space-y-4">
            <h2 className="text-xl sm:text-2xl font-bold">1. Overview</h2>
            <p className="text-sm sm:text-base leading-relaxed">
              kgen21 is a platform that allows users to create, configure, run, and share AI agents,
              workflows, automations, and integrations. These Terms describe the rights and
              responsibilities governing your use of the Service.
            </p>
          </section>

          {/* Section 2 */}
          <section className="space-y-4">
            <h2 className="text-xl sm:text-2xl font-bold">2. Eligibility</h2>
            <p className="text-sm sm:text-base leading-relaxed">
              You must be at least 18 years old and able to enter into a legally binding agreement to
              use the Service.
            </p>
          </section>

          {/* Section 3 */}
          <section className="space-y-4">
            <h2 className="text-xl sm:text-2xl font-bold">3. Account Registration</h2>
            <p className="text-sm sm:text-base leading-relaxed">
              You may be required to create an account to access certain features. By registering, you
              agree to:
            </p>
            <ul className="list-disc list-inside space-y-2 text-sm sm:text-base leading-relaxed pl-4">
              <li>Provide accurate and complete information</li>
              <li>Maintain the security of your credentials</li>
              <li>Be responsible for all activity associated with your account</li>
            </ul>
            <p className="text-sm sm:text-base leading-relaxed">
              We may suspend or terminate your account if it poses security risks, violates these
              Terms, or is used abusively.
            </p>
          </section>

          {/* Section 4 */}
          <section className="space-y-4">
            <h2 className="text-xl sm:text-2xl font-bold">4. Paid Plans, Credits & Billing</h2>
            <p className="text-sm sm:text-base leading-relaxed">
              Some features require a paid plan or the purchase of credits.
            </p>
            <p className="text-sm sm:text-base leading-relaxed">
              By subscribing or purchasing credits, you agree to:
            </p>
            <ul className="list-disc list-inside space-y-2 text-sm sm:text-base leading-relaxed pl-4">
              <li>Pay all applicable fees</li>
              <li>Provide accurate billing information</li>
              <li>Allow recurring charges where applicable</li>
            </ul>
            <p className="text-sm sm:text-base leading-relaxed">
              Fees are billed in advance and are non-refundable, except where required by law or
              expressly stated in our refund policy.
            </p>
            <h3 className="text-lg sm:text-xl font-semibold mt-4">Credits</h3>
            <p className="text-sm sm:text-base leading-relaxed">
              Credits represent usage units consumed per interaction or automated execution, according
              to rules described in the Service. Credits are non-refundable and expire at the end of
              each billing cycle, unless otherwise stated.
            </p>
          </section>

          {/* Section 5 */}
          <section className="space-y-4">
            <h2 className="text-xl sm:text-2xl font-bold">5. Cancellation & Refunds</h2>
            <p className="text-sm sm:text-base leading-relaxed">
              You may cancel your paid plan at any time through your account settings.
            </p>
            <p className="text-sm sm:text-base leading-relaxed">After cancellation:</p>
            <ul className="list-disc list-inside space-y-2 text-sm sm:text-base leading-relaxed pl-4">
              <li>You retain access to paid features until the end of the current billing period</li>
              <li>You will not be charged for subsequent periods</li>
              <li>We do not offer partial refunds for unused time</li>
            </ul>
            <p className="text-sm sm:text-base leading-relaxed">
              We may, at our discretion, issue refunds in exceptional cases.
            </p>
          </section>

          {/* Section 6 */}
          <section className="space-y-4">
            <h2 className="text-xl sm:text-2xl font-bold">6. Price Changes</h2>
            <p className="text-sm sm:text-base leading-relaxed">
              We may update pricing at any time. If we change subscription fees, we will provide at
              least 30 days' notice. Continued use of the Service after the changes take effect
              constitutes acceptance of the new pricing.
            </p>
          </section>

          {/* Section 7 */}
          <section className="space-y-4">
            <h2 className="text-xl sm:text-2xl font-bold">7. Acceptable Use</h2>
            <p className="text-sm sm:text-base leading-relaxed">You agree not to use the Service to:</p>
            <ul className="list-disc list-inside space-y-2 text-sm sm:text-base leading-relaxed pl-4">
              <li>Violate any law or regulation</li>
              <li>Generate or share illegal, harmful, or abusive content</li>
              <li>Automate harmful or unauthorized actions (e.g., spam, harassment, scraping)</li>
              <li>Interfere with or disrupt our platform</li>
              <li>Reverse-engineer, probe, or circumvent security or rate limits</li>
              <li>Misrepresent your identity or affiliation</li>
            </ul>
            <p className="text-sm sm:text-base leading-relaxed">
              We may review, restrict, or remove content or agents that violate these rules.
            </p>
          </section>

          {/* Section 8 */}
          <section className="space-y-4">
            <h2 className="text-xl sm:text-2xl font-bold">8. User Content, Agents & Ownership</h2>
            <p className="text-sm sm:text-base leading-relaxed">
              You may create or upload prompts, workflows, agent configurations, text, files, or other
              materials ("User Content").
            </p>
            <h3 className="text-lg sm:text-xl font-semibold mt-4">Ownership</h3>
            <p className="text-sm sm:text-base leading-relaxed">
              You retain all rights to your User Content.
            </p>
            <h3 className="text-lg sm:text-xl font-semibold mt-4">License to Operate the Service</h3>
            <p className="text-sm sm:text-base leading-relaxed">
              You grant us a non-exclusive, worldwide, royalty-free license to:
            </p>
            <ul className="list-disc list-inside space-y-2 text-sm sm:text-base leading-relaxed pl-4">
              <li>Host, store, process, index, and display your User Content</li>
              <li>Execute your agents, workflows, automations, and integrations</li>
              <li>Provide technical functionality such as logs, analytics, memory, and execution history</li>
            </ul>
            <h3 className="text-lg sm:text-xl font-semibold mt-4">Public Agents & Sharing</h3>
            <p className="text-sm sm:text-base leading-relaxed">
              If you publish or share an agent or workflow publicly, you grant us permission to:
            </p>
            <ul className="list-disc list-inside space-y-2 text-sm sm:text-base leading-relaxed pl-4">
              <li>Display it to others</li>
              <li>List it in catalogs or marketplaces</li>
              <li>Make it discoverable to other users</li>
            </ul>
            <p className="text-sm sm:text-base leading-relaxed">
              We will never make private agents public without your explicit action.
            </p>
          </section>

          {/* Section 8.1 */}
          <section className="space-y-4">
            <h2 className="text-xl sm:text-2xl font-bold">8.1 One-Time Approval for Automated Actions</h2>
            <p className="text-sm sm:text-base leading-relaxed">
              The User acknowledges and agrees that, as part of using the intelligent agents and
              services provided by kgen21.com ("the Company"), the system may allow a one-time
              approval for the execution of a specific task, action, or process ("Approved Action").
            </p>
            <p className="text-sm sm:text-base leading-relaxed">
              Once the initial approval is granted, the Company shall be entitled to execute the
              Approved Action automatically in future instances where an identical or substantially
              similar request is made, without requiring additional approval from the User each time.
            </p>
            <p className="text-sm sm:text-base leading-relaxed">
              The User hereby acknowledges and agrees that:
            </p>
            <ul className="list-disc list-inside space-y-2 text-sm sm:text-base leading-relaxed pl-4">
              <li>The responsibility for granting the initial approval rests solely with the User.</li>
              <li>
                Any action performed based on such approval shall be deemed to have been performed
                with the User's full knowledge and consent.
              </li>
              <li>
                The Company shall not be liable for any damage, loss, error, or outcome resulting
                from the execution of an Approved Action.
              </li>
              <li>
                The User is responsible for ensuring that all permissions granted accurately reflect
                their intent.
              </li>
              <li>
                The User may revoke, limit, or modify any approval at any time through the user
                settings, where such functionality is available.
              </li>
            </ul>
            <p className="text-sm sm:text-base leading-relaxed">
              The Company reserves the right to restrict, suspend, or disable automated actions if
              there is a reasonable concern regarding harm, abuse, misuse, or unlawful activity.
            </p>
          </section>

          {/* Section 9 */}
          <section className="space-y-4">
            <h2 className="text-xl sm:text-2xl font-bold">9. Data Privacy & Security</h2>
            <p className="text-sm sm:text-base leading-relaxed">
              We process personal data only as necessary to operate and improve the Service. We do not
              sell user data. Our Privacy Policy describes how your data is collected, stored, and used.
            </p>
          </section>

          {/* Section 10 */}
          <section className="space-y-4">
            <h2 className="text-xl sm:text-2xl font-bold">10. Data Export & Portability</h2>
            <p className="text-sm sm:text-base leading-relaxed">
              You may request an export of your agents, workflows, configurations, or data at any time.
              We will make reasonable efforts to provide exports in a practical format. Certain
              system-specific components may not be portable.
            </p>
          </section>

          {/* Section 11 */}
          <section className="space-y-4">
            <h2 className="text-xl sm:text-2xl font-bold">11. AI Outputs & Limitations</h2>
            <p className="text-sm sm:text-base leading-relaxed">
              AI-generated content may be inaccurate, incomplete, offensive, unpredictable, or unsafe.
            </p>
            <p className="text-sm sm:text-base leading-relaxed">You acknowledge that:</p>
            <ul className="list-disc list-inside space-y-2 text-sm sm:text-base leading-relaxed pl-4">
              <li>AI responses should be reviewed before use</li>
              <li>Automated outputs may produce unintended results</li>
              <li>
                You are solely responsible for actions or decisions made using AI-generated content
              </li>
              <li>You are responsible for monitoring any agents that execute actions automatically</li>
            </ul>
            <p className="text-sm sm:text-base leading-relaxed">
              We do not guarantee the accuracy, reliability, or suitability of AI outputs.
            </p>
          </section>

          {/* Section 12 */}
          <section className="space-y-4">
            <h2 className="text-xl sm:text-2xl font-bold">
              12. Automations, Integrations & Third-Party Services
            </h2>
            <p className="text-sm sm:text-base leading-relaxed">
              kgen21 integrates with third-party services (e.g., OpenAI, Meta, WhatsApp, email
              providers, cloud APIs).
            </p>
            <p className="text-sm sm:text-base leading-relaxed">
              Your use of those services is governed by their own terms and policies.
            </p>
            <p className="text-sm sm:text-base leading-relaxed">We are not responsible for:</p>
            <ul className="list-disc list-inside space-y-2 text-sm sm:text-base leading-relaxed pl-4">
              <li>Failures, delays, or outages caused by third-party providers</li>
              <li>Data handling practices of third-party services</li>
              <li>Actions executed by your agents through third-party integrations</li>
            </ul>
            <p className="text-sm sm:text-base leading-relaxed">
              You remain fully responsible for those actions.
            </p>
          </section>

          {/* Section 13 */}
          <section className="space-y-4">
            <h2 className="text-xl sm:text-2xl font-bold">13. Usage Limits & Fair Use</h2>
            <p className="text-sm sm:text-base leading-relaxed">
              To maintain platform stability, we may enforce limits on:
            </p>
            <ul className="list-disc list-inside space-y-2 text-sm sm:text-base leading-relaxed pl-4">
              <li>API calls</li>
              <li>Automation frequency</li>
              <li>Workflow execution volume</li>
              <li>Concurrent requests</li>
              <li>Bandwidth and storage</li>
            </ul>
            <p className="text-sm sm:text-base leading-relaxed">
              Abusive, excessive, or anomalous usage may result in throttling, suspension, or
              additional charges where applicable.
            </p>
          </section>

          {/* Section 14 */}
          <section className="space-y-4">
            <h2 className="text-xl sm:text-2xl font-bold">14. Beta Features</h2>
            <p className="text-sm sm:text-base leading-relaxed">
              We may offer experimental or beta features.
            </p>
            <p className="text-sm sm:text-base leading-relaxed">
              Beta features are provided "as is," without warranty, may contain defects, and may be
              modified or discontinued at any time.
            </p>
          </section>

          {/* Section 15 */}
          <section className="space-y-4">
            <h2 className="text-xl sm:text-2xl font-bold">15. Service Availability</h2>
            <p className="text-sm sm:text-base leading-relaxed">
              We aim to provide a stable and reliable platform, but we do not guarantee:
            </p>
            <ul className="list-disc list-inside space-y-2 text-sm sm:text-base leading-relaxed pl-4">
              <li>Uninterrupted service</li>
              <li>Error-free operation</li>
              <li>Protection against all failures or data loss</li>
            </ul>
            <p className="text-sm sm:text-base leading-relaxed">
              Scheduled or unscheduled interruptions may occur.
            </p>
          </section>

          {/* Section 16 */}
          <section className="space-y-4">
            <h2 className="text-xl sm:text-2xl font-bold">16. Intellectual Property</h2>
            <p className="text-sm sm:text-base leading-relaxed">
              All rights in the Service—including software, code, design, branding, UI, models, and
              documentation—belong to kgen21 or our licensors.
            </p>
            <p className="text-sm sm:text-base leading-relaxed">You may not:</p>
            <ul className="list-disc list-inside space-y-2 text-sm sm:text-base leading-relaxed pl-4">
              <li>Copy or modify the Service</li>
              <li>Redistribute our software or content</li>
              <li>Create derivative works of our platform</li>
              <li>Remove or obscure copyright notices</li>
            </ul>
          </section>

          {/* Section 17 */}
          <section className="space-y-4">
            <h2 className="text-xl sm:text-2xl font-bold">17. Termination</h2>
            <p className="text-sm sm:text-base leading-relaxed">
              You may stop using the Service at any time.
            </p>
            <p className="text-sm sm:text-base leading-relaxed">
              We may suspend or terminate your access if:
            </p>
            <ul className="list-disc list-inside space-y-2 text-sm sm:text-base leading-relaxed pl-4">
              <li>You violate these Terms</li>
              <li>Your use poses security or operational risks</li>
              <li>You engage in abusive, harmful, or illegal activity</li>
            </ul>
            <p className="text-sm sm:text-base leading-relaxed">
              If we terminate your account for violating these Terms, no refunds will be issued. Upon
              termination, your right to use the Service immediately ends.
            </p>
          </section>

          {/* Section 18 */}
          <section className="space-y-4">
            <h2 className="text-xl sm:text-2xl font-bold">18. Disclaimers</h2>
            <p className="text-sm sm:text-base leading-relaxed">
              The Service is provided "as is" and "as available" without warranties of any kind.
            </p>
            <p className="text-sm sm:text-base leading-relaxed">
              We disclaim all implied warranties, including:
            </p>
            <ul className="list-disc list-inside space-y-2 text-sm sm:text-base leading-relaxed pl-4">
              <li>Merchantability</li>
              <li>Fitness for a particular purpose</li>
              <li>Non-infringement</li>
            </ul>
            <p className="text-sm sm:text-base leading-relaxed">
              We do not guarantee that the Service will meet your expectations, be error-free, or be
              continuously available.
            </p>
          </section>

          {/* Section 19 */}
          <section className="space-y-4">
            <h2 className="text-xl sm:text-2xl font-bold">19. Limitation of Liability</h2>
            <p className="text-sm sm:text-base leading-relaxed">
              To the maximum extent permitted by law:
            </p>
            <ul className="list-disc list-inside space-y-2 text-sm sm:text-base leading-relaxed pl-4">
              <li>
                We are not liable for indirect, incidental, special, consequential, or punitive damages
              </li>
              <li>
                Our total liability for any claim will not exceed the amount you paid us in the
                preceding three (3) months
              </li>
            </ul>
            <p className="text-sm sm:text-base leading-relaxed">
              This limitation applies to all claims, including those arising from:
            </p>
            <ul className="list-disc list-inside space-y-2 text-sm sm:text-base leading-relaxed pl-4">
              <li>Use of or inability to use the Service</li>
              <li>AI outputs</li>
              <li>Automated actions</li>
              <li>Third-party services or integrations</li>
            </ul>
          </section>

          {/* Section 20 */}
          <section className="space-y-4">
            <h2 className="text-xl sm:text-2xl font-bold">20. Indemnification</h2>
            <p className="text-sm sm:text-base leading-relaxed">
              You agree to indemnify and hold us harmless from any claims, losses, liabilities,
              damages, or expenses (including attorneys' fees) arising out of:
            </p>
            <ul className="list-disc list-inside space-y-2 text-sm sm:text-base leading-relaxed pl-4">
              <li>Your use or misuse of the Service</li>
              <li>Actions taken by your agents</li>
              <li>Your violation of these Terms</li>
              <li>Your User Content</li>
            </ul>
          </section>

          {/* Section 21 */}
          <section className="space-y-4">
            <h2 className="text-xl sm:text-2xl font-bold">21. Changes to These Terms</h2>
            <p className="text-sm sm:text-base leading-relaxed">
              We may update these Terms from time to time. When we do, we will revise the "Last
              Updated" date above. Your continued use of the Service after updates constitutes
              acceptance of the revised Terms.
            </p>
          </section>

          {/* Section 22 */}
          <section className="space-y-4">
            <h2 className="text-xl sm:text-2xl font-bold">22. Governing Law</h2>
            <p className="text-sm sm:text-base leading-relaxed">
              These Terms are governed by the laws of the jurisdiction in which kgen21 operates,
              without regard to conflict-of-law rules. Any disputes shall be resolved exclusively in
              the competent courts of that jurisdiction.
            </p>
          </section>

          {/* Section 23 */}
          <section className="space-y-4">
            <h2 className="text-xl sm:text-2xl font-bold">23. Contact</h2>
            <p className="text-sm sm:text-base leading-relaxed">
              If you have questions about these Terms, contact us at:{' '}
              <a
                href="mailto:kgen21.help@gmail.com"
                className="text-purple-400 hover:text-purple-300 transition-colors underline"
              >
                kgen21.help@gmail.com
              </a>
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}

export default TermsOfService;

