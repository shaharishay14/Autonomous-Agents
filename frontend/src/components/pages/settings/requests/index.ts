import { api } from '../../../../lib/axios'

export interface CreditsBalance {
  total_credits: number
  credits_used: number
}

export const getCreditsBalance = async (): Promise<CreditsBalance> => {
  const response = await api.get<CreditsBalance>('/credits/balance/')
  return response.data
}

