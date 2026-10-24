import React from 'react';
import { getInitials } from '../../utils/formatters';

/**
 * Avatar Component
 * Circular monogram avatar with bold initials.
 */
export default function Avatar({ name, size = 'md', className = '' }) {
  const initials = getInitials(name);

  const sizeStyles = {
    sm: 'w-8 h-8 text-xs font-bold',
    md: 'w-10 h-10 text-sm font-bold',
    lg: 'w-12 h-12 text-base font-bold',
  };

  return (
    <div
      className={`rounded-full bg-indigo-600 text-white flex items-center justify-center select-none shrink-0 shadow-xs ${
        sizeStyles[size] || sizeStyles.md
      } ${className}`}
      title={name || 'Student'}
    >
      {initials}
    </div>
  );
}
