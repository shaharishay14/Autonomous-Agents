import { useNavigate } from 'react-router-dom';
import { ChevronRight } from 'lucide-react';

function PrivacyPolicy() {
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
      
      {/* Back Button */}
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
            Privacy Policy – kgen21.com
          </h1>
          <p className="text-gray-400 text-sm md:text-base">
            Last Updated: December 10, 2025
          </p>
        </div>

        {/* Content Card */}
        <div className="bg-gray-900/70 backdrop-blur-sm rounded-2xl p-6 sm:p-8 md:p-10 space-y-6 md:space-y-8 shadow-2xl border border-gray-800/50">
          {/* Introduction */}
          <div className="space-y-4 text-sm sm:text-base leading-relaxed">
            <p>Thank you for using kgen21 ("kgen21", "we", "us", or "our").</p>
            <p>
              This Privacy Policy explains how we collect, use, store, and protect your personal data
              when you use kgen21.com and related services (the "Service").
            </p>
            <p>
              By accessing or using kgen21.com, you agree to this Privacy Policy. If you do not agree,
              please discontinue use of the Service.
            </p>
          </div>

          {/* Section 1 */}
          <section className="space-y-4">
            <h2 className="text-xl sm:text-2xl font-bold">1. Information We Collect</h2>
            <p className="text-sm sm:text-base leading-relaxed">
              We collect the following categories of data to operate, secure, and improve the Service:
            </p>

            {/* 1.1 */}
            <div className="space-y-3 mt-4">
              <h3 className="text-lg sm:text-xl font-semibold">1.1 Account Information</h3>
              <p className="text-sm sm:text-base leading-relaxed">
                When you create an account, we collect:
              </p>
              <ul className="list-disc list-inside space-y-2 text-sm sm:text-base leading-relaxed pl-4">
                <li>Name</li>
                <li>Email address</li>
                <li>Authentication details (e.g., OAuth tokens)</li>
                <li>Profile and preferences</li>
              </ul>
            </div>

            {/* 1.2 */}
            <div className="space-y-3 mt-4">
              <h3 className="text-lg sm:text-xl font-semibold">1.2 User Content</h3>
              <p className="text-sm sm:text-base leading-relaxed">
                To provide the core functionality of kgen21, we collect and store the content you
                create, upload, or process:
              </p>
              <ul className="list-disc list-inside space-y-2 text-sm sm:text-base leading-relaxed pl-4">
                <li>Prompts and instructions</li>
                <li>Agents, workflows, triggers, automations</li>
                <li>Knowledge base files or documents you upload</li>
                <li>Agent conversation history</li>
                <li>Workflow execution logs and outputs</li>
                <li>Error or system logs relevant to your use</li>
              </ul>
              <p className="text-sm sm:text-base leading-relaxed mt-3">
                You may delete User Content at any time or request full deletion (see Section 9).
              </p>
            </div>

            {/* 1.3 */}
            <div className="space-y-3 mt-4">
              <h3 className="text-lg sm:text-xl font-semibold">1.3 Interaction & Usage Data</h3>
              <p className="text-sm sm:text-base leading-relaxed">
                We automatically collect information about how you use the Service, including:
              </p>
              <ul className="list-disc list-inside space-y-2 text-sm sm:text-base leading-relaxed pl-4">
                <li>Interactions with agents and workflows</li>
                <li>Trigger activity</li>
                <li>Clicks, navigation, and feature usage</li>
                <li>Execution timestamps</li>
                <li>System performance data</li>
                <li>IP address, device information, browser type, and OS</li>
              </ul>
              <p className="text-sm sm:text-base leading-relaxed mt-3">
                This helps us improve reliability, debugging, and user experience.
              </p>
            </div>

            {/* 1.4 */}
            <div className="space-y-3 mt-4">
              <h3 className="text-lg sm:text-xl font-semibold">1.4 Third-Party Integration Data</h3>
              <p className="text-sm sm:text-base leading-relaxed">
                If you connect kgen21 to third-party services (e.g., Gmail, WhatsApp, Telegram, Slack,
                GitHub, Google Calendar, OpenAI, Meta, Twilio, or any platform we provide, etc.), we
                process data only as necessary to operate the integration.
              </p>
              <p className="text-sm sm:text-base leading-relaxed mt-3">For example:</p>
              <ul className="list-disc list-inside space-y-2 text-sm sm:text-base leading-relaxed pl-4">
                <li>Gmail: new email metadata or body text (only if you create workflows that read emails)</li>
                <li>Calendar: event metadata (only if your agents need it)</li>
                <li>Slack: messages (only for triggers you configure)</li>
                <li>GitHub: commit data (only when used in a workflow)</li>
              </ul>
              <p className="text-sm sm:text-base leading-relaxed mt-3">
                We do not access more data than required. We never sync or scan entire accounts unless
                explicitly configured by you. Your use of third-party services is governed by their own
                privacy policies.
              </p>
            </div>

            {/* 1.5 */}
            <div className="space-y-3 mt-4">
              <h3 className="text-lg sm:text-xl font-semibold">1.5 Payment Information</h3>
              <p className="text-sm sm:text-base leading-relaxed">
                If you subscribe to a paid plan, we collect:
              </p>
              <ul className="list-disc list-inside space-y-2 text-sm sm:text-base leading-relaxed pl-4">
                <li>Name</li>
                <li>Billing email</li>
                <li>Billing address</li>
                <li>Subscription status</li>
              </ul>
              <p className="text-sm sm:text-base leading-relaxed mt-3">
                Payments are processed by third-party providers (e.g., Stripe, Lemon Squeezy, any
                payment platform). We do not store full credit card numbers on our servers.
              </p>
            </div>

            {/* 1.6 */}
            <div className="space-y-3 mt-4">
              <h3 className="text-lg sm:text-xl font-semibold">1.6 Cookies & Analytics</h3>
              <p className="text-sm sm:text-base leading-relaxed">We may use:</p>
              <ul className="list-disc list-inside space-y-2 text-sm sm:text-base leading-relaxed pl-4">
                <li>Cookies</li>
                <li>Local storage</li>
                <li>Analytics tools (e.g., Google Analytics, Plausible, Sentry, Logfire)</li>
                <li>Error monitoring tools</li>
                <li>Session tracking</li>
              </ul>
              <p className="text-sm sm:text-base leading-relaxed mt-3">
                These help us understand usage patterns, improve performance, detect issues, and
                personalize the interface.
              </p>
            </div>

            {/* 1.7 */}
            <div className="space-y-3 mt-4">
              <h3 className="text-lg sm:text-xl font-semibold">
                1.7 Data Related to Approvals, Permissions and Automations
              </h3>
              <p className="text-sm sm:text-base leading-relaxed">
                As part of the use of the platform operated by kgen21.com ("the Company"), certain
                information related to permissions and approvals granted by the User to intelligent
                agents may be collected and stored, including:
              </p>
              <ul className="list-disc list-inside space-y-2 text-sm sm:text-base leading-relaxed pl-4">
                <li>Types of approved tasks</li>
                <li>Automation settings</li>
                <li>User preferences</li>
                <li>Operational parameters related to agent execution</li>
              </ul>
              <p className="text-sm sm:text-base leading-relaxed mt-3">
                This data is collected and stored solely for the following purposes:
              </p>
              <ul className="list-disc list-inside space-y-2 text-sm sm:text-base leading-relaxed pl-4">
                <li>Proper operation of the Service</li>
                <li>Providing a personalized user experience</li>
                <li>Enabling automated actions based on the User's approvals</li>
                <li>Improving system performance</li>
              </ul>
              <p className="text-sm sm:text-base leading-relaxed mt-3">
                Such data is not sold to third parties and shall only be disclosed where required by law
                or as necessary for the operation of the Service.
              </p>
              <p className="text-sm sm:text-base leading-relaxed mt-3">
                The User may request access to, modification of, or deletion of such data in accordance
                with applicable laws and the Company's data handling procedures.
              </p>
            </div>
          </section>

          {/* Section 2 */}
          <section className="space-y-4">
            <h2 className="text-xl sm:text-2xl font-bold">2. How We Use Your Information</h2>
            <p className="text-sm sm:text-base leading-relaxed">We use your information to:</p>
            <ul className="list-disc list-inside space-y-2 text-sm sm:text-base leading-relaxed pl-4">
              <li>Provide and operate the Service</li>
              <li>Run your agents, workflows, and automations</li>
              <li>Execute third-party integrations you authorize</li>
              <li>Deliver support and communicate with you</li>
              <li>Improve product functionality and user experience</li>
              <li>Enforce our Terms of Service</li>
              <li>Detect and prevent fraud, abuse, and security threats</li>
            </ul>
            <p className="text-sm sm:text-base leading-relaxed mt-3">
              We do not sell your personal data or User Content.
            </p>
          </section>

          {/* Section 3 */}
          <section className="space-y-4">
            <h2 className="text-xl sm:text-2xl font-bold">3. AI Models & Your Data</h2>

            <div className="space-y-3">
              <h3 className="text-lg sm:text-xl font-semibold">3.1 No Training on Your Data</h3>
              <p className="text-sm sm:text-base leading-relaxed">We do not use:</p>
              <ul className="list-disc list-inside space-y-2 text-sm sm:text-base leading-relaxed pl-4">
                <li>Your conversations</li>
                <li>Your prompts</li>
                <li>Your agent definitions</li>
                <li>Your workflows or triggers</li>
                <li>Your knowledge base files</li>
                <li>Your uploaded documents</li>
                <li>Third-party integration data</li>
              </ul>
              <p className="text-sm sm:text-base leading-relaxed mt-3">
                to train our AI models or any third-party AI models.
              </p>
            </div>

            <div className="space-y-3 mt-4">
              <h3 className="text-lg sm:text-xl font-semibold">3.2 How AI Is Used</h3>
              <p className="text-sm sm:text-base leading-relaxed">
                Your content may be sent to third-party AI providers only when you explicitly configure
                an agent to use a model (e.g., OpenAI, Meta, Anthropic, etc.). We send only the data
                required to fulfill your request. Each provider has its own privacy policy.
              </p>
            </div>
          </section>

          {/* Section 4 */}
          <section className="space-y-4">
            <h2 className="text-xl sm:text-2xl font-bold">4. How We Share Information</h2>

            <div className="space-y-3">
              <h3 className="text-lg sm:text-xl font-semibold">4.1 Service Providers</h3>
              <p className="text-sm sm:text-base leading-relaxed">
                Trusted providers that help us operate kgen21:
              </p>
              <ul className="list-disc list-inside space-y-2 text-sm sm:text-base leading-relaxed pl-4">
                <li>Hosting (e.g., AWS, Render)</li>
                <li>Database & authentication (e.g., Supabase, MongoDB Atlas, composio)</li>
                <li>Vector embeddings (e.g., Qdrant)</li>
                <li>Analytics and logging tools</li>
                <li>Email and communications tools</li>
              </ul>
              <p className="text-sm sm:text-base leading-relaxed mt-3">
                All access is strictly controlled.
              </p>
            </div>

            <div className="space-y-3 mt-4">
              <h3 className="text-lg sm:text-xl font-semibold">4.2 Third-Party Integrations You Enable</h3>
              <p className="text-sm sm:text-base leading-relaxed">
                When you connect a service (e.g., Gmail, WhatsApp, GitHub, Calendar, or any platform we
                provide), kgen21 will only process and send data as needed to perform actions you
                configure.
              </p>
              <p className="text-sm sm:text-base leading-relaxed mt-3">
                You fully control these integrations.
              </p>
            </div>

            <div className="space-y-3 mt-4">
              <h3 className="text-lg sm:text-xl font-semibold">4.3 Legal & Safety</h3>
              <p className="text-sm sm:text-base leading-relaxed">We may disclose data if:</p>
              <ul className="list-disc list-inside space-y-2 text-sm sm:text-base leading-relaxed pl-4">
                <li>Required by law</li>
                <li>Necessary to respond to valid legal requests</li>
                <li>Needed to investigate abuse, security issues, or harmful activity</li>
                <li>Required to protect users, the public, or the platform</li>
              </ul>
              <p className="text-sm sm:text-base leading-relaxed mt-3">
                We do not allow government access without valid legal documentation.
              </p>
            </div>
          </section>

          {/* Section 5 */}
          <section className="space-y-4">
            <h2 className="text-xl sm:text-2xl font-bold">5. Security Measures</h2>
            <p className="text-sm sm:text-base leading-relaxed">
              We implement industry-standard protections, including:
            </p>
            <ul className="list-disc list-inside space-y-2 text-sm sm:text-base leading-relaxed pl-4">
              <li>Encryption in transit (HTTPS/TLS)</li>
              <li>Secure hosting and firewalls</li>
              <li>Role-based access controls</li>
              <li>Token-based authentication</li>
              <li>Audit logs</li>
              <li>Regular monitoring</li>
            </ul>
            <p className="text-sm sm:text-base leading-relaxed mt-3">
              No online service can guarantee absolute security, but we take strong, reasonable steps to
              protect your data.
            </p>
          </section>

          {/* Section 6 */}
          <section className="space-y-4">
            <h2 className="text-xl sm:text-2xl font-bold">6. Data Retention</h2>
            <p className="text-sm sm:text-base leading-relaxed">
              We retain your information as long as:
            </p>
            <ul className="list-disc list-inside space-y-2 text-sm sm:text-base leading-relaxed pl-4">
              <li>Your account is active</li>
              <li>Necessary to provide the Service</li>
              <li>Required by law or compliance</li>
            </ul>
            <p className="text-sm sm:text-base leading-relaxed mt-3">
              You may request deletion at any time. Logs, backups, and audit data may be retained for a
              limited period for security and compliance.
            </p>
          </section>

          {/* Section 7 */}
          <section className="space-y-4">
            <h2 className="text-xl sm:text-2xl font-bold">7. Your Rights</h2>
            <p className="text-sm sm:text-base leading-relaxed">You may have the right to:</p>
            <ul className="list-disc list-inside space-y-2 text-sm sm:text-base leading-relaxed pl-4">
              <li>Access your data</li>
              <li>Download or export your data</li>
              <li>Request correction</li>
              <li>Request deletion</li>
              <li>Restrict processing</li>
              <li>Withdraw consent</li>
            </ul>
            <p className="text-sm sm:text-base leading-relaxed mt-3">
              If you wish to exercise these rights, email us at{' '}
              <a
                href="mailto:kgen21.help@gmail.com"
                className="text-purple-400 hover:text-purple-300 transition-colors underline"
              >
                kgen21.help@gmail.com
              </a>
              . We will respond within a reasonable timeframe.
            </p>
          </section>

          {/* Section 8 */}
          <section className="space-y-4">
            <h2 className="text-xl sm:text-2xl font-bold">8. Data Export & Account Deletion</h2>

            <div className="space-y-3">
              <h3 className="text-lg sm:text-xl font-semibold">8.1 Data Export</h3>
              <p className="text-sm sm:text-base leading-relaxed">We can provide exports of:</p>
              <ul className="list-disc list-inside space-y-2 text-sm sm:text-base leading-relaxed pl-4">
                <li>Agents</li>
                <li>Workflows</li>
                <li>Prompts</li>
                <li>Knowledge bases</li>
                <li>Execution logs</li>
                <li>Configuration data</li>
              </ul>
            </div>

            <div className="space-y-3 mt-4">
              <h3 className="text-lg sm:text-xl font-semibold">8.2 Account Deletion</h3>
              <p className="text-sm sm:text-base leading-relaxed">Upon request:</p>
              <ul className="list-disc list-inside space-y-2 text-sm sm:text-base leading-relaxed pl-4">
                <li>Your account will be permanently removed</li>
                <li>Your content, agents, workflows, logs, and integrations will be deleted</li>
                <li>Some system logs may remain temporarily for security purposes</li>
              </ul>
            </div>
          </section>

          {/* Section 9 */}
          <section className="space-y-4">
            <h2 className="text-xl sm:text-2xl font-bold">9. International Data Transfers</h2>
            <p className="text-sm sm:text-base leading-relaxed">
              Your data may be processed in countries outside your jurisdiction, depending on where our
              systems and providers are hosted. We ensure appropriate safeguards exist (e.g., Standard
              Contractual Clauses where applicable).
            </p>
          </section>

          {/* Section 10 */}
          <section className="space-y-4">
            <h2 className="text-xl sm:text-2xl font-bold">10. Children's Privacy</h2>
            <p className="text-sm sm:text-base leading-relaxed">
              The Service is not intended for anyone under 18. We do not knowingly collect data from
              minors. If we become aware of such data, we will delete it promptly.
            </p>
          </section>

          {/* Section 11 */}
          <section className="space-y-4">
            <h2 className="text-xl sm:text-2xl font-bold">11. Updates to This Policy</h2>
            <p className="text-sm sm:text-base leading-relaxed">
              We may update this Privacy Policy from time to time. The "Last Updated" date will reflect
              the most recent version. Continued use of the Service constitutes acceptance of the
              updated Policy.
            </p>
          </section>

          {/* Section 12 */}
          <section className="space-y-4">
            <h2 className="text-xl sm:text-2xl font-bold">12. Contact Us</h2>
            <p className="text-sm sm:text-base leading-relaxed">
              If you have any questions about this Privacy Policy or how your data is handled, contact
              us at:{' '}
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

export default PrivacyPolicy;

