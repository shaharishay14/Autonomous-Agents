import { useMutation } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { yupResolver } from '@hookform/resolvers/yup'
import { toast } from 'react-toastify'
import { signinSchema } from '../schema'
import { useUserStore } from '../../../../../store/user.store'
import { loginUser, type LoginResponse } from '../requests'
import type { SigninFormData } from '../types'
import type { AxiosError } from 'axios'

interface ErrorResponse {
  message?: string
  detail?: string
}

export const useLogin = () => {
  const navigate = useNavigate()
  const {setUser, setIsAuthenticated} = useUserStore((state) => state)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<SigninFormData>({
    resolver: yupResolver(signinSchema),
  })

  const {
    mutateAsync,
    isPending: isLoading,
    isError,
    error,
    isSuccess,
  } = useMutation<LoginResponse, AxiosError<ErrorResponse>, SigninFormData>({
    mutationFn: loginUser,
    onSuccess: (data) => {
      // שמירת המשתמש ב-store
      setUser(data.user)
      setIsAuthenticated(true)
      // ה-tokens נשמרים אוטומטית ב-cookies על ידי הדפדפן
      // data.access - access token
      // data.refresh - refresh token
      
      // הצגת הודעת הצלחה
      toast.success(`Welcome back, ${data.user.username}!`)
      
      // ניווט לדף הbuilder
      navigate('/builder')
    },
    onError: (error) => {
      // בדיקה אם זו שגיאת אימות email
      if (error.response?.status === 403) {
        const detail = error.response?.data?.detail
        if (detail === 'Email verification required. Verification email sent.') {
          toast.info('Please verify your email. Verification email sent.')
          navigate('/auth/verify-email-prompt')
          return
        }
      }
      
      const message = error.response?.data?.message || error.message || 'Login failed'
      console.error('Login error:', message)
      toast.error(message)
    },
  })

  const onSubmit = async (data: SigninFormData) => {
    try {
      await mutateAsync(data)
    } catch (error) {
      // שמירת המייל/username ב-localStorage אם זו שגיאת verification
      // נשתמש ב-username אבל נניח שזה email אם יש @
      if (data.username.includes('@')) {
        localStorage.setItem('verificationEmail', data.username)
      }
    }
  }

  return {
    register,
    handleSubmit,
    errors,
    onSubmit,
    isLoading,
    isError,
    error,
    isSuccess,
  }
}

