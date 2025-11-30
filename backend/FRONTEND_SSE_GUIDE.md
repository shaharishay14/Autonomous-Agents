# Frontend SSE Integration Guide

## Important: The Frontend MUST Change

**The frontend cannot remain the same.** The endpoint now returns a **streaming response** instead of a single JSON response. Here's what needs to change:

## What Changed on Backend

### Before (Old Endpoint):
```
POST /api/agents/{id}/chat/
Response: Single JSON object
{
  "user_message": {...},
  "assistant_message": {...}
}
```

### After (New Endpoint):
```
POST /api/agents/{id}/chat/
Response: Server-Sent Events stream
Content-Type: text/event-stream

event: status
data: {"status": "thinking", "message": "Analyzing..."}

event: content_delta
data: {"content": "Hello, ", "index": 0}

event: content_delta
data: {"content": "how ", "index": 1}

event: message_complete
data: {"message_id": "...", "content": "..."}

event: done
data: {}
```

## Frontend Changes Required

### Option 1: Using Fetch API (Recommended)

The standard EventSource API doesn't support POST requests with body. Use fetch with ReadableStream instead:

```javascript
async function sendMessage(agentId, message, fileIds = []) {
  const response = await fetch(`/api/agents/${agentId}/chat/`, {
    method: 'POST',
    headers: {
      'Authorization': `Token ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message: message,
      file_ids: fileIds
    })
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  let buffer = '';
  let currentContent = '';

  while (true) {
    const { done, value } = await reader.read();

    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    // Split by double newline (SSE event separator)
    const lines = buffer.split('\n\n');
    buffer = lines.pop(); // Keep incomplete event in buffer

    for (const line of lines) {
      if (!line.trim()) continue;

      const event = parseSSEEvent(line);

      if (event.type === 'status') {
        // Update UI status indicator
        updateStatus(event.data.status, event.data.message);
      }
      else if (event.type === 'tool_call_start') {
        // Show tool execution started
        showToolExecution(event.data.tool, event.data.parameters);
      }
      else if (event.type === 'tool_call_result') {
        // Show tool execution result
        showToolResult(event.data.tool, event.data.success, event.data.result);
      }
      else if (event.type === 'content_delta') {
        // Append text to message display
        currentContent += event.data.content;
        updateMessageContent(currentContent);
      }
      else if (event.type === 'message_complete') {
        // Message saved to database
        const messageId = event.data.message_id;
        finalizeMessage(messageId, event.data.content);
      }
      else if (event.type === 'done') {
        // Stream finished
        console.log('Stream complete');
      }
      else if (event.type === 'error') {
        // Handle error
        showError(event.data.error);
      }
    }
  }
}

function parseSSEEvent(eventString) {
  const lines = eventString.split('\n');
  const event = { type: 'message', data: null };

  for (const line of lines) {
    if (line.startsWith('event:')) {
      event.type = line.slice(6).trim();
    } else if (line.startsWith('data:')) {
      const dataStr = line.slice(5).trim();
      try {
        event.data = JSON.parse(dataStr);
      } catch (e) {
        event.data = dataStr;
      }
    }
  }

  return event;
}
```

### Option 2: Using EventSource (Limited - Can't POST body)

If you want to use the standard EventSource API, you'd need to send the message via query params (not recommended for large messages):

```javascript
// NOT RECOMMENDED - Limited functionality
const eventSource = new EventSource(
  `/api/agents/${agentId}/chat/?message=${encodeURIComponent(message)}`,
  {
    headers: {
      'Authorization': `Token ${token}`
    }
  }
);

eventSource.addEventListener('status', (e) => {
  const data = JSON.parse(e.data);
  updateStatus(data.status, data.message);
});

eventSource.addEventListener('content_delta', (e) => {
  const data = JSON.parse(e.data);
  appendContent(data.content);
});

eventSource.addEventListener('done', () => {
  eventSource.close();
});
```

### Option 3: Using a Library (Easiest)

Use `@microsoft/fetch-event-source` for better POST support:

```bash
npm install @microsoft/fetch-event-source
```

```javascript
import { fetchEventSource } from '@microsoft/fetch-event-source';

