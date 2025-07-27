import type {
  ApiDocumentDelete,
  ApiDocumentSnippet,
  ApiExplorer,
  ApiParsedDocument,
  ApiQuery,
  ApiQueryResponseUpdate,
  DeleteFileRequest,
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

export const deleteApi = async (uri: string): Promise<void> => {
  const url = `${apiUrl}/${uri}`
  const response = await fetch(url, {
    method: 'DELETE',
  })
  if (!response.ok) {
    throw new Error(
      `HTTP error! Status: ${response.status} - ${response.statusText}`,
    )
  }
}

export const postToApi = async <TInput, TOutput>(
  route: string,
  payload: TInput,
): Promise<TOutput> => {
  const url = `${apiUrl}/${route}`
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })
  if (!response.ok) {
    throw new Error(
      `HTTP error! Status: ${response.status} - ${response.statusText}`,
    )
  }
  return (await response.json()) as TOutput
}

export const get_explorer = (): Promise<ApiExplorer> =>
  fetchApi<ApiExplorer>('explorer')

export const getParsedDocument = (
  encoded_uri: string,
): Promise<ApiParsedDocument> =>
  fetchApi<ApiParsedDocument>(`documents/${encoded_uri}?format=parsed`)

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
  abortController: AbortController,
  onUpdate: (update: ApiDocumentSnippet) => void,
  onDelete: (update: ApiDocumentDelete) => void,
): Promise<void> => {
  await fetchEventSource(`${apiUrl}/document_events`, {
    method: 'GET',
    headers: {
      Accept: 'text/event-stream', // Specify we accept SSE
    },
    signal: abortController.signal,
    onmessage: (event) => {
      if (event.event === 'delete') {
        const documentDelete: ApiDocumentDelete = JSON.parse(event.data)
        onDelete(documentDelete)
      } else if (event.event === 'update') {
        const documentSnippet: ApiDocumentSnippet = JSON.parse(event.data)
        onUpdate(documentSnippet)
      }
    },
  })
}

export const deleteFile = async (req: DeleteFileRequest): Promise<void> => {
  await deleteApi(`documents/${encodeURIComponent(req.uri)}`)
}

// upload a file to s3 by getting a presigned url and then uploading the file
export const uploadFile = async (
  uri: string,
  file: File,
): Promise<void> => {
  // Use postToApi to get the presigned URL
  const { url: presignedUrl } = await postToApi<{ uri: string }, { url: string }>('documents/presigned_url', { uri: uri })

  // Now upload the file to the presigned URL
  const uploadResponse = await fetch(presignedUrl, {
    method: 'PUT',
    body: file,
  })

  if (!uploadResponse.ok) {
    throw new Error(
      `File upload failed! Status: ${uploadResponse.status} - ${uploadResponse.statusText}`,
    )
  }
}
