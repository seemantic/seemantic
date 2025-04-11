import LeftPanel from '@/components/biz/left-panel'
import { SidebarProvider, SidebarTrigger } from '@/components/ui/sidebar'
import { createFileRoute, Outlet } from '@tanstack/react-router'

export const Route = createFileRoute('/_app')({
  component: RouteComponent,
})

function RouteComponent() {
  return <SidebarProvider>
    <LeftPanel />
    <SidebarTrigger />
    <Outlet />
  </SidebarProvider>
}
