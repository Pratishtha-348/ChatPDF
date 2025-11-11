import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import Login from './components/auth/Login';
import Register from './components/auth/Register';
import AdminDashboard from './components/Admin/AdminDashboard';
import ChatInterface from './components/User/ChatInterface';
import UploadScreen from './components/UploadScreen';
import ChatScreen from './components/ChatScreen';

function AppContent() {
  const { user, loading } = useAuth();
  const [authView, setAuthView] = useState('login'); // 'login' or 'register'
  const [showAdHocChat, setShowAdHocChat] = useState(false);
  const [adHocSession, setAdHocSession] = useState(null);

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="spinner"></div>
        <p>Loading...</p>
      </div>
    );
  }

  // Not authenticated - show auth screens
  if (!user) {
    return (
      <div className="auth-container">
        <div className="auth-box">
          {authView === 'login' ? (
            <Login onSwitchToRegister={() => setAuthView('register')} />
          ) : (
            <Register onSwitchToLogin={() => setAuthView('login')} />
          )}
        </div>

        {/* Ad-hoc PDF chat option */}
        <div className="divider">
          <span>OR</span>
        </div>

        <button
          className="btn-secondary"
          onClick={() => setShowAdHocChat(true)}
        >
          Try without login - Chat with your PDF
        </button>

        {/* Ad-hoc chat modal/overlay */}
        {showAdHocChat && (
          <div className="modal-overlay" onClick={() => setShowAdHocChat(false)}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              {!adHocSession ? (
                <UploadScreen
                  onUploadSuccess={(sessionId, filename) => {
                    setAdHocSession({ id: sessionId, filename });
                  }}
                />
              ) : (
                <ChatScreen
                  sessionId={adHocSession.id}
                  filename={adHocSession.filename}
                />
              )}
              <button
                className="modal-close"
                onClick={() => {
                  setShowAdHocChat(false);
                  setAdHocSession(null);
                }}
              >
                ✕
              </button>
            </div>
          </div>
        )}
      </div>
    );
  }

  // Authenticated users
  if (user.role === 'admin') {
    return <AdminDashboard />;
  }

  return <ChatInterface />;
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;