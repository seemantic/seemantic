import ConvPanel from '@/components/biz/ConvPanel' // Import the new component
import DocPanel from '@/components/biz/DocPanel'
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from '@/shadcn/components/ui/resizable'
import { getParsedDocument } from '@/utils/api'
import { createFileRoute } from '@tanstack/react-router'

type ConvSearchParams = {
  docUri: string | null
}

export const Route = createFileRoute('/_app/conv/$convId')({
  component: RouteComponent,
  validateSearch: (search: Record<string, unknown>): ConvSearchParams => {
    const { docUri } = search
    return {
      docUri: typeof docUri === 'string' ? docUri : null,
    }
  },
  loaderDeps: ({ search }: { search: ConvSearchParams }) => ({
    docUri: search.docUri,
  }),
  loader: async ({ deps: { docUri } }) => {
    const doc = docUri ? await getParsedDocument(docUri) : null

    return { doc }
  },
})

function RouteComponent() {
  // Get the route params and search params
  const { doc } = Route.useLoaderData()
  const { convId } = Route.useParams()

  if (doc === null) {
    return (
      <div className="flex h-screen w-full">
        <ConvPanel convId={convId} />
      </div>
    )
  } else {
    return (
      <div className="flex h-screen w-full">
        <ResizablePanelGroup direction="horizontal">
          <ResizablePanel>
            {/* Use the new ConvPanel component */}
            <ConvPanel convId={convId} />
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
