import React, { useState } from 'react';
import { Input } from "@/components/ui/input"; // Adjust the import path based on your project structure
import { Button } from '../ui/button';
import { ChevronRight } from "lucide-react";
import { Link } from '@tanstack/react-router'; // Import Link
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';

const MainNewChat: React.FC = () => {
    const [inputValue, setInputValue] = useState(""); // State for input value

    return (
        <div className="flex justify-center items-center h-screen w-full">
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
                    />
                    <div className="ml-2">
                        <Link
                            to="/search" // Replace with your search route
                            search={{ q: inputValue }} // Pass the input value as the "q" parameter
                            className="inline-flex"
                        >
                            <Button variant="default" disabled={!inputValue.trim()}>
                                <ChevronRight />
                            </Button>
                        </Link>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
};

export default MainNewChat;
