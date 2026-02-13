import React, { useState } from 'react';
import './MessageHistory.css';

function MessageHistory({ messages, isOpen, onClose, onClearHistory }) {
    const [showConfirmDialog, setShowConfirmDialog] = useState(false);

    const formatMessage = (text) => {
        const lines = text.split('\n');
        let formatted = [];
        let shlokaLines = [];

        lines.forEach((line, index) => {
            if (line.match(/[।॥]/)) {
                shlokaLines.push(line);
            } else {
                if (shlokaLines.length > 0) {
                    formatted.push(
                        <div key={`shloka-${index}`} className="shloka">
                            {shlokaLines.map((sl, i) => (
                                <div key={i}>{sl}</div>
                            ))}
                        </div>
                    );
                    shlokaLines = [];
                }
                if (line.trim()) {
                    formatted.push(<p key={index}>{line}</p>);
                }
            }
        });

        if (shlokaLines.length > 0) {
            formatted.push(
                <div key="shloka-end" className="shloka">
                    {shlokaLines.map((sl, i) => (
                        <div key={i}>{sl}</div>
                    ))}
                </div>
            );
        }

        return formatted;
    };

    const handleClearHistory = () => {
        onClearHistory();
        setShowConfirmDialog(false);
    };

    return (
        <>
            {/* Overlay */}
            {isOpen && <div className="history-overlay" onClick={onClose}></div>}

            {/* Sidebar */}
            <div className={`message-history ${isOpen ? 'open' : ''}`}>
                <div className="history-header">
                    <h2>Divine Dialogue</h2>
                    <div className="header-actions">
                        {messages.length > 0 && (
                            <button
                                className="clear-history-button"
                                onClick={() => setShowConfirmDialog(true)}
                                title="Clear history"
                            >
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2" strokeLinecap="round" strokeLinejoin="round" />
                                </svg>
                            </button>
                        )}
                        <button className="close-button" onClick={onClose}>
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                <path d="M18 6L6 18M6 6l12 12" strokeWidth="2" strokeLinecap="round" />
                            </svg>
                        </button>
                    </div>
                </div>

                <div className="history-content">
                    {messages.length === 0 ? (
                        <p className="empty-state">Your journey has just begun...</p>
                    ) : (
                        messages.map((message) => (
                            <div key={message.id} className={`history-message ${message.type}`}>
                                <div className="message-header">
                                    <span className="message-author">
                                        {message.type === 'krishna' ? '🪈 Krishna' : '👤 You'}
                                    </span>
                                    <span className="message-time">
                                        {message.timestamp.toLocaleTimeString('en-US', {
                                            hour: '2-digit',
                                            minute: '2-digit'
                                        })}
                                    </span>
                                </div>
                                <div className="message-body">
                                    {message.type === 'krishna' ? (
                                        formatMessage(message.text)
                                    ) : (
                                        <p>{message.text}</p>
                                    )}
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>

            {/* Confirmation Dialog */}
            {showConfirmDialog && (
                <div className="confirm-overlay" onClick={() => setShowConfirmDialog(false)}>
                    <div className="confirm-dialog" onClick={(e) => e.stopPropagation()}>
                        <div className="confirm-icon">
                            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" strokeLinecap="round" strokeLinejoin="round" />
                            </svg>
                        </div>
                        <h3>Clear Chat History?</h3>
                        <p>This will permanently delete all your conversations. This action cannot be undone.</p>
                        <div className="confirm-actions">
                            <button className="btn-cancel" onClick={() => setShowConfirmDialog(false)}>
                                Cancel
                            </button>
                            <button className="btn-confirm" onClick={handleClearHistory}>
                                Clear History
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
}

export default React.memo(MessageHistory);
