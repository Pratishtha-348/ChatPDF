import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { LogOut, Upload as UploadIcon, FileText, MessageSquare } from 'lucide-react';
import UserProfile from '../Shared/UserProfile';
import DateBadge from '../Shared/DateBadge';
import DocumentUpload from './DocumentUpload';
import DocumentList from './DocumentList';
import ChatInterface from '../User/ChatInterface';

function AdminDashboard() {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState('upload');
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const handleUploadSuccess = () => {
    setRefreshTrigger(prev => prev + 1);
    setActiveTab('documents');
  };

  return (
    <div className="admin-dashboard">
      {/* Sidebar */}
      <div className="dashboard-sidebar">
        <div className="sidebar-header">
          <h2>🔧 Admin Panel</h2>
        </div>

        <UserProfile email={user.email} role={user.role} />
        <DateBadge />

        <nav className="sidebar-nav">
          <button
            className={activeTab === 'upload' ? 'active' : ''}
            onClick={() => setActiveTab('upload')}
          >
            <UploadIcon size={20} />
            Upload Documents
          </button>
          <button
            className={activeTab === 'documents' ? 'active' : ''}
            onClick={() => setActiveTab('documents')}
          >
            <FileText size={20} />
            Manage Documents
          </button>
          <button
            className={activeTab === 'chat' ? 'active' : ''}
            onClick={() => setActiveTab('chat')}
          >
            <MessageSquare size={20} />
            Test Chat
          </button>
        </nav>

        <button className="btn-logout" onClick={logout}>
          <LogOut size={20} />
          Logout
        </button>
      </div>

      {/* Main Content */}
      <div className="dashboard-content">
        <div className="content-header">
          <h1>
            {activeTab === 'upload' && '📤 Upload Documents'}
            {activeTab === 'documents' && '📚 Document Library'}
            {activeTab === 'chat' && '💬 Test Chat Interface'}
          </h1>
          <p>
            {activeTab === 'upload' && 'Add new documents to the knowledge base'}
            {activeTab === 'documents' && 'Manage and organize uploaded documents'}
            {activeTab === 'chat' && 'Test queries against the knowledge base'}
          </p>
        </div>

        <div className="content-body">
          {activeTab === 'upload' && (
            <DocumentUpload onUploadSuccess={handleUploadSuccess} />
          )}
          {activeTab === 'documents' && (
            <DocumentList refreshTrigger={refreshTrigger} />
          )}
          {activeTab === 'chat' && (
            <ChatInterface isAdmin={true} />
          )}
        </div>
      </div>
    </div>
  );
}

export default AdminDashboard;