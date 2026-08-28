import React, { useState } from 'react';

export const NoteComposer = ({ onSubmit }) => {
    const [markdown, setMarkdown] = useState('');
    const [visibility, setVisibility] = useState('private');

    return (
        <div>
            <h3>Create Note</h3>
            <p className="privacy-notice">Your private notes are only visible to you.</p>
            <textarea aria-label="Note Content" value={markdown} onChange={e => setMarkdown(e.target.value)} />
            <select aria-label="Visibility" value={visibility} onChange={e => setVisibility(e.target.value)}>
                <option value="private">Private</option>
                <option value="workspace">Workspace</option>
            </select>
            <button onClick={() => onSubmit({ markdown, visibility })}>Save Note</button>
        </div>
    );
};
