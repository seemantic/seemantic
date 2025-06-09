import '@/components/biz/FileTree.css' // Assuming you have a CSS file for styles
import type { ApiDocumentSnippet } from '@/utils/api_data'
import {
  hotkeysCoreFeature,
  selectionFeature,
  syncDataLoaderFeature,
} from '@headless-tree/core'
import { useTree } from '@headless-tree/react'
import cn from 'classnames'

type TreeItem = {
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
            name: part,
            type: 'file',
            doc: doc,
            childrenPaths: [], // Files do not have children
          })
        } else {
          folderMap.set(currentNodePath, {
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
  })

  return (
    <div {...tree.getContainerProps()} className="tree">
      {tree.getItems().map((item) => (
        <button
          {...item.getProps()}
          key={item.getId()}
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
          >
            {item.getItemName()}
          </div>
        </button>
      ))}
    </div>
  )
}
