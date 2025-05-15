import type { ApiParsedDocument } from '@/utils/api_data'

type DocPanelProps = {
  doc: ApiParsedDocument
}

export default function DocPanel(props: DocPanelProps) {
  const { doc } = props
  return (
    <>
      <div>{doc.hash}</div>
      <div>{doc.markdown_content}</div>
    </>
  )
}
