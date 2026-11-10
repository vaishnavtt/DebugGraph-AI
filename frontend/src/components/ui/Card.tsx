import React from 'react';

export type CardVariant = 'porcelain' | 'ivory' | 'midnight' | 'glass';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  title?: string | React.ReactNode;
  subtitle?: string | React.ReactNode;
  action?: React.ReactNode;
  icon?: React.ReactNode;
  hoverEffect?: boolean;
  variant?: CardVariant;
  surface?: CardVariant;
}

export const Card: React.FC<CardProps> = ({
  children,
  className = '',
  title,
  subtitle,
  action,
  icon,
  hoverEffect = false,
  variant,
  surface,
}) => {
  const resolvedVariant: CardVariant = variant || surface || 'porcelain';

  const variantClasses = {
    porcelain:
      'bg-white border border-ivory-300/80 shadow-card text-slate-900',
    ivory:
      'bg-ivory-100/90 border border-ivory-300 shadow-soft text-slate-900',
    midnight:
      'bg-midnight-900 border border-midnight-750 shadow-2xl text-ivory-50',
    glass:
      'glass-panel text-slate-900',
  }[resolvedVariant];

  const hoverClasses = hoverEffect
    ? resolvedVariant === 'midnight'
      ? 'hover:border-electric-500/50 hover:shadow-glow-electric hover:-translate-y-1 transition-all duration-300'
      : 'hover:border-gold-300 hover:shadow-card-hover hover:-translate-y-1 transition-all duration-300'
    : 'transition-all duration-200';

  return (
    <div
      className={`rounded-3xl p-6 sm:p-7 relative overflow-hidden ${variantClasses} ${hoverClasses} ${className}`}
    >
      {(title || subtitle || action) && (
        <div
          className={`flex items-center justify-between pb-4 mb-5 border-b flex-wrap gap-3 ${
            resolvedVariant === 'midnight' ? 'border-midnight-800' : 'border-ivory-200'
          }`}
        >
          <div className="flex items-center gap-3.5">
            {icon && (
              <div
                className={`w-10 h-10 rounded-2xl flex items-center justify-center shrink-0 border ${
                  resolvedVariant === 'midnight'
                    ? 'bg-midnight-800 border-midnight-700 text-gold-300'
                    : 'bg-ivory-100/80 border-ivory-200 text-slate-800'
                }`}
              >
                {icon}
              </div>
            )}
            <div>
              {title && (
                <div
                  className={`font-bold text-sm md:text-base tracking-tight leading-snug ${
                    resolvedVariant === 'midnight' ? 'text-ivory-50' : 'text-slate-900'
                  }`}
                >
                  {title}
                </div>
              )}
              {subtitle && (
                <div
                  className={`text-xs mt-0.5 leading-normal ${
                    resolvedVariant === 'midnight' ? 'text-slate-400' : 'text-slate-500'
                  }`}
                >
                  {subtitle}
                </div>
              )}
            </div>
          </div>
          {action && <div className="shrink-0">{action}</div>}
        </div>
      )}
      {children}
    </div>
  );
};
