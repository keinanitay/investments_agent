import ReactMarkdown from 'react-markdown';
// placeholder for future chart rendering tools
import { useEffect, useRef } from 'react';

/**
 * renders the chat interface including message history and input area.
 */
export default function ChatArea({ messages, input, setInput, loading, onSend, onStop }) {
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [input]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!loading) onSend(e);
    }
  };

  return (
    <div className="chat-area">
      <div className="messages-box">
        {messages.length === 0 && (
          <div className="welcome-msg" style={{textAlign: 'center', marginTop: '20%', color: '#666'}}>
            How can I help you with your investments today?
          </div>
        )}
        
        {messages.map((msg, idx) => (
          <div key={idx} className={`message-row ${msg.role}`}>
            <div className="message-content-wrapper">
            <div className="message-bubble">
              {/* render text with markdown */}
                <ReactMarkdown>{msg.content}</ReactMarkdown>

                {/* check for graphs in metadata */}
                {msg.metadata?.type === 'chart' && (
                <div className="chart-container" style={{marginTop: '10px', height: '200px'}}>
                    {/* placeholder for future graph component - uses css class for theming */}
                    <div className="chart-placeholder">
                        Graph Data: {msg.metadata.chart_data.length} points
                    </div>
                </div>
                )}

                {/* check for sources/links */}
                {msg.metadata?.sources && (
                <div className="sources-list" style={{fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '5px'}}>
                    Sources: {msg.metadata.sources.map(s => s.name).join(', ')}
                </div>
                )}
            </div>

            {/* execution time - outside bubble */}
            {msg.metadata?.execution_time && (
              <div className="execution-time">
                {msg.metadata.execution_time.toFixed(2)}s
              </div>
            )}
            </div>
          </div>
        ))}
        
        {loading && (
          <div className="message-row assistant">
            <div className="message-bubble" style={{width: '150px'}}>
              <div className="skeleton" style={{width: '100%'}}></div>
              <div className="skeleton" style={{width: '70%'}}></div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <form className="input-area" onSubmit={(e) => { e.preventDefault(); if(!loading) onSend(e); }}>
        <textarea 
          ref={textareaRef}
          value={input} 
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about a stock..." 
          disabled={false} // keep enabled so user can type next query while waiting or stopping
          rows={1}
        />
        {loading ? (
          <button type="button" className="stop-btn" onClick={onStop}>Stop</button>
        ) : (
          <button type="submit">Send</button>
        )}
      </form>
    </div>
  );
}