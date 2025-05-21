import { create } from 'zustand'
import { immer } from 'zustand/middleware/immer'

import { subscribeToQuery } from './api'
import type {
  ApiQuery,
  ApiQueryMessage,
  ApiQueryReponsePair,
  ApiQueryResponseMessage,
  ApiQueryResponseUpdate,
} from './api_data'

export interface Conversation {
  queryResponsePairs: Record<string, ApiQueryReponsePair>
  queryResponsePairIds: Array<string>
}

export interface ConversationStoreState {
  conversations: Record<string, Conversation>
}

export interface ConversationStoreActions {
  createConversation: () => string
  appendApiQueryResponsePair: (convId: string, query: ApiQueryMessage) => void // init an new pair with an empty Response

  updateResponse: (
    convId: string,
    pairId: string,
    message: ApiQueryResponseMessage,
  ) => void
}

export const userConvStore = create<
  ConversationStoreState & ConversationStoreActions
>()(
  immer((set, get) => ({
    conversations: {},
    createConversation: () => {
      const convId = crypto.randomUUID()
      set((state) => {
        state.conversations[convId] = {
          queryResponsePairs: {},
          queryResponsePairIds: [],
        }
      })
      return convId
    },

    updateResponse: (
      convId: string,
      pairId: string,
      message: ApiQueryResponseMessage,
    ) => {
      set((state) => {
        const conversation = state.conversations[convId]
        if (conversation) {
          const pair = conversation.queryResponsePairs[pairId]
          if (pair) {
            pair.response = message
          }
        }
      })
    },

    appendApiQueryResponsePair: (convId: string, query: ApiQueryMessage) => {
      const pairId = crypto.randomUUID()
      const currentConversation = get().conversations[convId]
      const previousMessages = currentConversation.queryResponsePairIds.map(
        (key) => currentConversation.queryResponsePairs[key],
      )

      // Add user message to store
      set((state) => {
        const conversation = state.conversations[convId]
        if (conversation) {
          conversation.queryResponsePairs[pairId] = {
            query,
            response: {
              answer: '',
              search_results: [],
              chat_messages_exchanged: [],
            },
          }
          conversation.queryResponsePairIds.push(pairId)
        }
      })

      // Prepare ApiQuery
      const apiQuery: ApiQuery = {
        query: query,
        previous_messages: previousMessages,
      }

      const abortController = new AbortController()
      const accumulatedResponse: ApiQueryResponseMessage = {
        answer: '',
        search_results: [],
        chat_messages_exchanged: [],
      }

      // Asynchronously subscribe to query updates
      const storeActions = userConvStore.getState()

      subscribeToQuery(
        apiQuery,
        abortController,
        (update: ApiQueryResponseUpdate) => {
          if (update.delta_answer) {
            accumulatedResponse.answer += update.delta_answer
          }
          if (update.search_results && update.search_results.length > 0) {
            accumulatedResponse.search_results = update.search_results
          }
          if (
            update.chat_messages_exchanged &&
            update.chat_messages_exchanged.length > 0
          ) {
            accumulatedResponse.chat_messages_exchanged =
              update.chat_messages_exchanged
          }

          // Create a new object for the store update to ensure change detection
          const responseForStore = { ...accumulatedResponse }

          // Subsequent updates: update the existing assistant's message
          storeActions.updateResponse(convId, pairId, responseForStore)
        },
      )
    },
  })),
)
