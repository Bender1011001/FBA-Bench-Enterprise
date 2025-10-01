import React from 'react';

interface HelpButtonProps {
  onClick: () => void;
}

const HelpButton: React.FC<HelpButtonProps> = ({ onClick }) => {
  return (
    <button
      className="btn btn-secondary"
      onClick={onClick}
      style={{
        position: 'fixed',
        bottom: '1rem',
        right: '1rem',
        padding: '0.75rem 1rem',
        fontSize: '1rem',
        borderRadius: '50px',
        boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
        zIndex: 999,
      }}
      aria-label="Open help"
    >
      ?
    </button>
  );
};

export default HelpButton;