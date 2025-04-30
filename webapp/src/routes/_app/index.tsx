import ChatCard from '@/components/biz/ChatCard'
import { db } from '@/utils/db'
import { createFileRoute, useNavigate } from '@tanstack/react-router'


export const Route = createFileRoute('/_app/')({
  component: App,
})

function App() {
  const navigate = useNavigate()

  const handleChatSubmit = async (query: string) => {

    const uuid = crypto.randomUUID() // Generate a unique identifier for the conversation
    // insert a new entry in db
    await db.conversations.add({
      uuid: uuid, // Unique identifier for the conversation
      label: query, // A user-defined label or generated title for the conversation
      lastInteraction: new Date(), // Timestamp of the last interaction
      queryResponsePairs: [{
        query: { content: query}, // The user's query
        response: undefined, // Placeholder for the response, to be filled later
      }], // Initialize with an empty array

      })

      navigate({
        to: '/search',
        search: { q: query },
      })
    }

  
  return (
    <div className="flex justify-center items-center h-screen w-full">
      <ChatCard onSubmit={handleChatSubmit} />
    </div>
  )
}
