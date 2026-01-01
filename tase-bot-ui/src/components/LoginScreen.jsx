import { useState } from 'react';

/**
 * handles user authentication (login and signup).
 */
export default function LoginScreen({ onLogin, api }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [username, setUsername] = useState('');
  const [isSignup, setIsSignup] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      if (isSignup) {
        const res = await api.post('/auth/signup', { 
            email, 
            username, 
            password, 
            risk_level: "Medium" 
        });
        onLogin(res.data);
      } else {
        const res = await api.post('/auth/login', { email, password });
        onLogin(res.data);
      }
    } catch (err) {
      setError(err.response?.data?.detail || "An error occurred");
    }
  };

  return (
    <div className="login-container">
      <div className="login-box">
        <h2>TASE Bot | {isSignup ? 'Sign Up' : 'Login'}</h2>
        {error && <div className="error">{error}</div>}
        <form onSubmit={handleSubmit}>
          {isSignup && (
            <input 
              placeholder="Username" 
              value={username} 
              onChange={e => setUsername(e.target.value)} 
              required 
            />
          )}
          <input 
            placeholder="Email" 
            value={email} 
            onChange={e => setEmail(e.target.value)} 
            required 
            type="email"
          />
          <input 
            placeholder="Password" 
            value={password} 
            onChange={e => setPassword(e.target.value)} 
            required 
            type="password"
          />
          <button type="submit">{isSignup ? 'Create Account' : 'Enter'}</button>
        </form>
        <p style={{marginTop: '15px'}}>
          {isSignup ? "Already have an account? " : "Need an account? "}
          <span onClick={() => setIsSignup(!isSignup)} style={{cursor: 'pointer', color: 'var(--accent)', textDecoration: 'underline'}}>
            {isSignup ? "Login" : "Sign Up"}
          </span>
        </p>
      </div>
    </div>
  );
}