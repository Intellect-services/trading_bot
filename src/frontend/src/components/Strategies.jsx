import React, { useState } from 'react';
import { AnimatePresence } from 'framer-motion';
import StrategyList from './StrategyList';
import StrategyForm from './StrategyForm';
import './Strategies.css';

const Strategies = () => {
    const [showForm, setShowForm] = useState(false);
    const [editingStrategy, setEditingStrategy] = useState(null);

    const handleCreateNew = () => {
        setEditingStrategy(null);
        setShowForm(true);
    };

    const handleEdit = (strategy) => {
        setEditingStrategy(strategy);
        setShowForm(true);
    };

    const handleClose = () => {
        setShowForm(false);
        setEditingStrategy(null);
    };

    const handleSave = (strategy) => {
        // Strategy saved, form will close
        console.log('Strategy saved:', strategy);
    };

    return (
        <div className="strategies-page">
            <StrategyList
                onCreateNew={handleCreateNew}
                onEdit={handleEdit}
            />

            <AnimatePresence>
                {showForm && (
                    <StrategyForm
                        strategy={editingStrategy}
                        onClose={handleClose}
                        onSave={handleSave}
                    />
                )}
            </AnimatePresence>
        </div>
    );
};

export default Strategies;
