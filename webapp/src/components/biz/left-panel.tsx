import { Sidebar, SidebarContent, SidebarGroup, SidebarGroupContent, SidebarGroupLabel, SidebarMenu, SidebarMenuButton, SidebarMenuItem, SidebarProvider } from "@/components/ui/sidebar"
import { cn } from "@/lib/utils"
import { use, useEffect, useState } from "react";

const items = [
    {
        title: "Home",
        url: "#",
    },
    {
        title: "very lon title blablabla holala holala holala",
        url: "#",
    }
]

interface LeftPanelProps {
    className?: string; // Optional className for custom styles
}

export default function LeftPanel({ className }: LeftPanelProps) {

    const [serverData, setServerData] = useState<any>(null); // State to store received data


    useEffect(() => {
        const eventSource = new EventSource("/api/sse");
        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            setServerData(data); // Update state with received data
        };
        eventSource.onerror = (error) => {
            console.error("Error occurred:", error);
            eventSource.close();
        };
        return () => {
            eventSource.close();
        };
    }, []);

    return (
        <Sidebar >
            <SidebarContent>
                <SidebarGroup>
                    <SidebarGroupLabel>Application</SidebarGroupLabel>
                    <SidebarGroupContent>
                        <SidebarMenu>
                            {items.map((item) => (
                                <SidebarMenuItem key={item.title}>
                                    <SidebarMenuButton asChild>
                                        <a href={item.url}>
                                            <span>{item.title}</span>
                                        </a>
                                    </SidebarMenuButton>
                                </SidebarMenuItem>
                            ))}
                        </SidebarMenu>
                    </SidebarGroupContent>
                </SidebarGroup>
            </SidebarContent>
        </Sidebar>
    )
}