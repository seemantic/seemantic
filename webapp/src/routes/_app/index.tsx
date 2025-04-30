import ChatCard from '@/components/biz/ChatCard'
import { createConversation } from '@/utils/db'
import { createFileRoute, useNavigate } from '@tanstack/react-router'

export const Route = createFileRoute('/_app/')({
  component: App,
})

function App() {
  const navigate = useNavigate()

  const handleChatSubmit = async (query: string) => {
    const uuid = await createConversation(query)
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
