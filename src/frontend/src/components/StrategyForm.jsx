import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { X, Save, AlertCircle } from 'lucide-react';
import './StrategyForm.css';

const StrategyForm = ({ strategy, onClose, onSave }) => {
    const [formData, setFormData] = useState({
        name: '',
        description: '',
        type: 'moving_average',
        parameters: {},
        is_active: false
    });
    const [errors, setErrors] = useState({});
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        if (strategy) {
            setFormData({
                name: strategy.name || '',
                description: strategy.description || '',
                type: strategy.type || 'moving_average',
                parameters: strategy.parameters || {},
                is_active: strategy.is_active || false
            });
        }
    }, [strategy]);

    const strategyTypes = [
        { value: 'moving_average', label: 'Moving Average Crossover' },
        { value: 'mean_reversion', label: 'Mean Reversion' },
        { value: 'momentum', label: 'Momentum' },
        { value: 'rsi', label: 'RSI Strategy' }
    ];

    const handleChange = (field, value) => {
        setFormData(prev => ({ ...prev, [field]: value }));
        if (errors[field]) {
            setErrors(prev => ({ ...prev, [field]: null }));
        }
    };

    const handleParameterChange = (key, value) => {
        setFormData(prev => ({
            ...prev,
            parameters: { ...prev.parameters, [key]: value }
        }));
    };

    const validate = () => {
        const newErrors = {};

        if (!formData.name.trim()) {
            newErrors.name = 'Strategy name is required';
        }

        if (!formData.type) {
            newErrors.type = 'Strategy type is required';
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!validate()) return;

        setSaving(true);

        try {
            const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5002';
            const url = strategy
                ? `${API_URL}/api/strategies/${strategy.id}`
                : `${API_URL}/api/strategies`;

            const method = strategy ? 'PUT' : 'POST';

            const response = await fetch(url, {
                method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ...formData, user_id: 1 })
            });

            if (response.ok) {
                const data = await response.json();
                onSave(data.strategy);
                onClose();
            } else {
                const error = await response.json();
                setErrors({ submit: error.message || 'Failed to save strategy' });
            }
        } catch (error) {
            setErrors({ submit: 'Network error. Please try again.' });
        } finally {
            setSaving(false);
        }
    };

    const renderParameterFields = () => {
        switch (formData.type) {
            case 'moving_average':
                return (
                    <>
                        <div className="form-group">
                            <label>Short Window</label>
                            <input
                                type="number"
                                value={formData.parameters.short_window || 20}
                                onChange={(e) => handleParameterChange('short_window', parseInt(e.target.value))}
                                min="1"
                                max="100"
                            />
                            <span className="help-text">Fast moving average period</span>
                        </div>
                        <div className="form-group">
                            <label>Long Window</label>
                            <input
                                type="number"
                                value={formData.parameters.long_window || 50}
                                onChange={(e) => handleParameterChange('long_window', parseInt(e.target.value))}
                                min="1"
                                max="200"
                            />
                            <span className="help-text">Slow moving average period</span>
                        </div>
                    </>
                );

            case 'rsi':
                return (
                    <>
                        <div className="form-group">
                            <label>RSI Period</label>
                            <input
                                type="number"
                                value={formData.parameters.rsi_period || 14}
                                onChange={(e) => handleParameterChange('rsi_period', parseInt(e.target.value))}
                                min="2"
                                max="50"
                            />
                        </div>
                        <div className="form-group">
                            <label>Oversold Threshold</label>
                            <input
                                type="number"
                                value={formData.parameters.oversold || 30}
                                onChange={(e) => handleParameterChange('oversold', parseInt(e.target.value))}
                                min="0"
                                max="50"
                            />
                        </div>
                        <div className="form-group">
                            <label>Overbought Threshold</label>
                            <input
                                type="number"
                                value={formData.parameters.overbought || 70}
                                onChange={(e) => handleParameterChange('overbought', parseInt(e.target.value))}
                                min="50"
                                max="100"
                            />
                        </div>
                    </>
                );

            default:
                return (
                    <div className="form-group">
                        <label>Parameters (JSON)</label>
                        <textarea
                            value={JSON.stringify(formData.parameters, null, 2)}
                            onChange={(e) => {
                                try {
                                    const params = JSON.parse(e.target.value);
                                    setFormData(prev => ({ ...prev, parameters: params }));
                                } catch (err) {
                                    // Invalid JSON, ignore
                                }
                            }}
                            rows="4"
                        />
                    </div>
                );
        }
    };

    return (
        <motion.div
            className="strategy-form-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
        >
            <motion.div
                className="strategy-form-container"
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.9, opacity: 0 }}
                onClick={(e) => e.stopPropagation()}
            >
                <div className="form-header">
                    <h2>{strategy ? 'Edit Strategy' : 'Create New Strategy'}</h2>
                    <button className="btn-close" onClick={onClose}>
                        <X size={24} />
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="strategy-form">
                    {errors.submit && (
                        <div className="error-banner">
                            <AlertCircle size={20} />
                            <span>{errors.submit}</span>
                        </div>
                    )}

                    <div className="form-group">
                        <label>Strategy Name *</label>
                        <input
                            type="text"
                            value={formData.name}
                            onChange={(e) => handleChange('name', e.target.value)}
                            placeholder="e.g., My Moving Average Strategy"
                            className={errors.name ? 'error' : ''}
                        />
                        {errors.name && <span className="error-text">{errors.name}</span>}
                    </div>

                    <div className="form-group">
                        <label>Description</label>
                        <textarea
                            value={formData.description}
                            onChange={(e) => handleChange('description', e.target.value)}
                            placeholder="Describe your strategy..."
                            rows="3"
                        />
                    </div>

                    <div className="form-group">
                        <label>Strategy Type *</label>
                        <select
                            value={formData.type}
                            onChange={(e) => handleChange('type', e.target.value)}
                            className={errors.type ? 'error' : ''}
                        >
                            {strategyTypes.map(type => (
                                <option key={type.value} value={type.value}>
                                    {type.label}
                                </option>
                            ))}
                        </select>
                        {errors.type && <span className="error-text">{errors.type}</span>}
                    </div>

                    <div className="parameters-section">
                        <h3>Parameters</h3>
                        {renderParameterFields()}
                    </div>

                    <div className="form-group checkbox-group">
                        <label className="checkbox-label">
                            <input
                                type="checkbox"
                                checked={formData.is_active}
                                onChange={(e) => handleChange('is_active', e.target.checked)}
                            />
                            <span>Activate strategy immediately</span>
                        </label>
                    </div>

                    <div className="form-actions">
                        <button
                            type="button"
                            className="btn-secondary"
                            onClick={onClose}
                            disabled={saving}
                        >
                            Cancel
                        </button>
                        <motion.button
                            type="submit"
                            className="btn-primary"
                            disabled={saving}
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                        >
                            <Save size={20} />
                            {saving ? 'Saving...' : (strategy ? 'Update Strategy' : 'Create Strategy')}
                        </motion.button>
                    </div>
                </form>
            </motion.div>
        </motion.div>
    );
};

export default StrategyForm;
