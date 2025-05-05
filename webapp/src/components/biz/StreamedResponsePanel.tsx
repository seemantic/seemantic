import { Card, CardContent } from '@/shadcn/components/ui/card'
import { subscribeToQuery } from '@/utils/api'
import type {
  ApiQuery,
  ApiQueryResponseUpdate,
  ApiSearchResult,
} from '@/utils/api_data'
import React from 'react'

interface StreamedResponsePanelProps {
  query: ApiQuery
}

const StreamedResponsePanel: React.FC<StreamedResponsePanelProps> = ({
  query,
}) => {
  const [answer, setAnswer] = React.useState<string>('')
  const [refs, setRefs] = React.useState<Array<ApiSearchResult>>([])

  React.useEffect(() => {
    const abortController = new AbortController()

    const connect = async () => {
      await subscribeToQuery(
        query,
        abortController,
        (queryResponseUpdate: ApiQueryResponseUpdate) => {
          if (queryResponseUpdate.delta_answer) {
            setAnswer((prev: string) => prev + queryResponseUpdate.delta_answer)
          }
          if (
            queryResponseUpdate.search_result &&
            queryResponseUpdate.search_result.length > 0
          ) {
            setRefs(
              () => queryResponseUpdate.search_result as Array<ApiSearchResult>,
            )
          }
        },
      )
    }

    connect()

    // Cleanup function to abort the connection when the component unmounts or query changes
    return () => {
      abortController.abort()
    }
  }, [query])

  return (
    <div className="streamed-response-panel">
      {refs.map((ref) => (
        <Card key={ref.document_uri} className="mb-2">
          <CardContent>
            <p>{ref.document_uri}</p>
          </CardContent>
        </Card>
      ))}
      <div className="content">{answer}</div>
    </div>
  )
}

export default StreamedResponsePanel
