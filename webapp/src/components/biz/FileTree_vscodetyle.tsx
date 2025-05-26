import React, { useMemo } from 'react';
import {
  Tree,
  TreeController,
  TreeItem,
  TreeItemIndex,
  TreeItemRenderContext,
  TreeSource,
} from 'headless-tree';
import { produce } from 'immer'; // Optional: for easier state updates if needed

// Your type definitions
type File = {
  type: string; // e.g., 'file'
  name: string;
};

type Folder = {
  type: string; // e.g., 'folder'
  name: string;
  items: Array<Node>;
};

type Node = Folder | File;

type FileTreeProps = {
  nodes: Array<Node>;
};

// Helper function to transform your data into the format headless-tree expects
// and assign unique IDs.
const transformNodeToTreeItem = (node: Node, parentId?: string, index?: number): TreeItem<Node> => {
  const id = parentId ? `${parentId}-${node.name}` : node.name; // Simple ID generation, ensure uniqueness
  if ('items' in node) { // It's a Folder
    return {
      id,
      data: node,
      children: node.items.map((child, idx) => transformNodeToTreeItem(child, id, idx)),
    };
  } else { // It's a File
    return {
      id,
      data: node,
      children: [],
    };
  }
};

const FileSystemItem: React.FC<{
  item: TreeItem<Node>;
  context: TreeItemRenderContext<Node>;
  arrow: React.ReactNode;
}> = ({ item, context, arrow }) => {
  const isFolder = 'items' in item.data;
  const indent = context.depth * 20; // 20px indent per level

  return (
    <div
      {...context.itemContainerWithKeyboardNavigationProps}
      style={{
        paddingLeft: `${indent}px`,
        cursor: 'pointer',
        display: 'flex',
        alignItems: 'center',
      }}
    >
      {isFolder && (
        <span {...context.collapseInteractionProps} style={{ marginRight: '5px' }}>
          {arrow}
        </span>
      )}
      {!isFolder && <span style={{ marginRight: '5px', marginLeft: '15px' /* space for arrow on folders */ }}>📄</span>}
      <span>{item.data.name}</span>
    </div>
  );
};

const FileTree: React.FC<FileTreeProps> = ({ nodes }) => {
  const treeController = useMemo(() => new TreeController<Node>(), []);

  const treeSource: TreeSource<Node> = useMemo(() => {
    const items: Record<TreeItemIndex, TreeItem<Node>> = {};
    const rootItemIds: TreeItemIndex[] = [];

    const processNodes = (currentNodes: Array<Node>, parentId?: string) => {
      currentNodes.forEach((node, index) => {
        const treeItem = transformNodeToTreeItem(node, parentId, index);
        items[treeItem.id] = treeItem;
        if (!parentId) {
          rootItemIds.push(treeItem.id);
        }
        if ('items' in node && node.items.length > 0) {
          treeItem.children.forEach(childId => { // headless-tree expects children to be IDs
            const childNode = node.items.find(n => (parentId ? `${parentId}-${n.name}` : n.name) === childId);
            if (childNode) {
                 // The transformNodeToTreeItem already creates the full child objects,
                 // but headless-tree's basic `items` and `rootItemIds` structure
                 // relies on IDs for children. The `TreeItem` structure itself
                 // can hold the full child objects for easier rendering.
                 // Here we are just ensuring the items object is populated correctly.
                 const fullChildItem = transformNodeToTreeItem(childNode, treeItem.id);
                 items[fullChildItem.id] = fullChildItem;
                 // If `treeItem.children` was meant to be just IDs:
                 // if (!items[childId as string]) {
                 //   const childNode = node.items.find(n => (parentId ? `${parentId}-${n.name}` : n.name) === childId);
                 //   if (childNode) items[childId as string] = transformNodeToTreeItem(childNode, treeItem.id);
                 // }
            }
          });
           // Ensure children in TreeItem are just IDs if that's what the source expects
           // For this example, we are using the full nested structure from transformNodeToTreeItem.
           // If headless-tree requires children to be just IDs in the source,
           // the transform function and this part would need adjustment.
           // However, the documentation implies that `TreeItem` can have nested children.
        }
      });
    };

    processNodes(nodes);
    return { items, rootItemIds };
  }, [nodes]);


  // This is a more robust way to build the items and rootItemIds
  // according to the headless-tree documentation examples.
  const { items, rootItemIds } = useMemo(() => {
    const flatItems: Record<TreeItemIndex, TreeItem<Node>> = {};
    const topLevelIds: TreeItemIndex[] = [];

    function processNode(node: Node, parentId?: string): TreeItem<Node> {
      // Ensure unique ID: prefix with parentId if available, otherwise use name.
      // For root nodes, a simple name might suffice if globally unique.
      // Consider a more robust unique ID generation strategy for complex trees.
      const id = parentId ? `${parentId}/${node.name}` : node.name;

      if (flatItems[id]) {
        // This attempts to handle non-unique names by appending a suffix.
        // A better approach would be to have inherently unique IDs in your source data
        // or generate them based on path.
        let suffix = 1;
        while(flatItems[`${id}-${suffix}`]) {
          suffix++;
        }
        // @ts-ignore // Re-assigning id for uniqueness
        id = `${id}-${suffix}`;
      }


      if ('items' in node) { // Folder
        const childrenIds = node.items.map(child => processNode(child, id).id);
        const treeItem: TreeItem<Node> = {
          id,
          data: { ...node, type: 'folder' }, // Ensure type is set
          children: childrenIds,
        };
        flatItems[id] = treeItem;
        if (!parentId) topLevelIds.push(id);
        return treeItem;
      } else { // File
        const treeItem: TreeItem<Node> = {
          id,
          data: { ...node, type: 'file' }, // Ensure type is set
          children: [],
        };
        flatItems[id] = treeItem;
        if (!parentId) topLevelIds.push(id);
        return treeItem;
      }
    }

    nodes.forEach(node => processNode(node));
    return { items: flatItems, rootItemIds: topLevelIds };
  }, [nodes]);


  return (
    <Tree<Node>
      treeController={treeController}
      rootItemIds={rootItemIds}
      items={items}
      renderItem={({ item, context, children }) => {
        const isFolder = 'items' in item.data;
        const arrow = isFolder ? (context.isExpanded ? '▼' : '►') : null;

        return (
          <>
            <FileSystemItem item={item} context={context} arrow={arrow} />
            {context.isExpanded && children}
          </>
        );
      }}
      // Optional: if you want to control the expanded state or other features
      // onStateChange={(newState, oldState) => {
      //   console.log('Tree state changed:', newState);
      // }}
    />
  );
};

export default FileTree;

// Example Usage (in another component):
//
// import FileTree from './FileTree'; // Adjust path as needed
//
// const sampleNodes: Array<Node> = [
//   {
//     name: 'src',
//     type: 'folder',
//     items: [
//       { name: 'index.ts', type: 'file' },
//       {
//         name: 'components',
//         type: 'folder',
//         items: [
//           { name: 'Button.tsx', type: 'file' },
//           { name: 'Modal.tsx', type: 'file' },
//         ],
//       },
//       { name: 'App.tsx', type: 'file' },
//     ],
//   },
//   {
//     name: 'public',
//     type: 'folder',
//     items: [
//       { name: 'index.html', type: 'file' },
//       { name: 'favicon.ico', type: 'file' },
//     ],
//   },
//   { name: 'package.json', type: 'file' },
// ];
//
// const App = () => {
//   return (
//     <div>
//       <h1>File Explorer</h1>
//       <FileTree nodes={sampleNodes} />
//     </div>
//   );
// };
//
// export default App;