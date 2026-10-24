import React, { useState } from 'react';
import { Eye, EyeOff } from 'lucide-react';

/**
 * InputField Component
 * High-contrast input field with clear typography, focus ring, and password toggle.
 */
export default function InputField({
  label,
  name,
  type = 'text',
  value,
  onChange,
  placeholder,
  error,
  hint,
  required = false,
  disabled = false,
  className = '',
  icon: Icon,
  ...props
}) {
  const [showPassword, setShowPassword] = useState(false);
  const isPasswordType = type === 'password';
  const effectiveType = isPasswordType ? (showPassword ? 'text' : 'password') : type;

  return (
    <div className={`w-full flex flex-col gap-1.5 ${className}`}>
      {(label || required) && (
        <div className="flex items-center justify-between">
          {label && (
            <label
              htmlFor={name}
              className="text-xs font-bold text-slate-800 select-none"
            >
              {label}
            </label>
          )}
          {required && (
            <span className="text-xs font-medium text-slate-400">
              Required
            </span>
          )}
        </div>
      )}

      <div className="relative flex items-center">
        {Icon && (
          <div className="absolute left-3.5 text-slate-400 pointer-events-none">
            <Icon className="w-4 h-4" />
          </div>
        )}

        <input
          id={name}
          name={name}
          type={effectiveType}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          disabled={disabled}
          required={required}
          className={`w-full bg-white text-slate-900 text-sm px-4 py-2.5 rounded-xl border transition-all outline-none shadow-xs
            ${Icon ? 'pl-10' : ''}
            ${isPasswordType ? 'pr-11' : ''}
            ${
              error
                ? 'border-rose-400 focus:ring-2 focus:ring-rose-100'
                : 'border-slate-300 focus:border-indigo-600 focus:ring-2 focus:ring-indigo-100'
            }
            ${disabled ? 'bg-slate-50 text-slate-400 cursor-not-allowed' : ''}
            placeholder:text-slate-400 font-medium
          `}
          {...props}
        />

        {isPasswordType && (
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-3.5 text-slate-400 hover:text-slate-700 transition-colors p-1 focus:outline-none"
            tabIndex={-1}
            aria-label={showPassword ? 'Hide password' : 'Show password'}
          >
            {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
          </button>
        )}
      </div>

      {error && (
        <p className="text-xs text-rose-600 font-semibold mt-0.5">{error}</p>
      )}

      {hint && !error && (
        <p className="text-xs text-slate-500 font-medium mt-0.5">{hint}</p>
      )}
    </div>
  );
}
