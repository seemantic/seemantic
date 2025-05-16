import ConvPanel from '@/components/biz/ConvPanel' // Import the new component
import DocPanel from '@/components/biz/DocPanel'
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from '@/shadcn/components/ui/resizable'
import { getParsedDocument } from '@/utils/api'
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

    // Load conv and doc in parallel
    const [conv, doc] = await Promise.all([
      db.conversations.get({ uuid: convId }),
      docUri ? getParsedDocument(docUri) : Promise.resolve(null),
    ])

    // if conv is undefined, throw a 404 error
    if (!conv) {
      throw new Response('Not Found', {
        status: 404,
        statusText: 'Not Found',
      })
    }

    return { conv, doc }
  },
})

function RouteComponent() {
  // Get the route params and search params
  const { conv, doc } = Route.useLoaderData()

  if (doc === null) {
    return (
      <div className="flex h-screen w-full">
        <ConvPanel conv={conv} />
      </div>
    )
  } else {
    return (
      <div className="flex h-screen w-full">
        <ResizablePanelGroup direction="horizontal">
          <ResizablePanel>
            {/* Use the new ConvPanel component */}
            <ConvPanel conv={conv} />
          </ResizablePanel>
          <ResizableHandle withHandle />
          <ResizablePanel>
            <DocPanel doc={doc}></DocPanel>
          </ResizablePanel>
        </ResizablePanelGroup>
      </div>
    )
  }
}
