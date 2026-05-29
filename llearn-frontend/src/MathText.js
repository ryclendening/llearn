import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';
import './MathText.css';

function MathText({ text, className = '', citations = [], onCitationClick }) {
    const parts = splitCitationMarkers(String(text || ''), citations);

    return (
        <span className={`math-text ${className}`}>
            {parts.map((part, index) => (
                part.type === 'citation'
                    ? (
                        <button
                            key={`${part.sourceId}-${index}`}
                            type="button"
                            className="citation-superscript"
                            onClick={() => onCitationClick?.(part.citation)}
                            disabled={!part.citation?.material_id}
                            title={citationTitle(part.citation)}
                        >
                            {part.number}
                        </button>
                    )
                    : (
                        <ReactMarkdown
                            key={`${part.text}-${index}`}
                            remarkPlugins={[remarkMath]}
                            rehypePlugins={[rehypeKatex]}
                            components={{
                                p: ({ children }) => <span className="math-paragraph">{children}</span>,
                            }}
                        >
                            {normalizeMathDelimiters(part.text)}
                        </ReactMarkdown>
                    )
            ))}
        </span>
    );
}

function normalizeMathDelimiters(text) {
    return text
        .replace(/\\\[/g, '$$')
        .replace(/\\\]/g, '$$')
        .replace(/\\\(/g, '$')
        .replace(/\\\)/g, '$');
}

function splitCitationMarkers(text, citations) {
    const citationById = Object.fromEntries((citations || []).map((citation, index) => [
        citation.source_id,
        { citation, number: index + 1 },
    ]));
    const parts = [];
    const pattern = /\[(source_\d+)\]/g;
    let cursor = 0;
    let match;

    while ((match = pattern.exec(text)) !== null) {
        if (match.index > cursor) {
            parts.push({ type: 'text', text: text.slice(cursor, match.index) });
        }

        const citationMatch = citationById[match[1]];
        if (citationMatch) {
            parts.push({
                type: 'citation',
                sourceId: match[1],
                citation: citationMatch.citation,
                number: citationMatch.number,
            });
        } else {
            parts.push({ type: 'text', text: match[0] });
        }
        cursor = pattern.lastIndex;
    }

    if (cursor < text.length) {
        parts.push({ type: 'text', text: text.slice(cursor) });
    }

    return parts.length ? parts : [{ type: 'text', text }];
}

function citationTitle(citation) {
    if (!citation) {
        return 'Source unavailable';
    }
    const page = citation.page ? `page ${citation.page}` : 'page unknown';
    const snippet = citation.snippet ? `\n\n${citation.snippet}` : '';
    return `Open source ${page}${snippet}`;
}

export default MathText;
