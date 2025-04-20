import React from 'react'

interface StreamedResponsePanelProps {
  title: string
  content: string
}

const StreamedResponsePanel: React.FC<StreamedResponsePanelProps> = ({
  title,
  content,
}) => {
  return (
    <div className="streamed-response-panel">
      <h2>{title}</h2>
      <div className="content">{content}</div>
    </div>
  )
}

export default StreamedResponsePanel
