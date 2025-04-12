import React from 'react';
import ChatCard from './ChatCard'; // Import the new ChatCard component

const MainNewChat: React.FC = () => {
    return (
        <div className="flex justify-center items-center h-screen w-full">
            <ChatCard />
        </div>
    );
};

export default MainNewChat;
