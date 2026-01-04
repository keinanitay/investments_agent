import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useEffect, useRef } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

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
    <div className="chat-area" style={{ minWidth: 0 }}>
      <div className="messages-box">
        {messages.length === 0 && (
          <div className="welcome-msg" style={{textAlign: 'center', marginTop: '20%', color: '#666'}}>
            How can I help you with your investments today?
          </div>
        )}
        
        {messages.map((msg, idx) => (
          <div key={idx} className={`message-row ${msg.role}`}>
            <div className="message-content-wrapper">
            <div className="message-bubble" style={{ overflowWrap: 'anywhere' }}>
              {/* render text with markdown */}
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    table: ({node, ...props}) => (
                      <div style={{ overflowX: 'auto', maxWidth: '100%', marginBottom: '10px' }}>
                        <table {...props} style={{ borderCollapse: 'collapse', width: '100%' }} />
                      </div>
                    ),
                    pre: ({node, ...props}) => (
                      <div style={{ overflowX: 'auto', maxWidth: '100%', borderRadius: '4px' }}>
                        <pre {...props} />
                      </div>
                    )
                  }}
                >
                  {msg.content}
                </ReactMarkdown>

                {/* check for graphs in metadata */}
                {msg.metadata?.type === 'chart' && (
                <div className="chart-container" style={{marginTop: '15px', height: '250px', width: '100%', minWidth: '300px', maxWidth: '500px'}}>
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={msg.metadata.chart_data}>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                        <XAxis dataKey="name" stroke="var(--text-muted)" tick={{fill: 'var(--text-muted)'}} />
                        <YAxis stroke="var(--text-muted)" tick={{fill: 'var(--text-muted)'}} />
                        <Tooltip 
                          contentStyle={{ backgroundColor: 'var(--bg-sidebar)', border: '1px solid var(--border-color)', borderRadius: '4px', color: 'var(--text-main)' }}
                          itemStyle={{ color: 'var(--text-main)' }}
                          cursor={{fill: 'var(--bg-sidebar-hover)'}}
                        />
                        <Bar dataKey="value" fill="var(--accent)" radius={[4, 4, 0, 0]} barSize={40} />
                      </BarChart>
                    </ResponsiveContainer>
                </div>
                )}

                {/* check for sources/links */}
                {msg.metadata?.sources && (
                <div className="sources-list" style={{fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '5px'}}>
                    Sources: {msg.metadata.sources.map(s => s.name).join(', ')}
                </div>
                )}
            </div>

            {/* Stopped Indicator */}
            {msg.stopped && (
              <div style={{ fontSize: '0.75rem', color: '#ff6b6b', marginTop: '4px', fontStyle: 'italic', textAlign: 'right' }}>
                Stopped by user
              </div>
            )}

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