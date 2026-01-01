import { useState, useEffect } from 'react';

/**
 * renders the sidebar with chat history and user settings.
 */
export default function Sidebar({ collapsed, user, sessions, currentSessionId, onSelectSession, onNewChat, onRenameSession, onDeleteSession, onUpdateUser, onDeleteUser }) {
    const [menuOpenId, setMenuOpenId] = useState(null);
    const [settingsOpen, setSettingsOpen] = useState(false);

    // close menu when clicking outside
    useEffect(() => {
      const handleClickOutside = () => { setMenuOpenId(null); setSettingsOpen(false); };
      window.addEventListener('click', handleClickOutside);
      return () => window.removeEventListener('click', handleClickOutside);
    }, []);

    const handleRenameClick = (e, id, currentTitle) => {
      e.stopPropagation();
      setMenuOpenId(null);
      onRenameSession(id, currentTitle); // opens modal
    };

    return (
      <div className="sidebar">
        <div className="sidebar-header">
          <button onClick={onNewChat} className="new-chat-btn full-width" title="New Chat">
            {collapsed ? '+' : '+ New Chat'}
          </button>
          
          <div style={{position: 'relative', width: '100%'}}>
            <button 
                className="settings-btn" 
                onClick={(e) => { e.stopPropagation(); setSettingsOpen(!settingsOpen); }}
                style={collapsed ? { justifyContent: 'center', padding: 0 } : {}}
                title="Settings"
            >
                ⚙ {collapsed ? '' : 'Settings'}
            </button>
            {settingsOpen && (
                <div 
                  className="settings-menu" 
                  onClick={e => e.stopPropagation()}
                  style={collapsed ? { left: '50px', top: '0' } : {}}
                >
                    
                    {/* theme option */}
                    <div className="settings-item">
                        <span>Theme</span>
                        <span className="settings-arrow">▶</span>
                        <div className="submenu">
                            {['dark', 'light', 'forest', 'midnight'].map(t => (
                                <div 
                                    key={t}
                                    className={`submenu-item ${user.theme === t ? 'active' : ''}`}
                                    onClick={() => onUpdateUser({ theme: t })}
                                >
                                    {t.charAt(0).toUpperCase() + t.slice(1)}
                                    {user.theme === t && <span>✓</span>}
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* risk level option */}
                    <div className="settings-item">
                        <span>Risk Level</span>
                        <span className="settings-arrow">▶</span>
                        <div className="submenu">
                            {['Low', 'Medium', 'High'].map(r => (
                                <div 
                                    key={r}
                                    className={`submenu-item ${user.risk_level === r ? 'active' : ''}`}
                                    onClick={() => onUpdateUser({ risk_level: r })}
                                >
                                    {r}
                                    {user.risk_level === r && <span>✓</span>}
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* delete user */}
                    <div className="settings-item" onClick={onDeleteUser} style={{color: '#d32f2f'}}>
                        Delete User
                    </div>
                </div>
            )}
          </div>
        </div>

        {!collapsed && (
          <div className="recent-chats-separator">
              <div className="separator-line"></div>
              <span className="recent-chats-label">Recent Chats</span>
          </div>
        )}

        {!collapsed && <div className="session-list">
          {sessions.map(s => {
            // safety: get the id regardless of how mongo/pydantic sent it
            const realId = s.id || s._id;
            
            if (!realId) return null; // skip invalid items
            
            return (
              <div 
                key={realId} 
                className={`session-item ${realId === currentSessionId ? 'active' : ''}`}
              >
                <span 
                  className="session-title" 
                  onClick={() => onSelectSession(realId)}
                >
                  {s.title}
                </span>
                
                <button 
                  className="session-options-btn"
                  onClick={(e) => {
                    e.stopPropagation();
                    setMenuOpenId(menuOpenId === realId ? null : realId);
                  }}
                >
                  ⋮
                </button>

                {menuOpenId === realId && (
                  <div className="session-popup-menu">
                    <div className="session-popup-item" onClick={(e) => handleRenameClick(e, realId, s.title)}>Rename</div>
                    <div className="session-popup-item" onClick={(e) => {
                      e.stopPropagation();
                      onDeleteSession(realId);
                    }}>Delete</div>
                  </div>
                )}
              </div>
            );
          })}
        </div>}
      </div>
    );
  }