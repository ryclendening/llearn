import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';
import './MathText.css';

function MathText({ text, className = '', citations = [], onCitationClick }) {
    const parts = splitCitationMarkers(String(text || ''), citations);
    const citedSourceIds = new Set(parts.filter((part) => part.type === 'citation').map((part) => part.sourceId));
    const uncitedCitations = (citations || [])
        .map((citation, index) => ({ citation, number: index + 1 }))
        .filter(({ citation }) => citation?.source_id && !citedSourceIds.has(citation.source_id));

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
            {uncitedCitations.length > 0 && (
                <span className="citation-fallbacks">
                    {uncitedCitations.map(({ citation, number }) => (
                        <button
                            key={`fallback-${citation.source_id}`}
                            type="button"
                            className="citation-superscript"
                            onClick={() => onCitationClick?.(citation)}
                            disabled={!citation?.material_id}
                            title={citationTitle(citation)}
                        >
                            {number}
                        </button>
                    ))}
                </span>
            )}
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
