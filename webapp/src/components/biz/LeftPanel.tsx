import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
} from '@/shadcn/components/ui/sidebar'
import { userConvStore } from '@/utils/conv_manager'
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
