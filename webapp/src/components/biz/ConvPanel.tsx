import ChatCard from '@/components/biz/ChatCard' // Adjust the import path as needed
import StreamedResponsePanel from '@/components/biz/StreamedResponsePanel'
import type { ApiQuery } from '@/utils/api_data'
import { createConversation } from '@/utils/db'
import { getRouteApi, useNavigate } from '@tanstack/react-router'

// Assuming the route API is accessible here, otherwise props need to be passed
const routeApi = getRouteApi('/_app/conv/$convId')

// TODO: passer un UID (path) et la query str (search)
// c'est ce composant qui va storer en base

export default function ConvPanel() {
  const conv = routeApi.useLoaderData()
  const { convId } = routeApi.useParams() // Get convId from params
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
      <StreamedResponsePanel key={convId} query={apiQuery} />
      <div className="w-full flex justify-center">
        <ChatCard onSubmit={handleChatSubmit} />
      </div>
    </div>
  )
}
