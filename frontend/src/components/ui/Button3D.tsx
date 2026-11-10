import React from 'react';

export type Button3DVariant = 'primary' | 'gold' | 'midnight' | 'surface' | 'ghost';
export type Button3DSize = 'sm' | 'md' | 'lg';

interface Button3DProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Button3DVariant;
  size?: Button3DSize;
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
  loading?: boolean;
}

export const Button3D: React.FC<Button3DProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  icon,
  iconPosition = 'left',
  loading = false,
  className = '',
  disabled,
  ...props
}) => {
  const baseClasses =
    'btn-3d inline-flex items-center justify-center font-bold tracking-tight rounded-xl select-none transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none disabled:shadow-none cursor-pointer';

  const sizeClasses = {
    sm: 'text-xs px-3.5 py-1.5 gap-1.5',
    md: 'text-xs sm:text-sm px-5 py-2.5 gap-2',
    lg: 'text-sm sm:text-base px-6 py-3 gap-2.5',
  }[size];

  const variantClasses = {
    primary: 'btn-3d-primary',
    gold: 'btn-3d-gold',
    midnight: 'btn-3d-midnight',
    surface: 'btn-3d-surface',
    ghost:
      'bg-transparent hover:bg-ivory-200/70 text-slate-700 hover:text-slate-950 border border-transparent hover:border-ivory-300 active:translate-y-0.5',
  }[variant];

  return (
    <button
      className={`${baseClasses} ${sizeClasses} ${variantClasses} ${className}`}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <span className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin shrink-0" />
      ) : icon && iconPosition === 'left' ? (
        <span className="shrink-0">{icon}</span>
      ) : null}

      <span>{children}</span>

      {!loading && icon && iconPosition === 'right' ? (
        <span className="shrink-0">{icon}</span>
      ) : null}
    </button>
  );
};

