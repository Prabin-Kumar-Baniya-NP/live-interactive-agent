'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import styles from './Sidebar.module.css';

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

export function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const pathname = usePathname();

  const navItems = [
    { href: '/dashboard', label: 'Dashboard', icon: 'Items' }, // Placeholder icon
    { href: '/agents', label: 'Agents', icon: 'Users' },
    { href: '/templates', label: 'Templates', icon: 'FileText' },
  ];

  return (
    <aside className={`${styles.sidebar} ${collapsed ? styles.collapsed : ''}`}>
      <div className={styles.header}>
        {!collapsed && <span style={{ fontWeight: 'bold' }}>Platform</span>}
        <button
          onClick={onToggle}
          style={{
            marginLeft: 'auto',
            border: 'none',
            background: 'none',
            cursor: 'pointer',
          }}
        >
          {collapsed ? '>>' : '<<'}
        </button>
      </div>

      <nav className={styles.nav}>
        {navItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={`${styles.navItem} ${
              pathname === item.href ? styles.active : ''
            }`}
          >
            <span className={styles.icon}>{/* Icon Placeholder */}</span>
            {!collapsed && <span className={styles.text}>{item.label}</span>}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
