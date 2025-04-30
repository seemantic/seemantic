import type { EntityTable } from 'dexie'
import Dexie from 'dexie'
import type { ApiQueryMessage, ApiQueryResponseMessage } from './api_data'

export interface QueryResponsePair {
  query: ApiQueryMessage
  response?: ApiQueryResponseMessage
}

export interface ConversationEntry {
  uuid: string // Auto-incremented primary key
  label: string // A user-defined label or generated title for the conversation
  lastInteraction: Date // Timestamp of the last interaction
  queryResponsePairs: Array<QueryResponsePair>
}

class SeemanticDatabase extends Dexie {
  // Declare implicit table properties.
  // (Map interface types to tables, specifying primary key name <string> and value <any>).
  conversations!: EntityTable<ConversationEntry>

  constructor() {
    super('SeemanticDatabase') // Database name
    this.version(1).stores({
      conversations: '&uuid, label, lastInteraction',
    })
  }
}

// Instantiate the database
export const db = new SeemanticDatabase()

export const createConversation = async (query: string): Promise<string> => {
  const uuid = crypto.randomUUID() // Generate a unique identifier for the conversation
  // insert a new entry in db
  await db.conversations.add({
    uuid: uuid, // Unique identifier for the conversation
    label: query, // A user-defined label or generated title for the conversation
    lastInteraction: new Date(), // Timestamp of the last interaction
    queryResponsePairs: [
      {
        query: { content: query }, // The user's query
        response: undefined, // Placeholder for the response, to be filled later
      },
    ], // Initialize with an empty array
  })

  return uuid
}
