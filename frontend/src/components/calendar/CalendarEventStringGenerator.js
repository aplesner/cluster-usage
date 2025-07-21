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
        navigator.clipboard.writeText(eventString);
        setCopied(true);
        setTimeout(() => setCopied(false), 1200);
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