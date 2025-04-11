/* eslint-disable */

// @ts-nocheck

// noinspection JSUnusedGlobalSymbols

// This file was automatically generated by TanStack Router.
// You should NOT make any changes in this file as it will be overwritten.
// Additionally, you should also exclude this file from your linter and/or formatter to prevent it from being checked or modified.

// Import Routes

import { Route as rootRoute } from './routes/__root'
import { Route as AppRouteImport } from './routes/_app/route'
import { Route as DashboardIndexImport } from './routes/dashboard/index'
import { Route as AppIndexImport } from './routes/_app/index'
import { Route as AppSearchImport } from './routes/_app/search'

// Create/Update Routes

const AppRouteRoute = AppRouteImport.update({
  id: '/_app',
  getParentRoute: () => rootRoute,
} as any)

const DashboardIndexRoute = DashboardIndexImport.update({
  id: '/dashboard/',
  path: '/dashboard/',
  getParentRoute: () => rootRoute,
} as any)

const AppIndexRoute = AppIndexImport.update({
  id: '/',
  path: '/',
  getParentRoute: () => AppRouteRoute,
} as any)

const AppSearchRoute = AppSearchImport.update({
  id: '/search',
  path: '/search',
  getParentRoute: () => AppRouteRoute,
} as any)

// Populate the FileRoutesByPath interface

declare module '@tanstack/react-router' {
  interface FileRoutesByPath {
    '/_app': {
      id: '/_app'
      path: ''
      fullPath: ''
      preLoaderRoute: typeof AppRouteImport
      parentRoute: typeof rootRoute
    }
    '/_app/search': {
      id: '/_app/search'
      path: '/search'
      fullPath: '/search'
      preLoaderRoute: typeof AppSearchImport
      parentRoute: typeof AppRouteImport
    }
    '/_app/': {
      id: '/_app/'
      path: '/'
      fullPath: '/'
      preLoaderRoute: typeof AppIndexImport
      parentRoute: typeof AppRouteImport
    }
    '/dashboard/': {
      id: '/dashboard/'
      path: '/dashboard'
      fullPath: '/dashboard'
      preLoaderRoute: typeof DashboardIndexImport
      parentRoute: typeof rootRoute
    }
  }
}

// Create and export the route tree

interface AppRouteRouteChildren {
  AppSearchRoute: typeof AppSearchRoute
  AppIndexRoute: typeof AppIndexRoute
}

const AppRouteRouteChildren: AppRouteRouteChildren = {
  AppSearchRoute: AppSearchRoute,
  AppIndexRoute: AppIndexRoute,
}

const AppRouteRouteWithChildren = AppRouteRoute._addFileChildren(
  AppRouteRouteChildren,
)

export interface FileRoutesByFullPath {
  '': typeof AppRouteRouteWithChildren
  '/search': typeof AppSearchRoute
  '/': typeof AppIndexRoute
  '/dashboard': typeof DashboardIndexRoute
}

export interface FileRoutesByTo {
  '/search': typeof AppSearchRoute
  '/': typeof AppIndexRoute
  '/dashboard': typeof DashboardIndexRoute
}

export interface FileRoutesById {
  __root__: typeof rootRoute
  '/_app': typeof AppRouteRouteWithChildren
  '/_app/search': typeof AppSearchRoute
  '/_app/': typeof AppIndexRoute
  '/dashboard/': typeof DashboardIndexRoute
}

export interface FileRouteTypes {
  fileRoutesByFullPath: FileRoutesByFullPath
  fullPaths: '' | '/search' | '/' | '/dashboard'
  fileRoutesByTo: FileRoutesByTo
  to: '/search' | '/' | '/dashboard'
  id: '__root__' | '/_app' | '/_app/search' | '/_app/' | '/dashboard/'
  fileRoutesById: FileRoutesById
}

export interface RootRouteChildren {
  AppRouteRoute: typeof AppRouteRouteWithChildren
  DashboardIndexRoute: typeof DashboardIndexRoute
}

const rootRouteChildren: RootRouteChildren = {
  AppRouteRoute: AppRouteRouteWithChildren,
  DashboardIndexRoute: DashboardIndexRoute,
}

export const routeTree = rootRoute
  ._addFileChildren(rootRouteChildren)
  ._addFileTypes<FileRouteTypes>()

/* ROUTE_MANIFEST_START
{
  "routes": {
    "__root__": {
      "filePath": "__root.tsx",
      "children": [
        "/_app",
        "/dashboard/"
      ]
    },
    "/_app": {
      "filePath": "_app/route.tsx",
      "children": [
        "/_app/search",
        "/_app/"
      ]
    },
    "/_app/search": {
      "filePath": "_app/search.tsx",
      "parent": "/_app"
    },
    "/_app/": {
      "filePath": "_app/index.tsx",
      "parent": "/_app"
    },
    "/dashboard/": {
      "filePath": "dashboard/index.tsx"
    }
  }
}
ROUTE_MANIFEST_END */
