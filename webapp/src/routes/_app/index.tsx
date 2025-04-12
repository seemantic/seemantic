import { createFileRoute } from '@tanstack/react-router'
import MainNewChat from "@/components/biz/main-newchat";

export const Route = createFileRoute('/_app/')({
  component: App
})

function App() {

  return (
    <MainNewChat />
  )
}

