import React from 'react';

/**
 * generic modal component for dialogs and confirmations.
 */
export default function Modal({ isOpen, title, children, onClose, actions }) {
  if (!isOpen) return null;

  // close on backdrop click
  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div className="modal-overlay" onClick={handleBackdropClick}>
      <div className="modal-box">
        <div className="modal-header">
          {title}
        </div>
        <div className="modal-body">
          {children}
        </div>
        <div className="modal-actions">
          {actions || (
            <button onClick={onClose} style={{background: 'transparent', border: '1px solid var(--border-color)', color: 'var(--text-main)'}}>
              Close
            </button>
          )}
        </div>
      </div>
    </div>
  );
}