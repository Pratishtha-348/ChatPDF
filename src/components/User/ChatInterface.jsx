import React, { useState, useEffect, useRef } from 'react';
import { Send, Loader } from 'lucide-react';
import {
  queryRAGStream,
  saveMessage,
  getConversationHistory,
  clearConversations,
} from '../../services/api';
import Sidebar from './Sidebar';

function ChatInterface({ isAdmin = false }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    loadHistory();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadHistory = async () => {
    try {
      const response = await getConversationHistory();
      setMessages(response.data.messages);
    } catch (err) {
      console.error('Failed to load history:', err);
    }
  };

  const handleNewChat = async () => {
    if (window.confirm('Start a new conversation? This will clear the current chat.')) {
      try {
        await clearConversations();
        setMessages([]);
      } catch (err) {
        console.error('Failed to clear chat:', err);
      }
    }
  };

  const handleSuggestion = (suggestion) => {
    setInput(suggestion);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = { role: 'user', content: input };
    setMessages((prev) => [...prev, userMessage]);
    
    try {
      await saveMessage('user', input);
    } catch (err) {
      console.error('Failed to save message:', err);
    }

    const query = input;
    setInput('');
    setLoading(true);

    // Add placeholder for AI response
    setMessages((prev) => [...prev, { role: 'assistant', content: '' }]);

    try {
      const response = await queryRAGStream(query);
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let aiResponse = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n').filter((line) => line.trim() !== '');

        for (const line of lines) {
          try {
            const parsed = JSON.parse(line);
            if (parsed.chunk) {
              aiResponse += parsed.chunk;
              setMessages((prev) => {
                const newMessages = [...prev];
                newMessages[newMessages.length - 1].content = aiResponse;
                return newMessages;
              });
            }
          } catch (e) {
            console.error('Failed to parse chunk:', line);
          }
        }
      }

      // Save complete AI response
      try {
        await saveMessage('assistant', aiResponse);
      } catch (err) {
        console.error('Failed to save AI message:', err);
      }
    } catch (error) {
      console.error('Query failed:', error);
      setMessages((prev) => {
        const newMessages = [...prev];
        newMessages[newMessages.length - 1].content =
          'Sorry, I encountered an error. Please try again.';
        return newMessages;
      });
    } finally {
      setLoading(false);
    }
  };

  const ChatContent = () => (
    <div className="chat-interface">
      <div className="messages-container">
        {messages.length === 0 && (
          <div className="welcome-message">
            <h2>👋 Welcome!</h2>
            <p>Ask me anything about the company documents.</p>
          </div>
        )}

        {messages.map((message, index) => (
          <div key={index} className={`message ${message.role}`}>
            <div className="message-content">
              {message.content || <Loader className="spinner" size={20} />}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <form className="chat-input-form" onSubmit={handleSubmit}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question..."
          disabled={loading}
          className="chat-input"
        />
        <button type="submit" disabled={loading || !input.trim()} className="btn-send">
          <Send size={20} />
        </button>
      </form>
    </div>
  );

  // For admin dashboard (embedded chat)
  if (isAdmin) {
    return <ChatContent />;
  }

  // For user interface (full layout with sidebar)
  return (
    <div className="chat-layout">
      <Sidebar onNewChat={handleNewChat} onSuggestionClick={handleSuggestion} />
      <ChatContent />
    </div>
  );
}

export default ChatInterface;