import React from 'react';
import { User } from 'lucide-react';

function UserProfile({ email, role }) {
  const getInitials = (email) => {
    const name = email.split('@')[0];
    const parts = name.replace(/[._]/g, ' ').split(' ');
    if (parts.length >= 2) {
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return name.slice(0, 2).toUpperCase();
  };

  return (
    <div className="user-profile">
      <div className="user-avatar">
        {getInitials(email)}
      </div>
      <div className="user-info">
        <p className="user-email">{email}</p>
        <p className="user-role">{role === 'admin' ? 'Administrator' : 'User'}</p>
      </div>
    </div>
  );
}

export default UserProfile;