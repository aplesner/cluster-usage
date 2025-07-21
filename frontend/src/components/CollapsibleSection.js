import React, { useState } from 'react';
import './CollapsibleSection.css';

const CollapsibleSection = ({ title, children, defaultOpen = true }) => {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className="collapsible-section">
      <div
        className="collapsible-header"
        onClick={() => setOpen((o) => !o)}
        style={{ cursor: 'pointer', userSelect: 'none', display: 'flex', alignItems: 'center', gap: '0.5em', fontWeight: 600, fontSize: '1.2em', padding: '0.7em 1em', background: '#f5f7fa', borderBottom: '1px solid #e0e0e0', borderRadius: '8px 8px 0 0' }}
      >
        <span style={{ fontSize: '1.2em', transition: 'transform 0.2s', transform: open ? 'rotate(90deg)' : 'rotate(0deg)' }}>&#9654;</span>
        {title}
      </div>
      {open && <div className="collapsible-content" style={{ padding: '1em' }}>{children}</div>}
    </div>
  );
};

export default CollapsibleSection; 