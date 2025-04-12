import { createFileRoute, getRouteApi } from '@tanstack/react-router'


type SearchParams = {
  q: string
}

export const Route = createFileRoute('/_app/search')({
  component: RouteComponent,
  validateSearch: (search: Record<string, unknown>): SearchParams => {
    return { q: search.q as string || '' }
  },
})

const routeApi = getRouteApi('/_app/search')

function RouteComponent() {
  const searchParams = routeApi.useSearch()
  const { q } = searchParams




  
  return <div>{q}</div>
}
