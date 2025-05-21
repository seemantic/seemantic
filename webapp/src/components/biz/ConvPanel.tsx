import ChatCard from '@/components/biz/ChatCard' // Adjust the import path as needed
import StreamedResponsePanel from '@/components/biz/StreamedResponsePanel'
import { userConvStore } from '@/utils/conv_manager'
import { useNavigate } from '@tanstack/react-router'

type ConvPanelProps = {
  convId: string
}

export default function ConvPanel(props: ConvPanelProps) {
  const { convId } = props

  const navigate = useNavigate()
  const pairIds = userConvStore(
    (state) => state.conversations[convId].queryResponsePairIds,
  )

  const createConversation = userConvStore((state) => state.createConversation)
  const appendApiQueryResponsePair = userConvStore(
    (state) => state.appendApiQueryResponsePair,
  )

  const handleChatSubmit = (query: string) => {
    const newConvId = createConversation()
    appendApiQueryResponsePair(newConvId, {
      content: query,
    })
    navigate({
      to: '/conv/' + newConvId,
    })
  }

  return (
    <div className="flex flex-col h-full">
      {pairIds.map((pairId) => {
        return (
          <div key={pairId} className="flex flex-col">
            <StreamedResponsePanel
              key={pairId}
              convId={convId}
              queryResponsePairId={pairId}
            />
          </div>
        )
      })}
      <div className="w-full flex justify-center">
        <ChatCard onSubmit={handleChatSubmit} />
      </div>
    </div>
  )
}
