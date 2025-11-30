import { LogIn } from 'lucide-react'
import { 
  AuthLogo, 
  AuthHeader, 
  AuthDivider, 
  SocialButtons, 
  AuthFooterLink,
  SigninForm,
  SubmitButton
} from './components'
import { useLogin, useProviders } from './hooks'
import useDarkModeStore from '../../../../store/darkmode.store'



function Signin() {
  const { register, handleSubmit, errors, onSubmit, isLoading } = useLogin()
  const { handleGoogleLogin, handleGithubLogin, isLoading: isProviderLoading } = useProviders()
  const { isDarkMode } = useDarkModeStore()

  return (
    <div className={`min-h-[calc(100vh-4rem)] flex items-center justify-center p-4 ${
      isDarkMode ? 'bg-[#0a0a0a]' : 'bg-gradient-to-br from-purple-50 via-white to-pink-50'
    }`}>
      <div className="w-full max-w-md">

        <AuthLogo />
        
        <AuthHeader 
          title="Welcome back"
          subtitle="Sign in to continue building amazing AI agents"
        />

        <div className={`border rounded-xl p-6 md:p-8 ${
          isDarkMode ? 'bg-[#1a1a1a] border-gray-800' : 'bg-white border-purple-200 shadow-lg'
        }`}>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <SigninForm register={register} errors={errors} />
              <SubmitButton
                isLoading={isLoading || isProviderLoading}
                loadingText="Signing in..."
                text="Sign in"
                icon={LogIn}
              />
            </form>

            <AuthDivider />

            <SocialButtons 
              onGoogleClick={handleGoogleLogin}
              onGithubClick={handleGithubLogin}
            />

          <AuthFooterLink
            text="Don't have an account?"
            linkText="Create account"
            linkTo="/auth/signup"
          />
        </div>
      </div>
    </div>
  )
}

export default Signin

