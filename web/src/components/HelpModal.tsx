import React, { useEffect, useRef, useCallback } from 'react';

interface HelpModalProps {
  open: boolean;
  onClose: () => void;
  context: 'login' | 'register' | 'account' | 'billing';
}

const HelpModal: React.FC<HelpModalProps> = ({ open, onClose, context }) => {
  const modalRef = useRef<HTMLDivElement>(null);
  const firstButtonRef = useRef<HTMLButtonElement>(null);
  const lastButtonRef = useRef<HTMLButtonElement>(null);

  const handleClose = useCallback(() => {
    onClose();
  }, [onClose]);

  useEffect(() => {
    if (!open) return;

    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        handleClose();
      }
    };

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return;

      if (!modalRef.current) return;

      const focusableElements = modalRef.current.querySelectorAll(
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

    firstButtonRef.current?.focus();
    document.addEventListener('keydown', handleEsc);
    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.removeEventListener('keydown', handleEsc);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [open, handleClose]);

  if (!open) return null;

  const getContent = () => {
    const apiBase = (window as any).API_BASE_URL || 'http://127.0.0.1:8000';
    const howToGetStarted = (
      <>
        <h3 id="help-heading">How to Get Started</h3>
        <ol>
          <li>Register a new account or login with existing credentials.</li>
          <li>Backend auth endpoints: <a href="#" target="_blank" rel="noopener noreferrer">POST /auth/register</a> and <a href="#" target="_blank" rel="noopener noreferrer">POST /auth/login</a> at {apiBase}.</li>
          <li>For billing, subscribe via Stripe Checkout or manage in Customer Portal. See <a href="#" target="_blank" rel="noopener noreferrer">billing docs</a> for details.</li>
        </ol>
        <hr />
      </>
    );

    switch (context) {
      case 'login':
        return (
          <>
            {howToGetStarted}
            <h4>Login Help</h4>
            <p>Enter your email and password to sign in. Ensure your credentials are correct.</p>
            <p><strong>Common errors:</strong></p>
            <ul>
              <li>401 Invalid credentials: Check email/password.</li>
            </ul>
          </>
        );
      case 'register':
        return (
          <>
            {howToGetStarted}
            <h4>Register Help</h4>
            <p>Create a new account with a valid email and strong password.</p>
            <p><strong>Password policy:</strong> 8-128 chars, 1 lowercase, 1 uppercase, 1 digit, 1 special (!@#$%^&*()_+).</p>
            <p><strong>Common errors:</strong> 409 Duplicate email - choose another.</p>
          </>
        );
      case 'account':
        return (
          <>
            {howToGetStarted}
            <h4>Account Help</h4>
            <p>View your profile details: ID, email, creation/update dates, active status, subscription.</p>
            <p>Sign out clears access/refresh tokens from localStorage.</p>
          </>
        );
      case 'billing':
        return (
          <>
            {howToGetStarted}
            <h4>Billing Help</h4>
            <p><strong>Subscribe:</strong> Initiates Stripe Checkout for basic plan.</p>
            <p><strong>Manage Billing:</strong> Opens Stripe Customer Portal for invoices/updates.</p>
            <p>Requires STRIPE_SECRET_KEY, STRIPE_PRICE_ID_BASIC, STRIPE_WEBHOOK_SECRET in backend env.</p>
          </>
        );
      default:
        return (
          <>
            {howToGetStarted}
            <p>Additional context-specific help not available.</p>
          </>
        );
    }
  };

  return (
    <div
      ref={modalRef}
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
      aria-labelledby="help-heading"
    >
      <div className="card container" style={{ maxWidth: '500px', maxHeight: '80vh', overflowY: 'auto', position: 'relative' }}>
        <button
          ref={firstButtonRef}
          onClick={handleClose}
          className="btn btn-secondary"
          style={{
            position: 'absolute',
            top: '0.5rem',
            right: '0.5rem',
            padding: '0.25rem 0.5rem',
            fontSize: '1.25rem'
          }}
          aria-label="Close help modal"
        >
          ×
        </button>
        <div style={{ paddingTop: '2rem' }}>{getContent()}</div>
        <button
          ref={lastButtonRef}
          onClick={handleClose}
          className="btn btn-secondary"
          style={{
            marginTop: '1rem',
            width: '100%'
          }}
        >
          Close
        </button>
      </div>
    </div>
  );
};

export default HelpModal;