import React, { useState, useEffect } from 'react';
import api from '../../services/api';

function CalendarEventStringGenerator() {
    const [users, setUsers] = useState([]);
    const [selectedUser, setSelectedUser] = useState('');
    const [resource, setResource] = useState('tikgpu01');
    const [num, setNum] = useState(8);
    const [isTikgpuX, setIsTikgpuX] = useState(false);
    const [comment, setComment] = useState('');
    const [copied, setCopied] = useState(false);

    useEffect(() => {
        const fetchUsers = async () => {
            try {
                const data = await api.getUsers();
                setUsers(data);
                if (data.length > 0) setSelectedUser(data[0].username);
            } catch {
                setUsers([]);
            }
        };
        fetchUsers();
    }, []);

    const resourceOptions = Array.from({ length: 10 }, (_, i) => `tikgpu${(i+1).toString().padStart(2, '0')}`);

    let resourceString = isTikgpuX ? 'tikgpuX' : resource;
    let eventString = `${selectedUser} @ ${num}x ${resourceString}`;
    if (comment.trim()) {
        eventString += ` (${comment.trim()})`;
    }

    const handleCopy = () => {
        console.log('Copy button clicked, text to copy:', eventString);
        console.log('Clipboard API available:', !!navigator.clipboard);
        console.log('Clipboard writeText available:', !!(navigator.clipboard && navigator.clipboard.writeText));
        
        // Try using the modern clipboard API first
        if (navigator.clipboard && navigator.clipboard.writeText) {
            console.log('Using modern clipboard API');
            navigator.clipboard.writeText(eventString)
                .then(() => {
                    console.log('Modern clipboard API succeeded');
                    setCopied(true);
                    setTimeout(() => setCopied(false), 1200);
                })
                .catch((error) => {
                    console.log('Modern clipboard API failed:', error);
                    // Fallback to the old method if clipboard API fails
                    fallbackCopyTextToClipboard(eventString);
                });
        } else {
            console.log('Using fallback copy method');
            // Fallback for browsers that don't support clipboard API
            fallbackCopyTextToClipboard(eventString);
        }
    };

    const fallbackCopyTextToClipboard = (text) => {
        const textArea = document.createElement('textarea');
        textArea.value = text;
        
        // Make it invisible but keep it in the DOM
        textArea.style.position = 'absolute';
        textArea.style.left = '-9999px';
        textArea.style.top = '-9999px';
        textArea.style.width = '2em';
        textArea.style.height = '2em';
        textArea.style.padding = '0';
        textArea.style.border = 'none';
        textArea.style.outline = 'none';
        textArea.style.boxShadow = 'none';
        textArea.style.background = 'transparent';
        
        document.body.appendChild(textArea);
        
        // Use setTimeout to ensure the element is properly added to DOM
        setTimeout(() => {
            textArea.focus();
            textArea.select();
            
            try {
                const successful = document.execCommand('copy');
                if (successful) {
                    setCopied(true);
                    setTimeout(() => setCopied(false), 1200);
                    console.log('Text copied successfully via fallback method');
                } else {
                    console.warn('Fallback copy command failed');
                    // Try one more time with a slight delay
                    setTimeout(() => {
                        textArea.focus();
                        textArea.select();
                        const retrySuccessful = document.execCommand('copy');
                        if (retrySuccessful) {
                            setCopied(true);
                            setTimeout(() => setCopied(false), 1200);
                            console.log('Text copied successfully on retry');
                        } else {
                            console.error('Copy failed even on retry');
                        }
                    }, 100);
                }
            } catch (err) {
                console.error('Fallback copy failed', err);
            }
            
            document.body.removeChild(textArea);
        }, 10);
    };

    return (
        <>
        <div className="calendar-event-generator" style={{ marginBottom: '1.5rem', padding: '1rem', border: '1px solid #eee', borderRadius: '8px', background: '#fafbfc' }}>
            <h4 style={{ marginBottom: '0.5rem' }}>Generate Reservation String</h4>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem', alignItems: 'center' }}>
                <div>
                    <label>User:&nbsp;</label>
                    <select value={selectedUser} onChange={e => setSelectedUser(e.target.value)}>
                        {users.map(user => (
                            <option key={user.username} value={user.username}>{user.username}</option>
                        ))}
                    </select>
                </div>
                <div>
                    <label>Resource:&nbsp;</label>
                    <select value={resource} onChange={e => setResource(e.target.value)} disabled={isTikgpuX}>
                        {resourceOptions.map(opt => (
                            <option key={opt} value={opt}>{opt}</option>
                        ))}
                    </select>
                </div>
                <div>
                    <label>Count:&nbsp;</label>
                    <input type="number" min={1} max={40} value={num} onChange={e => setNum(Number(e.target.value))} style={{ width: '4em' }} />
                </div>
                <div>
                    <label>
                        <input type="checkbox" checked={isTikgpuX} onChange={e => setIsTikgpuX(e.target.checked)} /> tikgpuX
                    </label>
                </div>
                <div>
                    <label>Comment:&nbsp;</label>
                    <input type="text" value={comment} onChange={e => setComment(e.target.value)} placeholder="Optional" style={{ width: '12em' }} />
                </div>
            </div>
            <div style={{ marginTop: '1rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <span style={{ fontFamily: 'monospace', background: '#f4f4f4', padding: '0.3em 0.7em', borderRadius: '4px' }}>{eventString}</span>
                <button onClick={handleCopy} style={{ padding: '0.2em 0.8em', fontSize: '1em', cursor: 'pointer' }}>{copied ? 'Copied!' : 'Copy'}</button>
            </div>
        </div>
        <div className="format-guide">
            <h3>Calendar Event Format Guide</h3>
            <ul>
                <li>For specific resources: <b>username @ NRx resource1, NRx resource2 (comment)</b>, Example: <code>wattenhofer @ 8x tikgpu10 (ICML deadline)</code></li>
                <li>For estimated resources: <b>username @ NRx tikgpuX</b>, Example: <code>wattenhofer @ 12x tikgpuX</code></li>
            </ul>
        </div>
        </>
    );
}

export default CalendarEventStringGenerator; 