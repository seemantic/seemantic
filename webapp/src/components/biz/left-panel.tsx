'use client'; // Mark as a Client Component
import { Sidebar, SidebarContent, SidebarGroup, SidebarGroupContent, SidebarGroupLabel, SidebarMenu, SidebarMenuButton, SidebarMenuItem, SidebarProvider } from "@/components/ui/sidebar"
import { useQuery } from "@tanstack/react-query";
import { get_explorer, ApiExplorer, ApiDocumentSnippet } from "@/utils/api";



interface LeftPanelProps {
    className?: string; // Optional className for custom styles
}

export default function LeftPanel({ className }: LeftPanelProps) {

    const { data, isLoading, error } = useQuery<ApiExplorer>({
        queryKey: ["apiExplorer"],
        queryFn: get_explorer,
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