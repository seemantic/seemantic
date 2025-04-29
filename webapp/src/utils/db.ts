import type { EntityTable } from 'dexie'
import Dexie from 'dexie'
import type { ApiQueryReponsePair } from './api_data'

export interface Conversation {
  id?: number // Auto-incremented primary key
  label: string // A user-defined label or generated title for the conversation
  timestamp: Date // Timestamp of the last interaction or creation
  exchanges: Array<ApiQueryReponsePair>
}

export class SeemanticDatabase extends Dexie {
  // Declare implicit table properties.
  // (Map interface types to tables, specifying primary key name <string> and value <any>).
  conversations!: EntityTable<
    Conversation,
    'id' // Primary key "id" (for the typings only)
  >

  constructor() {
    super('SeemanticDatabase') // Database name
    this.version(1).stores({
      // Schema declaration: primary key "id" is auto-incremented.
      // We can add more indexes here later if needed, separated by commas (e.g., '++id, label, timestamp')
      conversations: '++id, timestamp',
    })
  }
}

// Instantiate the database
export const db = new SeemanticDatabase()
