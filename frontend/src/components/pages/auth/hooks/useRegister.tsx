import { useMutation } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { yupResolver } from '@hookform/resolvers/yup'
import { toast } from 'react-toastify'
import { signupSchema } from '../schema'
import { registerUser, type RegisterResponse } from '../requests'
import type { SignupFormData } from '../types'
import type { AxiosError } from 'axios'

interface ErrorResponse {
  message: string
}

export const useRegister = () => {
  const navigate = useNavigate()
  // No longer need setUser and setIsAuthenticated - user must verify email first

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<SignupFormData>({
    resolver: yupResolver(signupSchema),
  })

  const {
    mutateAsync,
    isPending: isLoading,
    isError,
    error,
    isSuccess,
  } = useMutation<RegisterResponse, AxiosError<ErrorResponse>, SignupFormData>({
    mutationFn: registerUser,
    onSuccess: (data) => {
      // NO AUTO-LOGIN - User must verify email first
      // Do NOT set user in store or setIsAuthenticated

      // Save email to localStorage for check-email page
      localStorage.setItem('verificationEmail', data.user.email)

      // Show success message
      toast.success('Registration successful! Please check your email to verify your account.')

      // Navigate to check-email page instead of builder
      navigate('/auth/check-email')
    },
    onError: (error) => {
      const message = error.response?.data?.message || error.message || 'Registration failed'
      console.error('Registration error:', message)
      toast.error(message)
    },
  })

  const onSubmit = async (data: SignupFormData) => {
    await mutateAsync(data)
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

