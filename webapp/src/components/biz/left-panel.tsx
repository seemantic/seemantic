'use client'; // Mark as a Client Component
import { Sidebar, SidebarContent, SidebarGroup, SidebarGroupContent, SidebarGroupLabel, SidebarMenu, SidebarMenuButton, SidebarMenuItem, SidebarProvider } from "@/components/ui/sidebar"
import { useQuery } from "@tanstack/react-query";
import { get_explorer, ApiExplorer, ApiDocumentSnippet, ApiDocumentDelete, subscribeToSSE } from "@/utils/api";
import { useState, useEffect, use } from 'react';
import { subscribe } from "diagnostics_channel";


interface LeftPanelProps {
    className?: string; // Optional className for custom styles
}

export default function LeftPanel({ className }: LeftPanelProps) {

    const { data, isLoading, error } = useQuery<ApiExplorer>({
        queryKey: ["apiExplorer"],
        queryFn: get_explorer,
    });

    const [updates, setUpdates] = useState([]);

    useEffect(() => {
        return subscribeToSSE<ApiDocumentSnippet | ApiDocumentDelete>("document_events", (eventType, eventData) => {
            console.log("Received event:", eventType, eventData);

        })
    }, []);

    const docs = data?.documents || [];

    return (
        <Sidebar >
            <SidebarContent>
                <SidebarGroup>
                    <SidebarGroupLabel>Application</SidebarGroupLabel>
                    <SidebarGroupContent>
                        <SidebarMenu>
                            {docs.map((doc) => (
                                <SidebarMenuItem key={doc.uri}>
                                    <SidebarMenuButton asChild>
                                        <a href={doc.uri}>
                                            <span>{doc.uri}</span>
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