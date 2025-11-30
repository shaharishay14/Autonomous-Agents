import { lazy } from 'react';

// Main pages
export const Builder = lazy(() => import('../pages/builder/Builder'));
export const Agents = lazy(() => import('../pages/agents/Agents'));
export const Integrations = lazy(() => import('../pages/integrations/Integrations'));
export const Workflows = lazy(() => import('../pages/workflows/Workflows'));
export const Chat = lazy(() => import('../pages/chat/Chat'));
export const Settings = lazy(() => import('../pages/settings/Settings'));
export const PublicChat = lazy(() => import('../pages/public/PublicChat'));

// Auth pages
export const Signup = lazy(() => import('../pages/auth/Signup'));
export const Signin = lazy(() => import('../pages/auth/Signin'));
export const ForgotPassword = lazy(() => import('../pages/auth/forgot-password/ForgotPassword'));
export const ResetPassword = lazy(() => import('../pages/auth/reset-password/ResetPassword'));
export const VerifyEmail = lazy(() => import('../pages/auth/verify-email/VerifyEmail'));
export const VerifyEmailPrompt = lazy(() => import('../pages/auth/verify-email-prompt/VerifyEmailPrompt'));
export const CheckEmail = lazy(() => import('../pages/auth/check-email/CheckEmail'));
export const GithubCallback = lazy(() => import('../pages/auth/github-callback/GithubCallback'));

