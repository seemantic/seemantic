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

export interface QueryResponseUpdate {
  delta_answer: string | null // If not null, it's the continuation of the answer. If null, keep the previous answer.
  search_result: Array<ApiSearchResult> | null // If null, keep the previous result. If not null, it replaces the previous search result.
}

export interface ApiSearchResultChunk {
  content: string // Content of the chunk
  start_index_in_doc: number // Start index in the document
  end_index_in_doc: number // End index in the document
}

export interface ApiSearchResult {
  uri: string // URI of the document
  chunks: Array<ApiSearchResultChunk> // List of chunks in the document
}

export interface ApiDocumentDelete {
  uri: string // Relative path within the source
}
export interface ApiDocumentSnippet {
  uri: string // Relative path within the source
  status: 'pending' | 'indexing' | 'indexing_success' | 'indexing_error' // Status of the document
  error_status_message?: string | null // Optional error message
  last_indexing?: string | null // ISO 8601 string for the last indexing timestamp
}

export interface ApiExplorer {
  documents: Array<ApiDocumentSnippet> // List of ApiDocumentSnippet objects
}

export const get_explorer = (): Promise<ApiExplorer> =>
  fetchApi<ApiExplorer>('explorer')
