import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Header from './Header';

const Layout = () => {
    return (
        <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--bg-primary)' }}>
            <Sidebar />
            <div style={{ flex: 1, marginLeft: '260px', display: 'flex', flexDirection: 'column' }}>
                <Header />
                <main style={{ flex: 1, padding: '2rem', overflowY: 'auto' }}>
                    <div className="container">
                        <Outlet />
                    </div>
                </main>
            </div>
        </div>
    );
};

export default Layout;
