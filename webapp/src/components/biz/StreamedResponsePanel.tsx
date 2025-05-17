import { Card, CardContent } from '@/shadcn/components/ui/card'
import { subscribeToQuery } from '@/utils/api'
import type {
  ApiChatMessage,
  ApiQuery,
  ApiQueryResponseMessage,
  ApiQueryResponseUpdate,
  ApiSearchResult,
} from '@/utils/api_data'
import { Link } from '@tanstack/react-router'
import React from 'react'

interface StreamedResponsePanelProps {
  query: ApiQuery
  onResponseCompleted: (response: ApiQueryResponseMessage) => void
}

const StreamedResponsePanel: React.FC<StreamedResponsePanelProps> = ({
  query,
  onResponseCompleted,
}) => {
  const [answer, setAnswer] = React.useState<string>('')
  const [refs, setRefs] = React.useState<Array<ApiSearchResult>>([])
  const [chatMessagesExchanged, setChatMessagesExchanged] = React.useState<
    Array<ApiChatMessage>
  >([])

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
          if (
            queryResponseUpdate.chat_messages_exchanged &&
            queryResponseUpdate.chat_messages_exchanged.length > 0
          ) {
            setChatMessagesExchanged(
              () =>
                queryResponseUpdate.chat_messages_exchanged as Array<ApiChatMessage>,
            )
          }
        },
        () => {
          onResponseCompleted({
            answer: answer,
            search_result: refs,
            chat_messages_exchanged: chatMessagesExchanged,
          })
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
