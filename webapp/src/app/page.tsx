import LeftPanel from "@/components/biz/left-panel";
import MainNewChat from "@/components/biz/main-newchat";
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";

export default function Home() {
  return (
    <SidebarProvider>
      <LeftPanel />
      <SidebarTrigger />
      <MainNewChat />
    </SidebarProvider>
  );
}
