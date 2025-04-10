'use client'; // Mark as a Client Component
import { Sidebar, SidebarContent, SidebarGroup, SidebarGroupContent, SidebarGroupLabel, SidebarMenu, SidebarMenuButton, SidebarMenuItem, SidebarProvider } from "@/components/ui/sidebar"
// import { get_explorer, ApiExplorer, ApiDocumentSnippet, ApiDocumentDelete, subscribeToSSE } from "@/utils/api";
// import { get_explorer, ApiExplorer, ApiDocumentSnippet, ApiDocumentDelete, subscribeToSSE } from "@/utils/api";
import type { ApiDocumentSnippet } from "@/utils/api";
// import { useState, useEffect } from 'react';


// interface LeftPanelProps {
//     className?: string; // Optional className for custom styles
// }

export default function LeftPanel() {

    // const { data, isLoading, error } = useQuery<ApiExplorer>({
    //     queryKey: ["apiExplorer"],
    //     queryFn: get_explorer,
    // });

    // const [updates, setUpdates] = useState([]);

    // useEffect(() => {
    //     return subscribeToSSE<ApiDocumentSnippet | ApiDocumentDelete>("document_events", (eventType, eventData) => {
    //         console.log("Received event:", eventType, eventData);

    //     })
    // }, []);

    // const docs = data?.documents || [];

    const docs: ApiDocumentSnippet[] = [
        {
            uri: "document1",
            status: "pending",
            error_status_message: null,
            last_indexing: null,
        },
        {
            uri: "document2",
            status: "indexing",
            error_status_message: null,
            last_indexing: null,
        },
        {
            uri: "document3",
            status: "indexing_success",
            error_status_message: null,
            last_indexing: null,
        },
        {
            uri: "document4",
            status: "indexing_error",
            error_status_message: "Error message here",
            last_indexing: null,
        },
    ];


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