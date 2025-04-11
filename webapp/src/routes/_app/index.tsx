import { createFileRoute } from '@tanstack/react-router'
import MainNewChat from "@/components/biz/main-newchat";
import { get_explorer } from '@/utils/api';

export const Route = createFileRoute('/_app/')({
  component: App,
  loader: async () => get_explorer()
})

function App() {

  return (
    <MainNewChat />
  )
}

