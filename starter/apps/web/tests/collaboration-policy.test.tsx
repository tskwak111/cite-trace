import React from 'react';
import { render, screen } from '@testing-library/react';
import { NoteComposer } from '../src/features/collaboration/NoteComposer';
import { ExportDialog } from '../src/features/export/ExportDialog';

describe('Collaboration & Privacy', () => {
    it('displays privacy notice in NoteComposer', () => {
        render(<NoteComposer onSubmit={() => {}} />);
        expect(screen.getByText(/Your private notes are only visible to you/)).toBeInTheDocument();
    });

    it('displays export privacy notice in ExportDialog', () => {
        render(<ExportDialog onExport={() => {}} />);
        expect(screen.getByText(/Private source text is excluded/)).toBeInTheDocument();
    });
});
