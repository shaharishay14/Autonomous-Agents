import { useMutation } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { toast } from 'react-toastify'
import {
  verifyEmailWithToken,
  type VerifyEmailWithTokenData,
  type VerifyEmailWithTokenResponse
} from '../requests'
import type { AxiosError } from 'axios'

interface ErrorResponse {
  error?: string
  message?: string
}

export const useVerifyEmail = () => {
  const navigate = useNavigate()

  const {
    mutateAsync,
    isPending: isLoading,
    isError,
    error,
    isSuccess,
  } = useMutation<VerifyEmailWithTokenResponse, AxiosError<ErrorResponse>, VerifyEmailWithTokenData>({
    mutationFn: verifyEmailWithToken,
    onSuccess: (data) => {
      console.log('Email verified:', data.detail)
      toast.success('Email verified successfully! Redirecting to login...')
      // Success - redirect to sign in
      setTimeout(() => {
        navigate('/auth/signin')
      }, 2000)
    },
    onError: (error) => {
      const message = error.response?.data?.error || error.response?.data?.message || error.message || 'Failed to verify email'
      console.error('Verify email error:', message)
      toast.error(message)
    },
  })

  const verifyWithToken = async (userId: string, token: string) => {
    await mutateAsync({ userId, token })
  }

  return {
    verifyWithToken,
    isLoading,
    isError,
    error,
    isSuccess,
  }
}

