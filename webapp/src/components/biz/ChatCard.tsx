import React, { useState } from 'react';
import { Input } from "@/components/ui/input"; // Adjust the import path based on your project structure
import { Button } from '../ui/button';
import { ChevronRight } from "lucide-react";
import { useNavigate } from '@tanstack/react-router'; // Import useNavigate
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';

const ChatCard: React.FC = () => {
    const [inputValue, setInputValue] = useState(""); // State for input value
    const navigate = useNavigate(); // Get the navigate function from TanStack Router

    const handleNavigate = () => {
        if (inputValue.trim()) {
            navigate({
                to: "/search",
                search: { q: inputValue },
            });
        }
    };

    return (
        <Card>
            <CardHeader className="text-center">
                <CardTitle>Talk to your documents</CardTitle>
            </CardHeader>
            <CardContent className="flex items-center">
                <Input
                    type="text"
                    placeholder="Question or search term"
                    className="w-120"
                    value={inputValue} // Bind input value to state
                    onChange={(e) => setInputValue(e.target.value)} // Update state on input change
                    onKeyDown={(e) => e.key === "Enter" && handleNavigate()} // Compact "Enter" key press handling
                />
                <div className="ml-2">
                    <Button
                        variant="default"
                        onClick={handleNavigate} // Use the shared navigation function
                    >
                        <ChevronRight />
                    </Button>
                </div>
            </CardContent>
        </Card>
    );
};

export default ChatCard;