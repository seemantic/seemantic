import React, { useState } from 'react';
import { Input } from "@/components/ui/input"; // Adjust the import path based on your project structure
import { Button } from '../ui/button';
import { ChevronRight } from "lucide-react";
import { useNavigate } from '@tanstack/react-router'; // Import useNavigate

const MainNewChat: React.FC = () => {
    const [inputValue, setInputValue] = useState(""); // State for input value
    const navigate = useNavigate(); // Initialize navigate function

    const handleButtonClick = () => {
        if (inputValue.trim()) {
            navigate({
                to: '/search', // Replace with your search route
                search: { q: inputValue }, // Pass the input value as the "q" parameter
            });
        }
    };

    return (
        <div className="flex justify-center items-center h-screen w-full">
            <Input
                type="text"
                placeholder="Talk to your documents"
                className="w-120"
                value={inputValue} // Bind input value to state
                onChange={(e) => setInputValue(e.target.value)} // Update state on input change
            />
            <div className="ml-2">
                <Button variant="default" onClick={handleButtonClick}>
                    <ChevronRight />
                </Button>
            </div>
        </div>
    );
};

export default MainNewChat;
