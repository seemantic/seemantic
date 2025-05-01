import ChatCard from '@/components/biz/ChatCard' // Adjust the import path as needed
import StreamedResponsePanel from '@/components/biz/StreamedResponsePanel'
import { createConversation } from '@/utils/db'
import { getRouteApi, useNavigate } from '@tanstack/react-router'

// Assuming the route API is accessible here, otherwise props need to be passed
const routeApi = getRouteApi('/_app/conv/$convId')

export default function ConvPanel() {
  const conv = routeApi.useLoaderData()
  const { convId } = routeApi.useParams() // Get convId from params
  const query = conv.queryResponsePairs[0].query.content
  const navigate = useNavigate()

  const handleChatSubmit = async (newQuery: string) => {
    const uuid = await createConversation(newQuery)
    navigate({
      to: '/conv/' + uuid,
    })
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1">{query}</div>
      <StreamedResponsePanel key={convId} query={query} />
      <div className="w-full flex justify-center">
        <ChatCard onSubmit={handleChatSubmit} />
      </div>
    </div>
  )
}
