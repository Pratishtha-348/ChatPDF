import React, { useState } from 'react';
import { register } from '../../services/auth';
import { UserPlus, Mail, Lock, Key } from 'lucide-react';

function Register({ onSwitchToLogin }) {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    role: 'user',
    adminKey: ''
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (formData.password.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }

    setLoading(true);

    try {
      await register(
        formData.email,
        formData.password,
        formData.role,
        formData.role === 'admin' ? formData.adminKey : null
      );
      setSuccess('Registration successful! Please login.');
      setTimeout(() => onSwitchToLogin(), 2000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-form">
      <div className="auth-header">
        <UserPlus size={40} />
        <h2>Create Account</h2>
        <p>Join the AI knowledge base</p>
      </div>

      <div className="role-selector">
        <button
          type="button"
          className={formData.role === 'user' ? 'active' : ''}
          onClick={() => setFormData({ ...formData, role: 'user' })}
        >
          User
        </button>
        <button
          type="button"
          className={formData.role === 'admin' ? 'active' : ''}
          onClick={() => setFormData({ ...formData, role: 'admin' })}
        >
          Admin
        </button>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <Mail size={18} />
          <input
            type="email"
            name="email"
            placeholder="Email"
            value={formData.email}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group">
          <Lock size={18} />
          <input
            type="password"
            name="password"
            placeholder="Password"
            value={formData.password}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group">
          <Lock size={18} />
          <input
            type="password"
            name="confirmPassword"
            placeholder="Confirm Password"
            value={formData.confirmPassword}
            onChange={handleChange}
            required
          />
        </div>

        {formData.role === 'admin' && (
          <div className="form-group">
            <Key size={18} />
            <input
              type="password"
              name="adminKey"
              placeholder="Admin Secret Key"
              value={formData.adminKey}
              onChange={handleChange}
              required
            />
          </div>
        )}

        {error && <div className="error-message">{error}</div>}
        {success && <div className="success-message">{success}</div>}

        <button type="submit" className="btn-primary" disabled={loading}>
          {loading ? 'Creating account...' : 'Create Account'}
        </button>
      </form>

      <p className="auth-switch">
        Already have an account?{' '}
        <button onClick={onSwitchToLogin} className="link-button">
          Login
        </button>
      </p>
    </div>
  );
}

export default Register;