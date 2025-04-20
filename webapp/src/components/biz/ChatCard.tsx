import { Input } from '@/shadcn/components/ui/input' // Adjust the import path based on your project structure
import { useNavigate } from '@tanstack/react-router' // Import useNavigate
import { ChevronRight } from 'lucide-react'
import React, { useState } from 'react'
import { Button } from '../../shadcn/components/ui/button'

const ChatCard: React.FC = () => {
  const [inputValue, setInputValue] = useState('') // State for input value
  const navigate = useNavigate() // Get the navigate function from TanStack Router

  const handleNavigate = () => {
    if (inputValue.trim()) {
      navigate({
        to: '/search',
        search: { q: inputValue },
      })
    }
  }

  return (
    <div className="flex items-center w-full max-w-120 p-4">
      <Input
        type="text"
        placeholder="Question or search term"
        value={inputValue} // Bind input value to state
        onChange={(e) => setInputValue(e.target.value)} // Update state on input change
        onKeyDown={(e) => e.key === 'Enter' && handleNavigate()} // Compact "Enter" key press handling
      />
      <div className="ml-2">
        <Button
          variant="default"
          onClick={handleNavigate} // Use the shared navigation function
        >
          <ChevronRight />
        </Button>
      </div>
    </div>
  )
}

export default ChatCard
