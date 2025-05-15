import DocPanel from '@/components/biz/DocPanel'
import { getParsedDocument } from '@/utils/api'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/_app/doc/$docUri')({
  component: RouteComponent,
  loader: async ({ params }) => {
    const { docUri } = params
    const doc = await getParsedDocument(docUri)
    return doc
  },
})

function RouteComponent() {
  const doc = Route.useLoaderData()

  return <DocPanel doc={doc} />
}
