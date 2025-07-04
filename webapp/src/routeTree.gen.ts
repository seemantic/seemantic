/* eslint-disable */

// @ts-nocheck

// noinspection JSUnusedGlobalSymbols

// This file was automatically generated by TanStack Router.
// You should NOT make any changes in this file as it will be overwritten.
// Additionally, you should also exclude this file from your linter and/or formatter to prevent it from being checked or modified.

import { Route as rootRouteImport } from './routes/__root'
import { Route as AppRouteRouteImport } from './routes/_app/route'
import { Route as DashboardIndexRouteImport } from './routes/dashboard/index'
import { Route as AppIndexRouteImport } from './routes/_app/index'
import { Route as AppDocDocUriRouteImport } from './routes/_app/doc.$docUri'
import { Route as AppConvConvIdRouteImport } from './routes/_app/conv.$convId'

const AppRouteRoute = AppRouteRouteImport.update({
  id: '/_app',
  getParentRoute: () => rootRouteImport,
} as any)
const DashboardIndexRoute = DashboardIndexRouteImport.update({
  id: '/dashboard/',
  path: '/dashboard/',
  getParentRoute: () => rootRouteImport,
} as any)
const AppIndexRoute = AppIndexRouteImport.update({
  id: '/',
  path: '/',
  getParentRoute: () => AppRouteRoute,
} as any)
const AppDocDocUriRoute = AppDocDocUriRouteImport.update({
  id: '/doc/$docUri',
  path: '/doc/$docUri',
  getParentRoute: () => AppRouteRoute,
} as any)
const AppConvConvIdRoute = AppConvConvIdRouteImport.update({
  id: '/conv/$convId',
  path: '/conv/$convId',
  getParentRoute: () => AppRouteRoute,
} as any)

export interface FileRoutesByFullPath {
  '/': typeof AppIndexRoute
  '/dashboard': typeof DashboardIndexRoute
  '/conv/$convId': typeof AppConvConvIdRoute
  '/doc/$docUri': typeof AppDocDocUriRoute
}
export interface FileRoutesByTo {
  '/': typeof AppIndexRoute
  '/dashboard': typeof DashboardIndexRoute
  '/conv/$convId': typeof AppConvConvIdRoute
  '/doc/$docUri': typeof AppDocDocUriRoute
}
export interface FileRoutesById {
  __root__: typeof rootRouteImport
  '/_app': typeof AppRouteRouteWithChildren
  '/_app/': typeof AppIndexRoute
  '/dashboard/': typeof DashboardIndexRoute
  '/_app/conv/$convId': typeof AppConvConvIdRoute
  '/_app/doc/$docUri': typeof AppDocDocUriRoute
}
export interface FileRouteTypes {
  fileRoutesByFullPath: FileRoutesByFullPath
  fullPaths: '/' | '/dashboard' | '/conv/$convId' | '/doc/$docUri'
  fileRoutesByTo: FileRoutesByTo
  to: '/' | '/dashboard' | '/conv/$convId' | '/doc/$docUri'
  id:
    | '__root__'
    | '/_app'
    | '/_app/'
    | '/dashboard/'
    | '/_app/conv/$convId'
    | '/_app/doc/$docUri'
  fileRoutesById: FileRoutesById
}
export interface RootRouteChildren {
  AppRouteRoute: typeof AppRouteRouteWithChildren
  DashboardIndexRoute: typeof DashboardIndexRoute
}

declare module '@tanstack/react-router' {
  interface FileRoutesByPath {
    '/_app': {
      id: '/_app'
      path: ''
      fullPath: ''
      preLoaderRoute: typeof AppRouteRouteImport
      parentRoute: typeof rootRouteImport
    }
    '/dashboard/': {
      id: '/dashboard/'
      path: '/dashboard'
      fullPath: '/dashboard'
      preLoaderRoute: typeof DashboardIndexRouteImport
      parentRoute: typeof rootRouteImport
    }
    '/_app/': {
      id: '/_app/'
      path: '/'
      fullPath: '/'
      preLoaderRoute: typeof AppIndexRouteImport
      parentRoute: typeof AppRouteRoute
    }
    '/_app/doc/$docUri': {
      id: '/_app/doc/$docUri'
      path: '/doc/$docUri'
      fullPath: '/doc/$docUri'
      preLoaderRoute: typeof AppDocDocUriRouteImport
      parentRoute: typeof AppRouteRoute
    }
    '/_app/conv/$convId': {
      id: '/_app/conv/$convId'
      path: '/conv/$convId'
      fullPath: '/conv/$convId'
      preLoaderRoute: typeof AppConvConvIdRouteImport
      parentRoute: typeof AppRouteRoute
    }
  }
}

interface AppRouteRouteChildren {
  AppIndexRoute: typeof AppIndexRoute
  AppConvConvIdRoute: typeof AppConvConvIdRoute
  AppDocDocUriRoute: typeof AppDocDocUriRoute
}

const AppRouteRouteChildren: AppRouteRouteChildren = {
  AppIndexRoute: AppIndexRoute,
  AppConvConvIdRoute: AppConvConvIdRoute,
  AppDocDocUriRoute: AppDocDocUriRoute,
}

const AppRouteRouteWithChildren = AppRouteRoute._addFileChildren(
  AppRouteRouteChildren,
)

const rootRouteChildren: RootRouteChildren = {
  AppRouteRoute: AppRouteRouteWithChildren,
  DashboardIndexRoute: DashboardIndexRoute,
}
export const routeTree = rootRouteImport
  ._addFileChildren(rootRouteChildren)
  ._addFileTypes<FileRouteTypes>()
