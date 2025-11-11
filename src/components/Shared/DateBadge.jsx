import React from 'react';
import { format } from 'date-fns';
import { Calendar } from 'lucide-react';

function DateBadge() {
  const today = new Date();
  
  return (
    <div className="date-badge">
      <Calendar size={14} />
      <span>Today: {format(today, 'EEEE, MMMM d, yyyy')}</span>
    </div>
  );
}

export default DateBadge;