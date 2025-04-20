import LeftPanel from '@/components/biz/LeftPanel'
import { SidebarProvider, SidebarTrigger } from '@/shadcn/components/ui/sidebar'
import { get_explorer } from '@/utils/api'
import { Outlet, createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/_app')({
  component: RouteComponent,
  loader: async () => get_explorer(),
})

function RouteComponent() {
  return (
    <SidebarProvider>
      <LeftPanel />
      <SidebarTrigger />
      <Outlet />
    </SidebarProvider>
  )
}
