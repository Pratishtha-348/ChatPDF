import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { uploadPdfSession } from '../services/api';

function UploadScreen({ onUploadSuccess }) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const onDrop = useCallback(async (acceptedFiles) => {
    if (acceptedFiles.length === 0) return;
    const file = acceptedFiles[0];
    
    setIsLoading(true);
    setError('');

    try {
      const response = await uploadPdfSession(file);
      onUploadSuccess(response.data.session_id, response.data.filename);
    } catch (err) {
      setError('Failed to upload PDF. Please try again.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  }, [onUploadSuccess]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ 
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    multiple: false,
  });

  return (
    <div style={styles.container}>
      <h1 style={styles.title}>Chat with any PDF</h1>
      <p style={styles.subtitle}>
        Upload a PDF and ask questions instantly without signing up.
      </p>
      <div {...getRootProps()} style={isDragActive ? {...styles.dropzone, ...styles.dropzoneActive} : styles.dropzone}>
        <input {...getInputProps()} />
        {isLoading ? (
          <p>Uploading and Processing...</p>
        ) : (
          <p>Click to upload, or drag PDF here</p>
        )}
      </div>
      {error && <p style={styles.errorText}>{error}</p>}
    </div>
  );
}

const styles = {
    container: { textAlign: 'center', padding: '50px 20px', fontFamily: 'sans-serif' },
    title: { fontSize: '2.5rem', marginBottom: '10px' },
    subtitle: { fontSize: '1.2rem', color: '#666', maxWidth: '600px', margin: '0 auto 30px' },
    dropzone: { border: '2px dashed #ccc', borderRadius: '10px', padding: '40px', cursor: 'pointer', transition: 'border .24s ease-in-out' },
    dropzoneActive: { borderColor: '#007bff' },
    errorText: { color: 'red', marginTop: '15px' },
};

export default UploadScreen;