import React, { useState, useEffect } from 'react';
import { FileText, Trash2, Calendar } from 'lucide-react';
import { getDocuments, deleteDocument } from '../../services/api';
import { format } from 'date-fns';

function DocumentList({ refreshTrigger }) {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(null);

  const fetchDocuments = async () => {
    try {
      const response = await getDocuments();
      setDocuments(response.data);
    } catch (err) {
      console.error('Failed to fetch documents:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, [refreshTrigger]);

  const handleDelete = async (docId) => {
    if (!window.confirm('Are you sure you want to delete this document?')) {
      return;
    }

    setDeleting(docId);
    try {
      await deleteDocument(docId);
      setDocuments(documents.filter(doc => doc.id !== docId));
    } catch (err) {
      alert('Failed to delete document');
    } finally {
      setDeleting(null);
    }
  };

  if (loading) {
    return <div className="loading">Loading documents...</div>;
  }

  if (documents.length === 0) {
    return (
      <div className="empty-state">
        <FileText size={64} className="empty-icon" />
        <h3>No documents yet</h3>
        <p>Upload your first document to get started</p>
      </div>
    );
  }

  return (
    <div className="document-list">
      {documents.map((doc) => (
        <div key={doc.id} className="document-card">
          <div className="doc-icon">
            <FileText size={24} />
          </div>
          <div className="doc-info">
            <h4>{doc.title || 'Untitled Document'}</h4>
            <div className="doc-meta">
              <Calendar size={14} />
              <span>{format(new Date(doc.created_at), 'MMM d, yyyy HH:mm')}</span>
              <span className="doc-uploader">• {doc.uploaded_by}</span>
            </div>
          </div>
          <button
            className="btn-delete"
            onClick={() => handleDelete(doc.id)}
            disabled={deleting === doc.id}
          >
            <Trash2 size={18} />
          </button>
        </div>
      ))}
    </div>
  );
}

export default DocumentList;