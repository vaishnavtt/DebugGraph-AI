import React from 'react';

export type BadgeVariant =
  | 'default'
  | 'success'
  | 'warning'
  | 'danger'
  | 'info'
  | 'purple'
  | 'cyan'
  | 'secondary'
  | 'outline'
  | 'accent'
  | 'gold'
  | 'midnight';

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  dot?: boolean;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'default',
  size = 'md',
  className = '',
  dot = false,
}) => {
  const variantStyles = {
    default: 'bg-ivory-200/80 text-slate-800 border-ivory-300',
    secondary: 'bg-ivory-100 text-slate-600 border-ivory-300',
    success: 'bg-emerald-50 text-emerald-800 border-emerald-300/80 shadow-[0_0_8px_rgba(16,185,129,0.15)]',
    warning: 'bg-amber-50 text-amber-900 border-amber-300/80',
    danger: 'bg-rose-50 text-rose-800 border-rose-300/80 shadow-[0_0_8px_rgba(244,63,94,0.15)]',
    info: 'bg-electric-50 text-electric-700 border-electric-200 shadow-[0_0_8px_rgba(0,102,255,0.15)]',
    cyan: 'bg-sky-50 text-sky-800 border-sky-300/80',
    purple: 'bg-indigo-50 text-indigo-800 border-indigo-200',
    accent: 'bg-violet-50 text-violet-800 border-violet-200',
    gold: 'bg-gold-50 text-gold-900 border-gold-300 shadow-[0_0_10px_rgba(197,160,89,0.2)]',
    midnight: 'bg-midnight-900 text-ivory-100 border-midnight-750 shadow-sm',
    outline: 'bg-white/80 backdrop-blur-sm text-slate-800 border-ivory-300 shadow-soft',
  };

  const dotStyles = {
    default: 'bg-slate-400',
    secondary: 'bg-slate-400',
    success: 'bg-emerald-500 shadow-[0_0_6px_#10B981]',
    warning: 'bg-amber-500 shadow-[0_0_6px_#F59E0B]',
    danger: 'bg-rose-500 shadow-[0_0_6px_#F43F5E]',
    info: 'bg-electric-500 shadow-[0_0_6px_#0066FF]',
    cyan: 'bg-sky-500',
    purple: 'bg-indigo-500',
    accent: 'bg-violet-500',
    gold: 'bg-gold-500 shadow-[0_0_6px_#C5A059]',
    midnight: 'bg-electric-400 shadow-[0_0_6px_#38BDF8]',
    outline: 'bg-slate-500',
  };

  const sizeStyles = {
    sm: 'text-[11px] px-2.5 py-0.5 gap-1.5 font-medium tracking-tight',
    md: 'text-xs px-3 py-1 gap-1.5 font-semibold tracking-tight',
    lg: 'text-xs px-3.5 py-1.5 gap-2 font-bold tracking-tight',
  };

  return (
    <span
      className={`inline-flex items-center rounded-full border transition-all ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
    >
      {dot && <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${dotStyles[variant]}`} />}
      <span>{children}</span>
    </span>
  );
};
