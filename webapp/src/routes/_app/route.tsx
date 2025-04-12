import LeftPanel from '@/components/biz/left-panel'
import { SidebarProvider, SidebarTrigger } from '@/components/ui/sidebar'
import { get_explorer } from '@/utils/api'
import { createFileRoute, Outlet } from '@tanstack/react-router'

export const Route = createFileRoute('/_app')({
  component: RouteComponent,
  loader: async () => get_explorer()
})

function RouteComponent() {
  return <SidebarProvider>
    <LeftPanel />
    <SidebarTrigger />
    <Outlet />
  </SidebarProvider>
}
