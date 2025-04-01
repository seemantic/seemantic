import { Sidebar, SidebarContent, SidebarGroup, SidebarGroupContent, SidebarGroupLabel, SidebarMenu, SidebarMenuButton, SidebarMenuItem, SidebarProvider } from "@/components/ui/sidebar"
import { cn } from "@/lib/utils"
import { useQuery } from "@tanstack/react-query";
import { use, useEffect, useState } from "react";
import { fetchApi } from "@/utils/api";


export interface ApiDocumentSnippet {
    uri: string; // Relative path within the source
    status: "pending" | "indexing" | "indexing_success" | "indexing_error"; // Status of the document
    error_status_message?: string | null; // Optional error message
    last_indexing?: string | null; // ISO 8601 string for the last indexing timestamp
}

export interface ApiExplorer {
    documents: ApiDocumentSnippet[]; // List of ApiDocumentSnippet objects
}

interface LeftPanelProps {
    className?: string; // Optional className for custom styles
}

export default function LeftPanel({ className }: LeftPanelProps) {

    const { data, isLoading, error } = useQuery<ApiExplorer>({
        queryKey: ["apiExplorer"],
        queryFn: () => fetchApi<ApiExplorer>("explorer"),
    });

    /*     useEffect(() => {
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
        }, []); */

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