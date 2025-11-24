import React, { createContext, useState, useContext, useEffect } from 'react';
import { authAPI, socket } from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const checkAuth = async () => {
            try {
                const response = await authAPI.checkStatus();
                if (response.data.isAuthenticated) {
                    setUser(response.data.user);
                    socket.connect();
                }
            } catch (error) {
                console.log('Not authenticated');
            } finally {
                setLoading(false);
            }
        };

        checkAuth();

        return () => {
            if (socket.connected) socket.disconnect();
        };
    }, []);

    const login = async (email, password) => {
        try {
            const response = await authAPI.login(email, password);

            if (response.data.status === 'success') {
                setUser(response.data.user);
                socket.connect();
                return { success: true };
            }
            return {
                success: false,
                error: response.data.message || 'Login failed',
                emailVerified: response.data.email_verified !== undefined ? response.data.email_verified : true
            };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.message || 'Login failed',
                emailVerified: error.response?.data?.email_verified !== undefined ? error.response?.data?.email_verified : true
            };
        }
    };

    const logout = async () => {
        try {
            await authAPI.logout();
            setUser(null);
            socket.disconnect();
        } catch (error) {
            console.error('Logout failed', error);
        }
    };

    const register = async (email, password, name) => {
        try {
            const response = await authAPI.register(email, password, name);

            if (response.data.status === 'success') {
                // Don't auto-login after registration - user needs to verify email
                return {
                    success: true,
                    message: response.data.message || 'Registration successful. Please check your email to verify your account.',
                    emailVerified: response.data.email_verified || false
                };
            }
            throw new Error(response.data.message || 'Registration failed');
        } catch (error) {
            throw new Error(error.response?.data?.message || error.message || 'Registration failed');
        }
    };

    const verifyEmail = async (token) => {
        try {
            const response = await authAPI.verifyEmail(token);
            if (response.data.status === 'success') {
                setUser(response.data.user);
                socket.connect();
                return { success: true, message: response.data.message };
            }
            throw new Error(response.data.message || 'Email verification failed');
        } catch (error) {
            throw new Error(error.response?.data?.message || error.message || 'Email verification failed');
        }
    };

    const resendVerification = async (email) => {
        try {
            const response = await authAPI.resendVerification(email);
            return { success: true, message: response.data.message };
        } catch (error) {
            throw new Error(error.response?.data?.message || error.message || 'Failed to resend verification email');
        }
    };

    const canTrade = () => {
        return user && user.email_verified && user.can_trade;
    };

    const isAdmin = () => {
        return user && (user.role === 'admin' || user.role === 'owner');
    };

    const isOwner = () => {
        return user && user.role === 'owner';
    };

    return (
        <AuthContext.Provider value={{
            user,
            login,
            logout,
            register,
            loading,
            verifyEmail,
            resendVerification,
            canTrade,
            isAdmin,
            isOwner,
            emailVerified: user?.email_verified || false,
            role: user?.role || 'trader'
        }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);
