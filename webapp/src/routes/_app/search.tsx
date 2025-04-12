import { createFileRoute, getRouteApi } from '@tanstack/react-router'
import ChatCard from '../../components/biz/ChatCard' // Adjust the import path as needed
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from '@/components/ui/resizable'

type SearchParams = {
  q: string
}

export const Route = createFileRoute('/_app/search')({
  component: RouteComponent,
  validateSearch: (search: Record<string, unknown>): SearchParams => {
    return { q: search.q as string || '' }
  },
})

const routeApi = getRouteApi('/_app/search')

function RouteComponent() {
  const searchParams = routeApi.useSearch()
  const { q } = searchParams

  return (

    <ResizablePanelGroup direction="horizontal">
      <ResizablePanel>      <div className="flex justify-center items-center h-screen w-full">
        <ChatCard />
      </div></ResizablePanel>
      <ResizableHandle />
      <ResizablePanel>Two</ResizablePanel>
    </ResizablePanelGroup>

  )
}
