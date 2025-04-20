import { createFileRoute } from '@tanstack/react-router'
import ChatCard from '@/components/biz/ChatCard'

export const Route = createFileRoute('/_app/')({
  component: App,
})

function App() {
  return (
    <div className="flex justify-center items-center h-screen w-full">
      <ChatCard />
    </div>
  )
}
