import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_URL,
});

// Add auth token to requests
export const setAuthToken = (token) => {
  if (token) {
    apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  } else {
    delete apiClient.defaults.headers.common['Authorization'];
  }
};

// Admin endpoints
export const uploadDocument = (file, title = null) => {
  const formData = new FormData();
  formData.append('file', file);
  if (title) formData.append('title', title);
  
  return apiClient.post('/admin/ingest_pdf', formData);
};

export const getDocuments = () => {
  return apiClient.get('/admin/documents');
};

export const deleteDocument = (docId) => {
  return apiClient.delete(`/admin/document/${docId}`);
};

// Query endpoints
export const queryRAG = (query, topK = 8) => {
  return apiClient.post('/rag/query', { query, top_k: topK });
};

export const queryRAGStream = async (query, topK = 8) => {
  const response = await fetch(`${API_URL}/rag/query_stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': apiClient.defaults.headers.common['Authorization'],
    },
    body: JSON.stringify({ query, top_k: topK }),
  });
  return response;
};

// Conversation endpoints
export const saveMessage = (role, content) => {
  return apiClient.post('/conversations/save', { role, content });
};

export const getConversationHistory = () => {
  return apiClient.get('/conversations/history');
};

export const clearConversations = () => {
  return apiClient.delete('/conversations/clear');
};

// Ad-hoc PDF chat (from previous implementation)
// Ad-hoc PDF chat (from previous implementation)
export const uploadPdfSession = (file) => {
  const formData = new FormData();
  formData.append('file', file);
  return apiClient.post('/chat/upload', formData);
};

export const queryChatSession = async (sessionId, query, topK = 5) => {
  const formData = new FormData();
  formData.append('session_id', sessionId);
  formData.append('query', query);
  formData.append('top_k', topK.toString());

  return fetch(`${apiClient.defaults.baseURL}/chat/query`, {
    method: 'POST',
    body: formData,
  });
};