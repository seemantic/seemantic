import { Card, CardContent } from '@/shadcn/components/ui/card'
import { userConvStore } from '@/utils/conv_manager'
import { Link } from '@tanstack/react-router'
import React from 'react'

interface StreamedResponsePanelProps {
  convId: string
  queryResponsePairId: string
}

const StreamedResponsePanel: React.FC<StreamedResponsePanelProps> = ({
  convId,
  queryResponsePairId,
}) => {
  const pair = userConvStore(
    (state) =>
      state.conversations[convId].queryResponsePairs[queryResponsePairId],
  )

  const refs = pair.response.search_results
  const answer = pair.response.answer

  return (
    <div className="streamed-response-panel">
      {refs.map((ref) => (
        <Link
          to="."
          search={{ docUri: ref.document_uri }}
          key={ref.document_uri}
        >
          <Card key={ref.document_uri} className="mb-2">
            <CardContent>
              <p>{ref.document_uri}</p>
            </CardContent>
          </Card>
        </Link>
      ))}
      <div className="content">{answer}</div>
    </div>
  )
}

export default StreamedResponsePanel
