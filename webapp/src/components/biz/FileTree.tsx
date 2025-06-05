import type { ApiDocumentSnippet } from '@/utils/api_data'
import {
  hotkeysCoreFeature,
  selectionFeature,
  syncDataLoaderFeature,
} from '@headless-tree/core'
import { useTree } from '@headless-tree/react'
import cn from 'classnames'

type TreeItem = {
  uri: string
  name: string
  type: 'file' | 'folder'
  childrenUris: Array<string>
}

type FileItem = TreeItem & {
  type: 'file'
  doc: ApiDocumentSnippet
  childrenUris: [] // alaways empty for files
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
    childrenUris: [],
  })

  for (const doc of docs) {
    const fileUri = doc.uri.startsWith('/') ? doc.uri : `/${doc.uri}`

    // Find the last separator to identify the parent folder.
    const lastSlashIndex = fileUri.lastIndexOf('/')

    // Determine the parent folder's URI.
    const folderUri =
      lastSlashIndex === 0 ? '/' : fileUri.substring(0, lastSlashIndex)

    // Create a new entry for the folder if it doesn't exist.
    if (!folderMap.has(folderUri)) {
      folderMap.set(folderUri, {
        uri: folderUri,
        name: folderUri.split('/').pop()!,
        type: 'folder',
        childrenUris: [],
      })
    }

    // Add the child to its parent's list, only if the parent is a folder.
    ;(folderMap.get(folderUri) as FolderItem).childrenUris.push(fileUri)

    // Ensure the file itself is also a key in the map.
    folderMap.set(fileUri, {
      uri: fileUri,
      name: fileUri.split('/').pop()!,
      type: 'file',
      doc: doc,
      childrenUris: [], // Files do not have children
    })
  }

  return folderMap
}

type FileTreeProps = {
  docs: Array<ApiDocumentSnippet>
}

export const FileTree = (props: FileTreeProps) => {
  const docs: Array<ApiDocumentSnippet> = props.docs

  const itemsMap = uriToItem(docs)

  const tree = useTree<FileItem | FolderItem>({
    rootItemId: '/',
    getItemName: (item) => item.getItemData().name,
    isItemFolder: (item) => item.getItemData().type === 'folder',
    dataLoader: {
      getItem: (itemId) => itemsMap.get(itemId)!,
      getChildren: (itemId) => itemsMap.get(itemId)!.childrenUris,
    },
    indent: 10,
    features: [syncDataLoaderFeature, selectionFeature, hotkeysCoreFeature],
  })

  return (
    <div {...tree.getContainerProps()} className="tree">
      {tree.getItems().map((item) => (
        <button
          {...item.getProps()}
          key={item.getId()}
          style={{
            paddingLeft: `${item.getItemMeta().level * 20}px`,
            display: 'block',
            width: '100%',
          }}
        >
          <div
            className={cn('treeitem', {
              focused: item.isFocused(),
              expanded: item.isExpanded(),
              selected: item.isSelected(),
              folder: item.isFolder(),
            })}
          >
            {item.getItemName()}
          </div>
        </button>
      ))}
    </div>
  )
}
