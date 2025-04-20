import { Outlet, createFileRoute } from '@tanstack/react-router'
import LeftPanel from '@/components/biz/leftPanel'
import { SidebarProvider, SidebarTrigger } from '@/components/ui/sidebar'
import { get_explorer } from '@/utils/api'

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
