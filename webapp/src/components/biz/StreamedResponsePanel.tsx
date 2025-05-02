import { subscribeToQuery } from '@/utils/api'
import type { ApiQuery, ApiQueryResponseUpdate } from '@/utils/api_data'
import React from 'react'

interface StreamedResponsePanelProps {
  query: ApiQuery
}

const StreamedResponsePanel: React.FC<StreamedResponsePanelProps> = ({
  query,
}) => {
  const [answer, setAnswer] = React.useState<string>('')

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
      <div className="content">{answer}</div>
    </div>
  )
}

export default StreamedResponsePanel
