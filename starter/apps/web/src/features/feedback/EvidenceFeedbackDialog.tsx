import React, { useState } from 'react';

export const EvidenceFeedbackDialog = ({ evidenceLinkId, onSubmit, onClose }) => {
    const [category, setCategory] = useState('source_evidence');
    const [comment, setComment] = useState('');

    const handleSubmit = () => {
        onSubmit({
            evidenceLinkId,
            category,
            comment
        });
    };

    return (
        <div role="dialog" aria-labelledby="feedback-dialog-title">
            <h2 id="feedback-dialog-title">Report Issue</h2>
            <select aria-label="Category" value={category} onChange={e => setCategory(e.target.value)}>
                <option value="source_evidence">Source Evidence Incorrect</option>
                <option value="reference_resolution">Wrong Reference</option>
            </select>
            <textarea aria-label="Comment" value={comment} onChange={e => setComment(e.target.value)} />
            <button onClick={handleSubmit}>Submit Feedback</button>
            <button onClick={onClose}>Cancel</button>
        </div>
    );
};
