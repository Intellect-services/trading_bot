import React, { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import { emailAPI } from '../services/api';
import { MailX, MailCheck, ArrowLeft } from 'lucide-react';

const Unsubscribe = () => {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const token = searchParams.get('token');
    const status = searchParams.get('status') || 'success';
    const [resubscribeMessage, setResubscribeMessage] = useState(null);
    const [resubscribing, setResubscribing] = useState(false);

    const handleResubscribe = async () => {
        if (!token) {
            setResubscribeMessage({ type: 'error', text: 'Missing unsubscribe token.' });
            return;
        }
        setResubscribing(true);
        setResubscribeMessage(null);
        try {
            const response = await emailAPI.resubscribe(token);
            if (response.data.status === 'success') {
                setResubscribeMessage({ type: 'success', text: 'You are back on the list. Expect the next drop soon!' });
            } else {
                setResubscribeMessage({ type: 'error', text: response.data.message || 'Unable to resubscribe.' });
            }
        } catch (error) {
            console.error('Failed to resubscribe', error);
            setResubscribeMessage({ type: 'error', text: 'Unable to resubscribe right now.' });
        } finally {
            setResubscribing(false);
        }
    };

    return (
        <div style={{
            minHeight: '100vh',
            background: 'radial-gradient(circle at top, rgba(99,102,241,0.2), #05060a)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '2rem'
        }}>
            <motion.div
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
                style={{
                    width: '100%',
                    maxWidth: '520px',
                    background: 'rgba(15,16,24,0.9)',
                    borderRadius: '24px',
                    padding: '2.5rem',
                    boxShadow: '0 25px 80px rgba(0,0,0,0.6)',
                    border: '1px solid rgba(255,255,255,0.05)'
                }}
            >
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem' }}>
                    <div style={{
                        width: 56,
                        height: 56,
                        borderRadius: '16px',
                        background: status === 'success' ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: status === 'success' ? '#10B981' : '#EF4444'
                    }}>
                        {status === 'success' ? <MailX size={26} /> : <MailCheck size={26} />}
                    </div>
                    <div>
                        <h1 style={{ margin: 0, fontSize: '1.8rem' }}>
                            {status === 'success' ? 'You are unsubscribed' : 'Notification center'}
                        </h1>
                        <p style={{ margin: 0, color: 'var(--text-muted)' }}>
                            {status === 'success'
                                ? 'We removed you from all marketing drops immediately.'
                                : 'Use this page to manage future communications.'}
                        </p>
                    </div>
                </div>

                <div style={{
                    padding: '1.25rem',
                    borderRadius: '18px',
                    background: 'rgba(255,255,255,0.02)',
                    border: '1px dashed rgba(255,255,255,0.06)',
                    marginBottom: '1.5rem'
                }}>
                    <p style={{ margin: 0, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                        You can always jump back in—rewriting trading playbooks works best when you hear about new features
                        the moment they land. Use the button below to re-subscribe with the same inbox.
                    </p>
                </div>

                <button
                    type="button"
                    className="btn-primary"
                    onClick={handleResubscribe}
                    disabled={!token || resubscribing}
                    style={{ width: '100%', marginBottom: '1rem' }}
                >
                    {resubscribing ? 'Re-subscribing...' : 'Resubscribe to updates'}
                </button>

                {resubscribeMessage && (
                    <div style={{
                        padding: '0.9rem 1rem',
                        borderRadius: 'var(--radius-md)',
                        border: `1px solid ${resubscribeMessage.type === 'success' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
                        background: resubscribeMessage.type === 'success' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                        color: resubscribeMessage.type === 'success' ? '#10B981' : '#EF4444',
                        marginBottom: '1rem'
                    }}>
                        {resubscribeMessage.text}
                    </div>
                )}

                <button
                    type="button"
                    className="btn-glass"
                    onClick={() => navigate('/login')}
                    style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', width: '100%' }}
                >
                    <ArrowLeft size={18} /> Back to login
                </button>
            </motion.div>
        </div>
    );
};

export default Unsubscribe;
