import { useMutation } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { toast } from 'react-toastify'
import { useUserStore } from '../../../../../store/user.store'
import { logoutUser, type LogoutResponse } from '../requests'
import type { AxiosError } from 'axios'

interface ErrorResponse {
  message: string
}

export const useLogout = () => {
  const navigate = useNavigate()
  const {clearUser, setIsAuthenticated} = useUserStore((state) => state)

  const {
    mutateAsync,
    isPending: isLoading,
    isError,
    error,
  } = useMutation<LogoutResponse, AxiosError<ErrorResponse>>({
    mutationFn: logoutUser,
    onSuccess: () => {
      // ניקוי המשתמש מה-store
      clearUser()
      setIsAuthenticated(false)
      // הצגת הודעת הצלחה
      toast.success('Logged out successfully')
      
      // ניווט לדף ההתחברות
      navigate('/auth/signin')
    },
    onError: (error) => {
      const message = error.response?.data?.message || error.message || 'Logout failed'
      console.error('Logout error:', message)
      toast.error(message)
    },
  })

  const logout = async () => {
    await mutateAsync()
  }

  return {
    logout,
    isLoading,
    isError,
    error,
  }
}

