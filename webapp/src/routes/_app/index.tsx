import ChatCard from '@/components/biz/ChatCard'
import { userConvStore } from '@/utils/conv_manager'
import { createFileRoute, useNavigate } from '@tanstack/react-router'

export const Route = createFileRoute('/_app/')({
  component: App,
})

function App() {
  const navigate = useNavigate()

  const createConversation = userConvStore((state) => state.createConversation)
  const appendApiQueryResponsePair = userConvStore(
    (state) => state.appendApiQueryResponsePair,
  )

  const handleChatSubmit = async (query: string) => {
    const uuid = await createConversation()
    appendApiQueryResponsePair(uuid, {
      content: query,
    })
    navigate({
      to: '/conv/' + uuid,
    })
  }

  return (
    <div className="flex justify-center items-center h-screen w-full">
      <ChatCard onSubmit={handleChatSubmit} />
    </div>
  )
}
