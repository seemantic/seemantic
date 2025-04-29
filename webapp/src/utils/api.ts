import type { ApiExplorer } from '@/utils/api_data'

export const apiUrl = `${import.meta.env.VITE_API_URL}/api/v1`

export const fetchApi = async <T>(route: string): Promise<T> => {
  const url = `${apiUrl}/${route}`
  const response = await fetch(url)
  if (!response.ok) {
    throw new Error(
      `HTTP error! Status: ${response.status} - ${response.statusText}`,
    )
  }
  return (await response.json()) as T
}

export const get_explorer = (): Promise<ApiExplorer> =>
  fetchApi<ApiExplorer>('explorer')
