import type { QueryResponseUpdate } from '@/utils/api'
import { apiUrl } from '@/utils/api'
import { createEventSource } from 'eventsource-client'
import React from 'react'

interface StreamedResponsePanelProps {
  query: string
}

const StreamedResponsePanel: React.FC<StreamedResponsePanelProps> = ({
  query,
}) => {
  const [answer, setAnswer] = React.useState<string>('')

  const connect = async () => {
    const es = createEventSource({
      url: `${apiUrl}/queries`,
      method: 'POST',
      body: JSON.stringify({ query }),
      headers: {
        'Content-Type': 'application/json',
      },
    })

    for await (const { data } of es) {
      const queryResponseUpdate: QueryResponseUpdate = 
      JSON.parse(data)
      if (queryResponseUpdate.delta_answer) {
        setAnswer((prev: string) => prev + queryResponseUpdate.delta_answer)
      }
    }
    es.close()
  }

  React.useEffect(() => {
    connect()
    return () => {}
  }, [query])

  return (
    <div className="streamed-response-panel">
      <h2>{answer}</h2>
      <div className="content">{answer}</div>
    </div>
  )
}

export default StreamedResponsePanel
