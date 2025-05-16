import ConvPanel from '@/components/biz/ConvPanel' // Import the new component
import DocPanel from '@/components/biz/DocPanel'
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from '@/shadcn/components/ui/resizable'
import { db } from '@/utils/db'
import { createFileRoute } from '@tanstack/react-router'

type ConvSearchParams = {
  docUri?: string
}

export const Route = createFileRoute('/_app/conv/$convId')({
  component: RouteComponent,
  validateSearch: (search: Record<string, unknown>): ConvSearchParams => {
    const { docUri } = search
    return {
      docUri: typeof docUri === 'string' ? docUri : undefined,
    }
  },
  loaderDeps: ({ search }: { search: ConvSearchParams }) => ({
    docUri: search.docUri,
  }),
  loader: async ({ params, deps: { docUri } }) => {
    const { convId } = params
    const conv = await db.conversations.get({ uuid: convId })
    // if conv is undefined, throw a 404 error
    if (!conv) {
      throw new Response('Not Found', {
        status: 404,
        statusText: 'Not Found',
      })
    }
    return { conv, docUri }
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
        <ResizablePanel>
          <DocPanel doc={null}></DocPanel>
        </ResizablePanel>
      </ResizablePanelGroup>
    </div>
  )
}
