import React from 'react';
import styles from './Header.module.css';

interface HeaderProps {
  title?: string;
  user?: {
    name: string;
    avatarUrl?: string;
  };
}

import { ThemeToggle } from '@/components/ui/ThemeToggle';

export function Header({ title = 'Dashboard', user }: HeaderProps) {
  return (
    <header className={styles.header}>
      <h1 className={styles.title}>{title}</h1>
      <div
        className={styles.userSection}
        style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}
      >
        <ThemeToggle />
        {/* Placeholder for user profile/avatar - will be implemented later */}
        {user ? <span>{user.name}</span> : <span>Guest</span>}
      </div>
    </header>
  );
}
