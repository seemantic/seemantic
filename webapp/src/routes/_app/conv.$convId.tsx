import StreamedResponsePanel from '@/components/biz/StreamedResponsePanel'
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from '@/shadcn/components/ui/resizable'
import { db } from '@/utils/db'
import { createFileRoute, getRouteApi } from '@tanstack/react-router'
import ChatCard from '../../components/biz/ChatCard' // Adjust the import path as needed

export const Route = createFileRoute('/_app/conv/$convId')({
  component: RouteComponent,
  loader: async ({ params }) => {
    const { convId } = params
    const conv = await db.conversations.get({ uuid: convId })
    // if conv is undefined, throw a 404 error
    if (!conv) {
      throw new Response('Not Found', {
        status: 404,
        statusText: 'Not Found',
      })
    }
    return conv
  },
})

const routeApi = getRouteApi('/_app/conv/$convId')

function RouteComponent() {
  const conv = routeApi.useLoaderData()
  const query = conv.queryResponsePairs[0].query.content

  const handleSubmit = () => {}

  return (
    <div className="flex h-screen w-full">
      <ResizablePanelGroup direction="horizontal">
        <ResizablePanel>
          <div className="flex flex-col h-full">
            <div className="flex-1">{query}</div>
            <StreamedResponsePanel query={query} />
            <div className="w-full flex justify-center">
              <ChatCard onSubmit={handleSubmit} />
            </div>
          </div>
        </ResizablePanel>
        <ResizableHandle withHandle />
        <ResizablePanel>Two</ResizablePanel>
      </ResizablePanelGroup>
    </div>
  )
}
