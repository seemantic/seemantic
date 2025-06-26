import LeftPanel from '@/components/biz/LeftPanel'
import { SidebarProvider, SidebarTrigger } from '@/shadcn/components/ui/sidebar'
import { userConvStore } from '@/utils/conv_manager'
import { Outlet, createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/_app')({
  loader: async () => {
    await userConvStore.getState().listenToDocumentEvents()
  },
  component: RouteComponent,
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
