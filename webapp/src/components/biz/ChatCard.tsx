import { Button } from '@/shadcn/components/ui/button'
import { Input } from '@/shadcn/components/ui/input' // Adjust the import path based on your project structure
import { ChevronRight } from 'lucide-react'
import React, { useState } from 'react'

// Define props interface
interface ChatCardProps {
  onSubmit: (value: string) => void // Function to handle submission in the parent
}

const ChatCard: React.FC<ChatCardProps> = ({ onSubmit }) => {
  const [inputValue, setInputValue] = useState('') // State for input value

  const handleSubmit = () => {
    if (inputValue.trim()) {
      onSubmit(inputValue) // Call the parent's submit handler
    }
  }

  return (
    <div className="flex items-center w-full max-w-120 p-4">
      <Input
        type="text"
        placeholder="Question or search term"
        value={inputValue} // Bind input value to state
        onChange={(e) => setInputValue(e.target.value)} // Update state on input change
        onKeyDown={(e) => e.key === 'Enter' && handleSubmit()} // Call internal submit handler
      />
      <div className="ml-2">
        <Button
          variant="default"
          onClick={handleSubmit} // Call internal submit handler
        >
          <ChevronRight />
        </Button>
      </div>
    </div>
  )
}

export default ChatCard
