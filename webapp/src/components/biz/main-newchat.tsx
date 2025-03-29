import React from 'react';
import { Input } from "@/components/ui/input"; // Adjust the import path based on your project structure
import { Button } from '../ui/button';
import { ChevronRight } from "lucide-react"

const MainNewChat: React.FC = () => {
    return (
        <div className="flex justify-center items-center h-screen w-full">
            <Input
                type="text"
                placeholder="Talk to your documents"
                className="w-120"
            />
            <div className="ml-2">
                <Button variant="default"><ChevronRight /></Button>
            </div>
        </div >
    );
};

export default MainNewChat;
