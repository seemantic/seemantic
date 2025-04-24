import type { QueryResponseUpdate } from '@/utils/api'
import { apiUrl } from '@/utils/api'
import { fetchEventSource } from '@microsoft/fetch-event-source'
import React from 'react'

interface StreamedResponsePanelProps {
  query: string
}

const StreamedResponsePanel: React.FC<StreamedResponsePanelProps> = ({
  query,
}) => {
  const [answer, setAnswer] = React.useState<string>('')

  React.useEffect(() => {
    const abortController = new AbortController()

    const connect = async () => {
      await fetchEventSource(`${apiUrl}/queries`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json', // Use application/json for the request body
          Accept: 'text/event-stream', // Specify we accept SSE
        },
        body: JSON.stringify({ query }),
        signal: abortController.signal,
        onmessage: (event) => {
          const queryResponseUpdate: QueryResponseUpdate = JSON.parse(
            event.data,
          )
          if (queryResponseUpdate.delta_answer) {
            setAnswer((prev: string) => prev + queryResponseUpdate.delta_answer)
          }
        },
      })
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
