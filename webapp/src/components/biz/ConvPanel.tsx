import ChatCard from '@/components/biz/ChatCard' // Adjust the import path as needed
import StreamedResponsePanel from '@/components/biz/StreamedResponsePanel'
import type { ApiQuery } from '@/utils/api_data'
import type { ConversationEntry } from '@/utils/db'
import { createConversation } from '@/utils/db'
import { useNavigate } from '@tanstack/react-router'

type ConvPanelProps = {
  conv: ConversationEntry
}

export default function ConvPanel(props: ConvPanelProps) {
  const { conv } = props
  const queryMessage = conv.queryResponsePairs.at(-1)?.query
  // raise error if queryMessage is undefined
  if (queryMessage === undefined) {
    throw new Error('No query message found')
  }

  const apiQuery: ApiQuery = {
    query: queryMessage,
    previous_messages: [],
  }

  const navigate = useNavigate()

  const handleChatSubmit = async (query: string) => {
    const uuid = await createConversation(query)
    navigate({
      to: '/conv/' + uuid,
    })
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1">{queryMessage.content}</div>
      <StreamedResponsePanel key={conv.uuid} query={apiQuery} />
      <div className="w-full flex justify-center">
        <ChatCard onSubmit={handleChatSubmit} />
      </div>
    </div>
  )
}
