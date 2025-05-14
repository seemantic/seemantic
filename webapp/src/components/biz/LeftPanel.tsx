import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from '@/shadcn/components/ui/sidebar'
import { subscribeToDocumentEvents } from '@/utils/api'
import type { ApiDocumentDelete, ApiDocumentSnippet } from '@/utils/api_data'
import { Link, getRouteApi } from '@tanstack/react-router'
import React from 'react'

export default function LeftPanel() {
  const route = getRouteApi('/_app')
  const data = route.useLoaderData()

  const [docs, setDocs] = React.useState<Array<ApiDocumentSnippet>>(
    data.documents,
  )

  React.useEffect(() => {
    const abortController = new AbortController()

    const connect = async () => {
      await subscribeToDocumentEvents(
        abortController,
        (doc: ApiDocumentSnippet) => {
          // Update the documents state with the new document
          setDocs((prevDocs) => {
            const existingDoc = prevDocs.find((d) => d.uri === doc.uri)
            if (existingDoc) {
              return prevDocs.map((d) => (d.uri === doc.uri ? doc : d))
            } else {
              return [...prevDocs, doc]
            }
          })
        },
        (deleted: ApiDocumentDelete) => {
          // Remove the deleted document from the documents state
          setDocs((prevDocs) =>
            prevDocs.filter((doc) => doc.uri !== deleted.uri),
          )
        },
      )
    }

    connect()

    // Cleanup function to abort the connection when the component unmounts or query changes
    return () => {
      abortController.abort()
    }
  }, [data])

  return (
    <Sidebar>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Application</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {docs.map((doc) => (
                <Link
                  to="/doc/$docUri"
                  params={{ docUri: encodeURIComponent(doc.uri) }}
                  key={doc.uri}
                >
                  <SidebarMenuItem key={doc.uri}>
                    <SidebarMenuButton className="h-20">
                      <a href={doc.uri} className="flex flex-col text-left">
                        <span className="text-sm font-medium">{doc.uri}</span>
                        <span className="text-xs text-muted-foreground">
                          {doc.status}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          {doc.last_indexing}
                        </span>
                      </a>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                </Link>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  )
}
