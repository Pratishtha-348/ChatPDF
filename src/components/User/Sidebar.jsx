import React from 'react';
import { useAuth } from '../../context/AuthContext';
import { LogOut, Plus, Lightbulb } from 'lucide-react';
import UserProfile from '../Shared/UserProfile';
import DateBadge from '../Shared/DateBadge';

function Sidebar({ onNewChat, onSuggestionClick }) {
  const { user, logout } = useAuth();

  const suggestions = [
    "What are the company policies?",
    "Tell me about employee benefits",
    "What are the upcoming holidays?",
    "Explain the referral program",
  ];

  return (
    <div className="chat-sidebar">
      <div className="sidebar-header">
        <h2>💬 AI Assistant</h2>
      </div>

      <UserProfile email={user.email} role={user.role} />
      <DateBadge />

      <button className="btn-new-chat" onClick={onNewChat}>
        <Plus size={20} />
        New Chat
      </button>

      <div className="suggestions-section">
        <h3>
          <Lightbulb size={18} />
          Try asking:
        </h3>
        {suggestions.map((suggestion, index) => (
          <button
            key={index}
            className="suggestion-button"
            onClick={() => onSuggestionClick(suggestion)}
          >
            {suggestion}
          </button>
        ))}
      </div>

      <button className="btn-logout" onClick={logout}>
        <LogOut size={20} />
        Logout
      </button>
    </div>
  );
}

export default Sidebar;