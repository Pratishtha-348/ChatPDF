import React, { useState, useRef, useEffect } from 'react';
import { queryChatSession } from '../services/api';

function ChatScreen({ sessionId, filename }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };
  
  useEffect(scrollToBottom, [messages]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = { role: 'user', content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
        const response = await queryChatSession(sessionId, input);
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let aiResponse = '';
        
        setMessages(prev => [...prev, { role: 'assistant', content: '' }]);

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value, { stream: true });
            const lines = chunk.split('\n').filter(line => line.trim() !== '');

            for (const line of lines) {
                try {
                    const parsed = JSON.parse(line);
                    if (parsed.chunk) {
                        aiResponse += parsed.chunk;
                        setMessages(prev => {
                            const newMessages = [...prev];
                            newMessages[newMessages.length - 1].content = aiResponse;
                            return newMessages;
                        });
                    }
                    if (parsed.complete) {
                        console.log("Sources:", parsed.sources);
                    }
                } catch (e) {
                    console.error("Failed to parse JSON chunk:", line);
                }
            }
        }

    } catch (error) {
        setMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, I ran into an error. Please try again.' }]);
        console.error("Query failed:", error);
    } finally {
        setIsLoading(false);
    }
  };

  return (
    <div style={styles.chatContainer}>
      <h2 style={styles.chatHeader}>Chatting with: {filename}</h2>
      <div style={styles.messageList}>
        {messages.map((msg, index) => (
          <div key={index} style={msg.role === 'user' ? styles.userMessage : styles.aiMessage}>
            {msg.content}
          </div>
        ))}
        {isLoading && <div style={styles.aiMessage}><i>Thinking...</i></div>}
        <div ref={messagesEndRef} />
      </div>
      <form onSubmit={handleSubmit} style={styles.inputForm}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question about the document..."
          style={styles.input}
          disabled={isLoading}
        />
        <button type="submit" style={styles.button} disabled={isLoading}>Send</button>
      </form>
    </div>
  );
}

const styles = {
    chatContainer: { display: 'flex', flexDirection: 'column', height: '100%', maxWidth: '800px', margin: 'auto', fontFamily: 'sans-serif' },
    chatHeader: { padding: '20px', borderBottom: '1px solid #eee', textAlign: 'center' },
    messageList: { flex: 1, padding: '20px', overflowY: 'auto' },
    inputForm: { display: 'flex', padding: '20px', borderTop: '1px solid #eee' },
    input: { flex: 1, padding: '10px', borderRadius: '5px', border: '1px solid #ccc' },
    button: { padding: '10px 15px', marginLeft: '10px', border: 'none', backgroundColor: '#007bff', color: 'white', borderRadius: '5px', cursor: 'pointer' },
    userMessage: { backgroundColor: '#007bff', color: 'white', padding: '10px', borderRadius: '10px', alignSelf: 'flex-end', maxWidth: '80%', marginBottom: '10px', marginLeft: 'auto' },
    aiMessage: { backgroundColor: '#f1f1f1', color: 'black', padding: '10px', borderRadius: '10px', alignSelf: 'flex-start', maxWidth: '80%', marginBottom: '10px', whiteSpace: 'pre-wrap' },
};

export default ChatScreen;