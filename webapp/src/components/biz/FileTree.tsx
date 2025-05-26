import {
  hotkeysCoreFeature,
  selectionFeature,
  syncDataLoaderFeature,
} from '@headless-tree/core'
import { useTree } from '@headless-tree/react'
import cn from 'classnames'

type File = {
  type: string
  name: string
}

type Folder = {
  name: string
  items: Array<Node>
}

type Node = Folder | File

type FileTreeProps = {
  nodes: Array<Node>
}

export const FileTree = (props: FileTreeProps) => {
  const tree = useTree<string>({
    initialState: { expandedItems: ['folder-1'] },
    rootItemId: 'folder',
    getItemName: (item) => item.getItemData(),
    isItemFolder: (item) => !item.getItemData().endsWith('item'),
    dataLoader: {
      getItem: (itemId) => itemId,
      getChildren: (itemId) => [`${itemId}-1`, `${itemId}-2`, `${itemId}-3`],
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
