import type {
  ApiDocumentDelete,
  ApiDocumentSnippet,
  ApiExplorer,
  ApiQuery,
  ApiQueryResponseUpdate,
} from '@/utils/api_data'
import { fetchEventSource } from '@microsoft/fetch-event-source'

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

export const subscribeToQuery = async (
  query: ApiQuery,
  abortController: AbortController,
  onUpdate: (update: ApiQueryResponseUpdate) => void,
): Promise<void> => {
  await fetchEventSource(`${apiUrl}/queries`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json', // Use application/json for the request body
      Accept: 'text/event-stream', // Specify we accept SSE
    },
    body: JSON.stringify(query), // Send the query as JSON
    signal: abortController.signal,
    onmessage: (event) => {
      const queryResponseUpdate: ApiQueryResponseUpdate = JSON.parse(event.data)
      onUpdate(queryResponseUpdate)
    },
  })
}

export const subscribeToDocumentEvents = async (
  query: ApiQuery,
  abortController: AbortController,
  onUpdate: (update: ApiDocumentSnippet) => void,
  onDelete: (update: ApiDocumentDelete) => void,
): Promise<void> => {
  await fetchEventSource(`${apiUrl}/document_events`, {
    method: 'GET',
    headers: {
      Accept: 'text/event-stream', // Specify we accept SSE
    },
    body: JSON.stringify(query), // Send the query as JSON
    signal: abortController.signal,
    onmessage: (event) => {
      if (event.data === 'delete') {
        const documentDelete: ApiDocumentDelete = JSON.parse(event.data)
        onDelete(documentDelete)
      } else {
        const documentSnippet: ApiDocumentSnippet = JSON.parse(event.data)
        onUpdate(documentSnippet)
      }
    },
  })
}
