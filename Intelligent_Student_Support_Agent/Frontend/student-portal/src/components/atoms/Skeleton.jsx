import React from 'react';

/**
 * Skeleton atom
 * Restrained placeholder indicator while data is loading.
 */
export default function Skeleton({
  width = 'w-full',
  height = 'h-4',
  rounded = 'rounded-[4px]',
  className = '',
}) {
  return (
    <div
      className={`bg-slate-200/70 animate-pulse ${width} ${height} ${rounded} ${className}`}
    />
  );
}
