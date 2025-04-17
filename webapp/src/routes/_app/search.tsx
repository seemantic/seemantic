import { createFileRoute, getRouteApi } from '@tanstack/react-router'
import ChatCard from '../../components/biz/ChatCard' // Adjust the import path as needed
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from '@/components/ui/resizable'

type SearchParams = {
  q: string
}

export const Route = createFileRoute('/_app/search')({
  component: RouteComponent,
  validateSearch: (search: Record<string, unknown>): SearchParams => {
    return { q: (search.q as string) || '' }
  },
})

const routeApi = getRouteApi('/_app/search')

function RouteComponent() {
  const searchParams = routeApi.useSearch()
  const { q } = searchParams

  return (
    <div className="flex h-screen w-full">
      <ResizablePanelGroup direction="horizontal">
        <ResizablePanel>
          <div className="flex flex-col h-full">
            <div className="flex-1">{q}</div>
            <div className="w-full flex justify-center">
              <ChatCard />
            </div>
          </div>
        </ResizablePanel>
        <ResizableHandle withHandle />
        <ResizablePanel>Two</ResizablePanel>
      </ResizablePanelGroup>
    </div>
  )
}
