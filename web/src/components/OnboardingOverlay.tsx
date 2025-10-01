import React, { useEffect, useRef, useCallback } from 'react';

interface OnboardingOverlayProps {
  onClose: () => void;
}

const OnboardingOverlay: React.FC<OnboardingOverlayProps> = ({ onClose }) => {
  const modalRef = useRef<HTMLDivElement>(null);
  const firstButtonRef = useRef<HTMLButtonElement>(null);
  const lastButtonRef = useRef<HTMLButtonElement>(null);

  const handleDismiss = useCallback(() => {
    localStorage.setItem('fbaee_onboarding_dismissed', 'true');
    onClose();
  }, [onClose]);

  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        handleDismiss();
      }
    };

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return;

      const focusableElements = modalRef.current?.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      ) as NodeListOf<HTMLElement>;

      if (focusableElements.length <= 1) return;

      const first = focusableElements[0];
      const last = focusableElements[focusableElements.length - 1];

      if (e.shiftKey) {
        if (document.activeElement === first) {
          last.focus();
          e.preventDefault();
        }
      } else {
        if (document.activeElement === last) {
          first.focus();
          e.preventDefault();
        }
      }
    };

    if (modalRef.current) {
      firstButtonRef.current?.focus();
      document.addEventListener('keydown', handleEsc);
      document.addEventListener('keydown', handleKeyDown);
    }

    return () => {
      document.removeEventListener('keydown', handleEsc);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [handleDismiss]);

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.5)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
      }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="onboarding-heading"
    >
      <div ref={modalRef} className="card container" style={{ position: 'relative' }}>
        <button
          onClick={handleDismiss}
          style={{
            position: 'absolute',
            top: '0.5rem',
            right: '0.5rem',
            background: 'none',
            border: 'none',
            fontSize: '1.5rem',
            cursor: 'pointer',
            color: '#6c757d',
          }}
          aria-label="Close onboarding"
        >
          ×
        </button>
        <h2 id="onboarding-heading">Welcome to FBA Enterprise Sandbox</h2>
        <ul>
          <li>Quick steps:</li>
          <li>1) Configure window.API_BASE_URL in index.html</li>
          <li>2) Register or login</li>
          <li>3) Use Billing to subscribe/manage if desired</li>
        </ul>
        <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end', marginTop: '1rem' }}>
          <button
            ref={firstButtonRef}
            className="btn btn-secondary"
            onClick={handleDismiss}
          >
            Dismiss
          </button>
          <button
            ref={lastButtonRef}
            className="btn btn-primary"
            onClick={handleDismiss}
          >
            Get started
          </button>
        </div>
      </div>
    </div>
  );
};

export default OnboardingOverlay;