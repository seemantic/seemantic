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
  updateMessage: (
    convId: string,
    messageId: string,
    message: ApiQueryResponseMessage,
  ) => void
}

export const userStore = create<
  ConversationStoreState & ConversationStoreActions
>()(
  immer((set) => ({
    conversations: {},
    createConversation: (userMessage: string) => {
      const convId = crypto.randomUUID()
      set((state) => {
        state.conversations[convId] = {
          messages: {
            [convId]: { content: userMessage },
          },
          messageKeys: [convId],
        }
      })
      return convId
    },
    appendMessage: (
      convId: string,
      message: ApiQueryMessage | ApiQueryResponseMessage,
    ) => {
      const messageId = crypto.randomUUID()
      set((state) => {
        const conversation = state.conversations[convId]
        if (conversation) {
          conversation.messages[messageId] = message
          conversation.messageKeys.push(messageId)
        }
      })
      return messageId
    },
    updateMessage: (
      convId: string,
      messageId: string,
      message: ApiQueryMessage | ApiQueryResponseMessage,
    ) => {
      set((state) => {
        const conversation = state.conversations[convId]
        if (conversation && conversation.messages[messageId]) {
          conversation.messages[messageId] = message
        }
      })
    },
  })),
)
