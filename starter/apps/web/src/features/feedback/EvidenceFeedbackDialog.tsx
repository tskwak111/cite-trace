import React, { useState } from 'react';

export type FeedbackCategory = 'source_evidence' | 'reference_resolution';

export interface FeedbackPayload {
    evidenceLinkId: string;
    category: FeedbackCategory;
    comment: string;
}

export interface EvidenceFeedbackDialogProps {
    evidenceLinkId: string;
    onSubmit: (payload: FeedbackPayload) => void;
    onClose: () => void;
}

export const EvidenceFeedbackDialog = ({ evidenceLinkId, onSubmit, onClose }: EvidenceFeedbackDialogProps) => {
    const [category, setCategory] = useState<FeedbackCategory>('source_evidence');
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
            <select aria-label="Category" value={category} onChange={e => setCategory(e.target.value as FeedbackCategory)}>
                <option value="source_evidence">Source Evidence Incorrect</option>
                <option value="reference_resolution">Wrong Reference</option>
            </select>
            <textarea aria-label="Comment" value={comment} onChange={e => setComment(e.target.value)} />
            <button onClick={handleSubmit}>Submit Feedback</button>
            <button onClick={onClose}>Cancel</button>
        </div>
    );
};
