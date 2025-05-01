import ConvPanel from '@/components/biz/ConvPanel' // Import the new component
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from '@/shadcn/components/ui/resizable'
import { db } from '@/utils/db'
import { createFileRoute } from '@tanstack/react-router'

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

function RouteComponent() {
  return (
    <div className="flex h-screen w-full">
      <ResizablePanelGroup direction="horizontal">
        <ResizablePanel>
          {/* Use the new ConvPanel component */}
          <ConvPanel />
        </ResizablePanel>
        <ResizableHandle withHandle />
        <ResizablePanel>Two</ResizablePanel>
      </ResizablePanelGroup>
    </div>
  )
}
