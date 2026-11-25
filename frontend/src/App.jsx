import React, { useState } from 'react';
import Login from './components/Login';
import Dashboard from './pages/Dashboard';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  return (
    <div>
      {!isAuthenticated ? (
        <Login onLoginSuccess={() => setIsAuthenticated(true)} />
      ) : (
        <Dashboard onLogout={() => {
          localStorage.removeItem('token');
          setIsAuthenticated(false);
        }} />
      )}
    </div>
  );
}

export default App;