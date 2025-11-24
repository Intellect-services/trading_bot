import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Plus, Play, Pause, Trash2, Edit, TrendingUp, Activity } from 'lucide-react';
import './StrategyList.css';

const StrategyList = ({ onCreateNew, onEdit }) => {
    const [strategies, setStrategies] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState('all'); // all, active, inactive

    useEffect(() => {
        fetchStrategies();
    }, []);

    const fetchStrategies = async () => {
        try {
            const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5002';
            const response = await fetch(`${API_URL}/api/strategies?user_id=1`);
            const data = await response.json();
            if (data.status === 'success') {
                setStrategies(data.strategies);
            }
        } catch (error) {
            console.error('Error fetching strategies:', error);
        } finally {
            setLoading(false);
        }
    };

    const toggleStrategy = async (strategyId, currentStatus) => {
        try {
            const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5002';
            const response = await fetch(`${API_URL}/api/strategies/${strategyId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ is_active: !currentStatus })
            });

            if (response.ok) {
                fetchStrategies();
            }
        } catch (error) {
            console.error('Error toggling strategy:', error);
        }
    };

    const deleteStrategy = async (strategyId) => {
        if (!window.confirm('Are you sure you want to delete this strategy?')) return;

        try {
            const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5002';
            const response = await fetch(`${API_URL}/api/strategies/${strategyId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                fetchStrategies();
            }
        } catch (error) {
            console.error('Error deleting strategy:', error);
        }
    };

    const filteredStrategies = strategies.filter(s => {
        if (filter === 'active') return s.is_active;
        if (filter === 'inactive') return !s.is_active;
        return true;
    });

    if (loading) {
        return (
            <div className="strategy-list-loading">
                <div className="loading-spinner"></div>
                <p>Loading strategies...</p>
            </div>
        );
    }

    return (
        <div className="strategy-list-container">
            <div className="strategy-list-header">
                <div className="header-left">
                    <h2>Trading Strategies</h2>
                    <p className="subtitle">{strategies.length} strategies configured</p>
                </div>

                <div className="header-actions">
                    <div className="filter-tabs">
                        <button
                            className={filter === 'all' ? 'active' : ''}
                            onClick={() => setFilter('all')}
                        >
                            All ({strategies.length})
                        </button>
                        <button
                            className={filter === 'active' ? 'active' : ''}
                            onClick={() => setFilter('active')}
                        >
                            Active ({strategies.filter(s => s.is_active).length})
                        </button>
                        <button
                            className={filter === 'inactive' ? 'active' : ''}
                            onClick={() => setFilter('inactive')}
                        >
                            Inactive ({strategies.filter(s => !s.is_active).length})
                        </button>
                    </div>

                    <motion.button
                        className="btn-create-strategy"
                        onClick={onCreateNew}
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                    >
                        <Plus size={20} />
                        New Strategy
                    </motion.button>
                </div>
            </div>

            <div className="strategies-grid">
                {filteredStrategies.length === 0 ? (
                    <div className="empty-state">
                        <Activity size={64} className="empty-icon" />
                        <h3>No strategies found</h3>
                        <p>Create your first trading strategy to get started</p>
                        <button className="btn-primary" onClick={onCreateNew}>
                            <Plus size={20} />
                            Create Strategy
                        </button>
                    </div>
                ) : (
                    filteredStrategies.map((strategy, index) => (
                        <motion.div
                            key={strategy.id}
                            className={`strategy-card ${strategy.is_active ? 'active' : 'inactive'}`}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: index * 0.05 }}
                        >
                            <div className="strategy-card-header">
                                <div className="strategy-info">
                                    <h3>{strategy.name}</h3>
                                    <span className="strategy-type">{strategy.type}</span>
                                </div>
                                <div className={`status-badge ${strategy.is_active ? 'active' : 'inactive'}`}>
                                    {strategy.is_active ? 'Active' : 'Inactive'}
                                </div>
                            </div>

                            <p className="strategy-description">
                                {strategy.description || 'No description provided'}
                            </p>

                            <div className="strategy-metrics">
                                <div className="metric">
                                    <TrendingUp size={16} />
                                    <span>Win Rate: --</span>
                                </div>
                                <div className="metric">
                                    <Activity size={16} />
                                    <span>Trades: --</span>
                                </div>
                            </div>

                            <div className="strategy-actions">
                                <motion.button
                                    className="btn-icon"
                                    onClick={() => toggleStrategy(strategy.id, strategy.is_active)}
                                    whileHover={{ scale: 1.1 }}
                                    whileTap={{ scale: 0.9 }}
                                    title={strategy.is_active ? 'Pause' : 'Activate'}
                                >
                                    {strategy.is_active ? <Pause size={18} /> : <Play size={18} />}
                                </motion.button>

                                <motion.button
                                    className="btn-icon"
                                    onClick={() => onEdit(strategy)}
                                    whileHover={{ scale: 1.1 }}
                                    whileTap={{ scale: 0.9 }}
                                    title="Edit"
                                >
                                    <Edit size={18} />
                                </motion.button>

                                <motion.button
                                    className="btn-icon danger"
                                    onClick={() => deleteStrategy(strategy.id)}
                                    whileHover={{ scale: 1.1 }}
                                    whileTap={{ scale: 0.9 }}
                                    title="Delete"
                                >
                                    <Trash2 size={18} />
                                </motion.button>
                            </div>
                        </motion.div>
                    ))
                )}
            </div>
        </div>
    );
};

export default StrategyList;
