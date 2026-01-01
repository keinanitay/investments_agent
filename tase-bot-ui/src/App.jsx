import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './App.css';
import { Toaster, toast } from 'react-hot-toast';
import LoginScreen from './components/LoginScreen';
import Sidebar from './components/Sidebar';
import ChatArea from './components/ChatArea';
import Modal from './components/Modal';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api',
});

function App() {
  // load user from storage
  const [token, setToken] = useState(() => {
    return localStorage.getItem('tase_token') || null;
  });

  const [user, setUser] = useState(() => {
    const savedUser = localStorage.getItem('tase_user');
    const savedToken = localStorage.getItem('tase_token');
    // only load user if token also exists
    return (savedUser && savedToken) ? JSON.parse(savedUser) : null;
  });

  const [sessions, setSessions] = useState([]); 
  
  // load active session id from storage
  const [currentSessionId, setCurrentSessionId] = useState(() => {
    return localStorage.getItem('tase_current_session_id') || null;
  });

  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(() => {
    return window.innerWidth > 768;
  });
  const userMenuRef = useRef(null);

  // modal state configuration
  const [modalConfig, setModalConfig] = useState({
    isOpen: false,
    type: null, // 'rename', 'delete_chat', 'delete_user'
    data: null,
    inputValue: ''
  });

  const abortControllerRef = useRef(null);
  const tokenRef = useRef(token);

  // keep tokenRef in sync with token state
  useEffect(() => {
    tokenRef.current = token;
  }, [token]);

  // axios interceptor for auth
  useEffect(() => {
    const reqInterceptor = api.interceptors.request.use(config => {
      if (tokenRef.current) {
        config.headers.Authorization = `Bearer ${tokenRef.current}`;
      }
      return config;
    });
    return () => api.interceptors.request.eject(reqInterceptor);
  }, []); // run once on mount

  // axios interceptor for response (auto-logout on 401)
  useEffect(() => {
    const resInterceptor = api.interceptors.response.use(
      response => response,
      error => {
        if (error.response && error.response.status === 401) {
          // token is invalid or expired -> force logout
          setUser(null);
          setToken(null);
          setSessions([]);
          setMessages([]);
          setCurrentSessionId(null);
        }
        return Promise.reject(error);
      }
    );
    return () => api.interceptors.response.eject(resInterceptor);
  }, []);

  // sync user to storage
  useEffect(() => {
    if (user && token) {
      localStorage.setItem('tase_user', JSON.stringify(user));
      localStorage.setItem('tase_token', token);
    } else {
      localStorage.removeItem('tase_user');
      localStorage.removeItem('tase_token');
      // if logging out, clear the session id too
      localStorage.removeItem('tase_current_session_id'); 
      setCurrentSessionId(null);
    }
  }, [user, token]);

  // sync session id to storage
  useEffect(() => {
    if (currentSessionId) {
      localStorage.setItem('tase_current_session_id', currentSessionId);
    } else {
      localStorage.removeItem('tase_current_session_id');
    }
  }, [currentSessionId]);

  // set browser tab title
  useEffect(() => {
    document.title = "TASE Bot";
  }, []);

  // apply theme
  useEffect(() => {
    if (user && user.theme) {
      document.body.setAttribute('data-theme', user.theme);
    } else {
      document.body.removeAttribute('data-theme'); // default dark
    }
  }, [user]);

  // click outside user menu
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target)) {
        setMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // main app logic

  useEffect(() => {
    if (token) {
      loadHistory();
    }
  }, [token]);

  useEffect(() => {
    if (token && currentSessionId) {
      fetchSessionMessages(currentSessionId);
    } else {
      setMessages([]);
    }
  }, [currentSessionId, token]);

  const loadHistory = async () => {
    try {
      const res = await api.get(`/chat/history/all`);
      setSessions(Array.isArray(res.data) ? res.data : []);
    } catch (err) {
      console.error("Failed to load history", err);
      toast.error("Failed to load chats");
      setSessions([]); 
    }
  };

  const fetchSessionMessages = async (sessionId) => {
    try {
      const res = await api.get(`/chat/history/${sessionId}`);
      setMessages(Array.isArray(res.data?.messages) ? res.data.messages : []);
    } catch (err) {
      console.error("Failed to load messages", err);
      // If the ID in storage is invalid (e.g., chat was deleted), reset it
      setCurrentSessionId(null); 
    }
  };

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userText = input;
    setInput('');
    setLoading(true);
    
    // cancel previous request if any (though ui prevents this usually)
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    const controller = new AbortController();
    abortControllerRef.current = controller;

    const tempMsg = { role: 'user', content: userText, timestamp: new Date() };
    setMessages(prev => [...prev, tempMsg]);

    try {
      const res = await api.post('/chat/message', {
        content: userText,
        session_id: currentSessionId
      }, { signal: controller.signal });

      if (!currentSessionId) {
        setCurrentSessionId(res.data.session_id);
        loadHistory();
      }

      setMessages(prev => [...prev, res.data.ai_msg]);
    } catch (err) {
      if (axios.isCancel(err)) {
        console.log("Request cancelled by user");
      } else {
        console.error(err);
        toast.error("Failed to send message");
      }
    } finally {
      setLoading(false);
      abortControllerRef.current = null;
    }
  };

  const handleStop = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setLoading(false);
    }
  };

  const executeRenameSession = async () => {
    const { id } = modalConfig.data;
    const newTitle = modalConfig.inputValue;
    if (!newTitle.trim()) return;

    try {
      // optimistic update
      setSessions(prev => prev.map(s => 
        (s.id === id || s._id === id) ? { ...s, title: newTitle } : s
      ));
      
      await api.put(`/chat/history/${id}`, { title: newTitle });
      closeModal();
    } catch (err) {
      toast.error("Failed to rename chat");
      loadHistory(); // revert on failure
    }
  };

  const executeDeleteSession = async () => {
    const { id } = modalConfig.data;
    try {
      // optimistic update
      setSessions(prev => prev.filter(s => (s.id !== id && s._id !== id)));
      if (currentSessionId === id) {
        setCurrentSessionId(null);
        setMessages([]);
      }

      await api.delete(`/chat/history/${id}`);
      closeModal();
    } catch (err) {
      toast.error("Failed to delete chat");
      loadHistory(); // revert
    }
  };

  const handleUpdateUser = async (updates) => {
    try {
      // optimistic update
      const updatedUser = { ...user, ...updates };
      setUser(updatedUser);

      await api.put(`/auth/profile`, updates);
      toast.success("Profile updated");
    } catch (err) {
      toast.error("Failed to update profile");
      // revert logic could go here
    }
  };

  const executeDeleteUser = async () => {
    try {
      await api.delete(`/auth/profile`);
      setUser(null);
      setToken(null);
      setSessions([]);
      setMessages([]);
      setCurrentSessionId(null);
      toast.success("Account deleted");
      closeModal();
    } catch (err) {
      toast.error("Failed to delete account");
    }
  };

  // modal handlers
  const closeModal = () => setModalConfig({ ...modalConfig, isOpen: false });

  const openRenameModal = (id, currentTitle) => {
    setModalConfig({
      isOpen: true,
      type: 'rename',
      data: { id },
      inputValue: currentTitle
    });
  };

  const openDeleteChatModal = (id) => {
    setModalConfig({ isOpen: true, type: 'delete_chat', data: { id }, inputValue: '' });
  };

  const openDeleteUserModal = () => {
    setModalConfig({ isOpen: true, type: 'delete_user', data: null, inputValue: '' });
  };


  const handleLogin = (data) => {
    setUser(data.user);
    setToken(data.access_token);
    setMenuOpen(false);
  };

  const currentSession = sessions.find(s => (s.id === currentSessionId || s._id === currentSessionId));

  if (!user) {
    return <LoginScreen onLogin={handleLogin} api={api} />;
  }

  return (
    <div className="app-container">
      <Toaster position="top-center" />
      {/* full width header */}
      <div className="app-header">
        <div className="header-left">
          <button 
            className="hamburger-btn" 
            onClick={() => setSidebarOpen(!sidebarOpen)}
            title="Toggle Sidebar"
          >
            ☰
          </button>
          <img src="/vite.svg" alt="App Logo" className="app-logo" />
          <h3>TASE Bot</h3>
        </div>
        
        <div className="header-center">
          {currentSession?.title || "New Chat"}
        </div>

        <div className="header-right">
          <div className="user-bubble-container" ref={userMenuRef}>
            <div
              className="user-bubble"
              onClick={() => setMenuOpen(!menuOpen)}
            >
              {(user.username || user.email || "?").charAt(0).toUpperCase()}
            </div>
            {menuOpen && (
              <div className="user-menu">
                <div className="user-greeting">Hello {user.username || "User"}</div>
                <div className="menu-item" onClick={() => {
                  setUser(null);
                  setToken(null);
                }}>
                  {/* simple logout icon svg */}
                  <svg className="logout-icon" viewBox="0 0 24 24">
                    <path d="M16 13v-2H7V8l-5 4 5 4v-3z"/>
                    <path d="M20 3h-9c-1.103 0-2 .897-2 2v4h2V5h9v14h-9v-4H9v4c0 1.103.897 2 2 2h9c1.103 0 2-.897 2-2V5c0-1.103-.897-2-2-2z"/>
                  </svg>
                  Log Out
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* main content: sidebar + chat */}
      <div className="app-content">
        <div className={`sidebar-wrapper ${sidebarOpen ? 'open' : ''}`}>
          <Sidebar
          collapsed={!sidebarOpen}
          user={user}
          sessions={sessions || []}
          currentSessionId={currentSessionId}
          onSelectSession={setCurrentSessionId}
          onRenameSession={openRenameModal}
          onDeleteSession={openDeleteChatModal}
          onNewChat={() => setCurrentSessionId(null)}
          onUpdateUser={handleUpdateUser}
          onDeleteUser={openDeleteUserModal}
          />
        </div>
        {/* overlay for mobile when sidebar is open */}
        {sidebarOpen && <div className="sidebar-overlay" onClick={() => setSidebarOpen(false)}></div>}

        <ChatArea
          messages={messages || []}
          input={input}
          setInput={setInput}
          loading={loading}
          onSend={handleSend}
          onStop={handleStop}
        />
      </div>

      {/* modals */}
      <Modal
        isOpen={modalConfig.isOpen}
        onClose={closeModal}
        title={
          modalConfig.type === 'rename' ? 'Rename Chat' :
          modalConfig.type === 'delete_chat' ? 'Delete Chat' :
          modalConfig.type === 'delete_user' ? 'Delete Account' : ''
        }
        actions={
          <>
            <button onClick={closeModal} style={{background: 'transparent', border: '1px solid var(--border-color)', color: 'var(--text-main)', padding: '8px 16px', borderRadius: '4px', cursor: 'pointer'}}>
              Cancel
            </button>
            <button 
              onClick={() => {
                if (modalConfig.type === 'rename') executeRenameSession();
                else if (modalConfig.type === 'delete_chat') executeDeleteSession();
                else if (modalConfig.type === 'delete_user') executeDeleteUser();
              }}
              style={{
                background: modalConfig.type === 'rename' ? 'var(--accent)' : '#d32f2f',
                color: 'white',
                border: 'none',
                padding: '8px 16px',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              {modalConfig.type === 'rename' ? 'Save' : 'Delete'}
            </button>
          </>
        }
      >
        {modalConfig.type === 'rename' && (
          <input 
            autoFocus
            value={modalConfig.inputValue}
            onChange={(e) => setModalConfig({...modalConfig, inputValue: e.target.value})}
            style={{width: '100%', padding: '10px', background: 'var(--bg-input)', border: '1px solid var(--border-color)', color: 'var(--text-main)', borderRadius: '4px'}}
          />
        )}
        {modalConfig.type === 'delete_chat' && (
          <p>Are you sure you want to delete this chat? This action cannot be undone.</p>
        )}
        {modalConfig.type === 'delete_user' && (
          <p>Are you sure you want to permanently delete your account? All your data will be lost.</p>
        )}
      </Modal>
    </div>
  );
}

export default App;