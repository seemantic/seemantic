import '@/components/biz/FileTree.css' // Assuming you have a CSS file for styles
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from '@/shadcn/components/ui/hover-card'
import type { ApiDocumentSnippet } from '@/utils/api_data'
import {
  hotkeysCoreFeature,
  selectionFeature,
  syncDataLoaderFeature,
} from '@headless-tree/core'
import { useTree } from '@headless-tree/react'
import { useNavigate } from '@tanstack/react-router'
import cn from 'classnames'
import { Check, CircleX, LoaderCircle } from 'lucide-react'

type TreeItem = {
  uri: string
  name: string
  type: 'file' | 'folder'
  childrenPaths: Array<string>
}

type FileItem = TreeItem & {
  type: 'file'
  doc: ApiDocumentSnippet
}

type FolderItem = TreeItem & {
  type: 'folder'
}

function uriToItem(
  docs: Array<ApiDocumentSnippet>,
): Map<string, FileItem | FolderItem> {
  const folderMap = new Map<string, FileItem | FolderItem>()

  // Add the root folder to the map.
  folderMap.set('/', {
    uri: '/',
    name: 'root',
    type: 'folder',
    childrenPaths: [],
  })

  for (const doc of docs) {
    const docUri = doc.uri

    // extract all folders uris from the file URI
    // e.g. /folder1/folder2/file.txt -> ['/', '/folder1', '/folder1/folder2']
    const fileParts = doc.uri.split('/')
    let currentNodePath = ''
    for (const part of fileParts) {
      const parentFolderPath = currentNodePath || '/'
      currentNodePath = `${currentNodePath}/${part}`
      // add the current folder to the map if it doesn't exist
      if (!folderMap.has(currentNodePath)) {
        if (currentNodePath === `/${docUri}`) {
          folderMap.set(currentNodePath, {
            uri: docUri,
            name: part,
            type: 'file',
            doc: doc,
            childrenPaths: [], // Files do not have children
          })
        } else {
          folderMap.set(currentNodePath, {
            uri: currentNodePath,
            name: part,
            type: 'folder',
            childrenPaths: [],
          })
        }
        // associate the folder with its parent, we know it exists
        ;(folderMap.get(parentFolderPath) as FolderItem).childrenPaths.push(
          currentNodePath,
        )
      }
    }
  }

  return folderMap
}

type FileTreeProps = {
  docs: Array<ApiDocumentSnippet>
}

export const FileTree = (props: FileTreeProps) => {
  const navigate = useNavigate()
  const docs: Array<ApiDocumentSnippet> = props.docs

  const itemsMap = uriToItem(docs)

  const tree = useTree<FileItem | FolderItem>({
    rootItemId: '/',
    getItemName: (item) => item.getItemData().name,
    isItemFolder: (item) => item.getItemData().type === 'folder',
    dataLoader: {
      getItem: (itemId) => itemsMap.get(itemId)!,
      getChildren: (itemId) => itemsMap.get(itemId)!.childrenPaths,
    },
    features: [syncDataLoaderFeature, selectionFeature, hotkeysCoreFeature],
    onPrimaryAction(item) {
      if (!item.isFolder()) {
        const doc = (item.getItemData() as FileItem).doc
        if (doc.last_indexing !== null) {
          navigate({
            to: '/doc/$docUri',
            params: { docUri: encodeURIComponent(doc.uri) },
          })
        }
      }
    },
  })

  return (
    <div {...tree.getContainerProps()} className="tree">
      {tree.getItems().map((item) => (
        <HoverCard key={item.getId()} openDelay={200} closeDelay={0}>
          <HoverCardTrigger asChild>
            <button
              {...item.getProps()}
              style={{
                paddingLeft: `${item.getItemMeta().level * 20}px`,
                width: '100%',
                textAlign: 'left',
              }}
            >
              <div
                className={cn('treeitem', {
                  focused: item.isFocused(),
                  expanded: item.isExpanded(),
                  selected: item.isSelected(),
                  folder: item.isFolder(),
                })}
                style={{ display: 'flex', alignItems: 'center' }}
              >
                {/* Show icon only for files, and select icon by doc.status */}
                {!item.isFolder() &&
                  (() => {
                    const doc = (item.getItemData() as FileItem).doc
                    if (doc.status === 'indexing_success') {
                      return <Check color="green" style={{ marginRight: 8 }} />
                    } else if (
                      doc.status === 'indexing' ||
                      doc.status === 'pending'
                    ) {
                      return (
                        <LoaderCircle
                          color="orange"
                          style={{ marginRight: 8 }}
                        />
                      )
                    } else {
                      return <CircleX color="red" style={{ marginRight: 8 }} />
                    }
                  })()}
                {item.getItemName()}
              </div>
            </button>
          </HoverCardTrigger>
          <HoverCardContent
            style={{
              whiteSpace: 'nowrap',
              overflow: 'visible',
              paddingTop: 4,
              paddingBottom: 4,
              width: 'auto',
              minWidth: 'unset',
              maxWidth: 'none',
            }}
          >
            <span style={{ fontFamily: 'monospace' }}>
              {item.getItemData().uri}
            </span>
          </HoverCardContent>
        </HoverCard>
      ))}
    </div>
  )
}
