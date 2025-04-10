import { createFileRoute } from '@tanstack/react-router'
import LeftPanel from "@/components/biz/left-panel";
import MainNewChat from "@/components/biz/main-newchat";
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { get_explorer } from '@/utils/api';

export const Route = createFileRoute('/')({
  component: App,
  loader: async () => get_explorer()
})

function App() {
  
  return (
    <SidebarProvider>
      <LeftPanel />
      <SidebarTrigger />
      <MainNewChat />
    </SidebarProvider>
  )
}

