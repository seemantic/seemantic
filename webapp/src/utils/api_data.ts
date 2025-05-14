export interface ApiDocumentSnippet {
  uri: string
  status: 'pending' | 'indexing' | 'indexing_success' | 'indexing_error'
  error_status_message: string | null
  last_indexing: string | null // Assuming datetime is serialized as string (e.g., ISO 8601)
}

export interface ApiDocumentDelete {
  uri: string
}

export interface ApiExplorer {
  documents: Array<ApiDocumentSnippet>
}

export interface ApiSearchResultChunk {
  content: string
  start_index_in_doc: number
  end_index_in_doc: number
}

export interface ApiSearchResult {
  document_uri: string
  chunks: Array<ApiSearchResultChunk>
}

export interface ApiChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface ApiQueryResponseUpdate {
  delta_answer: string | null
  search_result: Array<ApiSearchResult> | null
  chat_messages_exchanged: Array<ApiChatMessage> | null
}

export interface ApiQueryResponseMessage {
  answer: string
  search_result: Array<ApiSearchResult>
  chat_messages_exchanged: Array<ApiChatMessage>
}

export interface ApiQueryMessage {
  content: string
}

export interface ApiQueryReponsePair {
  query: ApiQueryMessage
  response: ApiQueryResponseMessage
}

export interface ApiQuery {
  query: ApiQueryMessage
  previous_messages: Array<ApiQueryReponsePair>
}

export interface ApiParsedDocument {
  hash: string
  markdown_content: string
}
