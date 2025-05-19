import { create } from 'zustand'
import { immer } from 'zustand/middleware/immer'

import type { ApiQueryMessage, ApiQueryResponseMessage } from './api_data'

export interface Conversation {
  messages: Record<string, ApiQueryMessage | ApiQueryResponseMessage>
  messageKeys: Array<string>
}

export interface ConversationStoreState {
  conversations: Record<string, Conversation>
}

export interface ConversationStoreActions {
  createConversation: (userMessage: string) => string
  appendMessage: (
    convId: string,
    message: ApiQueryMessage | ApiQueryResponseMessage,
  ) => string
  updateResponse: (
    convId: string,
    messageId: string,
    message: ApiQueryResponseMessage,
  ) => void
}

export const userStore = create<
  ConversationStoreState & ConversationStoreActions
>((set) => ({
  conversations: {},
  createConversation: (userMessage: string) => {
    const convId = crypto.randomUUID()
    set((state) => ({
      conversations: {
        ...state.conversations,
        [convId]: {
          messages: {
            [convId]: { content: userMessage },
          },
          messageKeys: [convId],
        },
      },
    }))
    return convId
  },
  appendMessage: (
    convId: string,
    message: ApiQueryMessage | ApiQueryResponseMessage,
  ) => {
    const messageId = crypto.randomUUID()
    set((state) => {
      const conversation = state.conversations[convId]
      return {
        conversations: {
          ...state.conversations,
          [convId]: {
            ...conversation,
            messages: {
              ...conversation.messages,
              [messageId]: message,
            },
            messageKeys: [...conversation.messageKeys, messageId],
          },
        },
      }
    })
    return messageId
  },
  updateResponse: (
    convId: string,
    messageId: string,
    message: ApiQueryResponseMessage,
  ) => {
    set((state) => {
      const conversation = state.conversations[convId]
      return {
        conversations: {
          ...state.conversations,
          [convId]: {
            ...conversation,
            messages: {
              ...conversation.messages,
              [messageId]: message,
            },
          },
        },
      }
    })
  },
}))