await fetchEventSource(`/api/agents/${agentId}/chat/`, {
  method: 'POST',
  headers: {
    'Authorization': `Token ${token}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    message: message,
    file_ids: fileIds
  }),
  onopen(response) {
    if (response.ok) {
      console.log('Stream opened');
    } else {
      throw new Error(`Failed: ${response.status}`);
    }
  },
  onmessage(event) {
    const data = JSON.parse(event.data);

    switch (event.event) {
      case 'status':
        updateStatus(data.status, data.message);
        break;
      case 'tool_call_start':
        showToolExecution(data.tool, data.parameters);
        break;
      case 'tool_call_result':
        showToolResult(data.tool, data.success, data.result);
        break;
      case 'content_delta':
        appendContent(data.content);
        break;
      case 'message_complete':
        finalizeMessage(data.message_id, data.content);
        break;
      case 'done':
        console.log('Complete');
        break;
      case 'error':
        showError(data.error);
        break;
    }
  },
  onerror(err) {
    console.error('Stream error:', err);
    throw err; // Stop retrying
  }
});
```

## React Example (Complete Component)

```jsx
import React, { useState } from 'react';
import { fetchEventSource } from '@microsoft/fetch-event-source';

function ChatInterface({ agentId, token }) {
  const [messages, setMessages] = useState([]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [status, setStatus] = useState('');

  const sendMessage = async (text) => {
    if (!text.trim() || isStreaming) return;

    // Add user message to UI
    setMessages(prev => [...prev, { role: 'user', content: text }]);
    setCurrentMessage('');
    setIsStreaming(true);

    let assistantContent = '';

    try {
      await fetchEventSource(`/api/agents/${agentId}/chat/`, {
        method: 'POST',
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: text, file_ids: [] }),

        onmessage(event) {
          const data = JSON.parse(event.data);

          switch (event.event) {
            case 'status':
              setStatus(data.message);
              break;

            case 'content_delta':
              assistantContent += data.content;
              // Update last message in real-time
              setMessages(prev => {
                const newMessages = [...prev];
                if (newMessages[newMessages.length - 1]?.role === 'assistant') {
                  newMessages[newMessages.length - 1].content = assistantContent;
                } else {
                  newMessages.push({ role: 'assistant', content: assistantContent });
                }
                return newMessages;
              });
              break;

            case 'message_complete':
              // Final message saved
              setMessages(prev => {
                const newMessages = [...prev];
                if (newMessages[newMessages.length - 1]?.role === 'assistant') {
                  newMessages[newMessages.length - 1].id = data.message_id;
                }
                return newMessages;
              });
              break;

            case 'done':
              setIsStreaming(false);
              setStatus('');
              break;

            case 'error':
              console.error('Stream error:', data.error);
              setIsStreaming(false);
              break;
          }
        },

        onerror(err) {
          console.error('Stream error:', err);
          setIsStreaming(false);
          throw err;
        }
      });
    } catch (error) {
      console.error('Failed to send message:', error);
      setIsStreaming(false);
    }
  };

  return (
    <div className="chat-interface">
      <div className="messages">
        {messages.map((msg, idx) => (
          <div key={msg.id || idx} className={`message ${msg.role}`}>
            {msg.content}
          </div>
        ))}
      </div>

      {status && (
        <div className="status-indicator">
          {status}
        </div>
      )}

      <input
        value={currentMessage}
        onChange={(e) => setCurrentMessage(e.target.value)}
        onKeyPress={(e) => e.key === 'Enter' && sendMessage(currentMessage)}
        disabled={isStreaming}
        placeholder="Type a message..."
      />
    </div>
  );
}

export default ChatInterface;
```

## Event Types Reference

| Event Type | Description | Data Fields |
|------------|-------------|-------------|
| `status` | Agent status update | `status`, `message`, `timestamp` |
| `tool_call_start` | Tool execution started | `tool`, `parameters`, `timestamp` |
| `tool_call_result` | Tool execution completed | `tool`, `success`, `result`, `error`, `timestamp` |
| `content_delta` | Partial response text | `content`, `index`, `timestamp` |
| `message_complete` | Message saved to DB | `message_id`, `content`, `created_at` |
| `done` | Stream finished | `timestamp` |
| `error` | Error occurred | `error`, `details`, `timestamp` |
| `heartbeat` | Keep-alive signal | `message`, `timestamp` |

## Status Values

- `thinking` - Analyzing the request
- `tool_calling` - Loading/executing tools
- `processing` - Composio agent working
- `responding` - Generating final response
- `complete` - Finished

## Migration Strategy

If you want to support both old and new clients:

1. **Option A**: Keep old endpoint, add new endpoint at `/chat/stream/`
2. **Option B**: Replace endpoint, update frontend (breaking change)
3. **Option C**: Add version parameter `/api/v2/agents/.../chat/`

**Current implementation uses Option B** (replaced the endpoint). If you need backward compatibility, let me know and I can add a parallel endpoint.

## Testing the Endpoint

Use the provided test script:

```bash
# Start server
python manage.py runserver

# In another terminal, run test
python test_streaming_chat.py
```

You should see real-time streaming output with all event types.
