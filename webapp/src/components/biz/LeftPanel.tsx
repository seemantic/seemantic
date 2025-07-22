import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupAction,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
} from '@/shadcn/components/ui/sidebar'
import { userConvStore } from '@/utils/conv_manager'
import { FolderPlus } from 'lucide-react'
import { FileTree } from './FileTree'

export default function LeftPanel() {
  const docs = userConvStore((state) => state.documents)
  // get the values of docs as an array
  const docsArray = Object.values(docs)

  return (
    <Sidebar>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Seemantic</SidebarGroupLabel>
          <SidebarGroupAction
            title="New Folder"
            onClick={() => {
              // Dummy action
              alert('New Folder action clicked')
            }}
          >
            <FolderPlus /> <span className="sr-only">New Folder</span>
          </SidebarGroupAction>
          <SidebarGroupContent>
            <SidebarMenu>
              <FileTree docs={docsArray} />
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  )
}
