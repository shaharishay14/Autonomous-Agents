import { Suspense } from 'react';
import { createBrowserRouter, createRoutesFromElements, Route, RouterProvider } from 'react-router-dom';
import Root from './Root';
import PrivateRoutes from './PrivateRoutes';
import PublicRoutes from './PublicRoutes';
import { PageLoader } from './components';
import {
  // Main pages
  Builder,
  Agents,
  Integrations,
  Workflows,
  Chat,
  Settings,
  PublicChat,
  // Auth pages
  Signup,
  Signin,
  ForgotPassword,
  ResetPassword,
  VerifyEmail,
  VerifyEmailPrompt,
  CheckEmail,
  GithubCallback
} from './lazyRoutes';


function Router() {

    const router = createBrowserRouter(
        createRoutesFromElements(
            <>
                {/* Public Chat Route - Standalone, no layout */}
                <Route 
                    path="/public/chat/:agentid" 
                    element={
                        <Suspense fallback={<PageLoader />}>
                            <PublicChat />
                        </Suspense>
                    } 
                />

                <Route path="/" element={<Root />}>
                    <Route index element={<Builder />} />
                    <Route path="/builder" element={<Builder />} />

                    {/* Auth Routes */}
                    <Route element={<PublicRoutes />}>
                        <Route path="/auth">
                            <Route path="signup" element={<Signup />} />
                            <Route path="signin" element={<Signin />} />
                            <Route path="forgot-password" element={<ForgotPassword />} />
                            <Route path="reset-password" element={<ResetPassword />} />
                            <Route path="verify" element={<VerifyEmail />} />
                            <Route path="verify-email-prompt" element={<VerifyEmailPrompt />} />
                            <Route path="check-email" element={<CheckEmail />} />
                            <Route path="callback/github" element={<GithubCallback />} />
                            <Route path="callback/google" element={<div>Google Callback</div>} />
                        </Route>
                    </Route>
                    
                    <Route element={<PrivateRoutes />}>
                        <Route path="/agents" element={<Agents />} />
                        <Route path="/integrations" element={<Integrations />} />
                        <Route path="/workflows" element={<Workflows />} />
                        <Route path="/chat/:id" element={<Chat />} />
                        <Route path="/settings" element={<Settings />} />
                    </Route>
                </Route>
            </>
        )
    )

    return (
        <RouterProvider router={router} />
    )
}


export default Router;