import React from 'react';

export const ExportDialog = ({ onExport }) => {
    return (
        <div role="dialog">
            <h2>Export Analysis</h2>
            <p className="privacy-notice">Private source text is excluded from exports.</p>
            <button onClick={() => onExport('json')}>Export as JSON</button>
            <button onClick={() => onExport('markdown')}>Export as Markdown</button>
        </div>
    );
};
