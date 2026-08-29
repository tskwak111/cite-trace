import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { EvidenceFeedbackDialog } from '../src/features/feedback/EvidenceFeedbackDialog';

describe('EvidenceFeedbackDialog', () => {
    it('submits feedback with correct category and comment', () => {
        const handleSubmit = vi.fn();
        render(<EvidenceFeedbackDialog evidenceLinkId="123" onSubmit={handleSubmit} onClose={() => {}} />);

        fireEvent.change(screen.getByLabelText('Category'), { target: { value: 'source_evidence' } });
        fireEvent.change(screen.getByLabelText('Comment'), { target: { value: 'This is wrong' } });
        fireEvent.click(screen.getByText('Submit Feedback'));

        expect(handleSubmit).toHaveBeenCalledWith({
            evidenceLinkId: '123',
            category: 'source_evidence',
            comment: 'This is wrong'
        });
    });
});
