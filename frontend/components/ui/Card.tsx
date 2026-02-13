import React from 'react';
import styles from './Card.module.css';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  padding?: 'none' | 'sm' | 'md' | 'lg';
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, children, padding = 'md', style, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={`${styles.card} ${styles[padding]} ${className || ''}`}
        style={style}
        {...props}
      >
        {children}
      </div>
    );
  }
);

Card.displayName = 'Card';
