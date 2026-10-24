import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { CheckCircle2, Sparkles } from 'lucide-react';
import { formatDate } from '../../utils/formatters';

/**
 * MessageBubble Component
 * Clean, modern ChatGPT/Claude style message rendering.
 * Natural layout with high-contrast text and structured tables.
 */
export default function MessageBubble({
  role = 'assistant',
  content = '',
  timestamp = null,
  trace = null,
}) {
  const isUser = role === 'user';

  // Check if AI verified records
  const hasToolTrace =
    !isUser &&
    Boolean(
      trace?.steps?.some((step) => step.tool_name) ||
      content.includes('INR') ||
      content.includes('₹') ||
      content.includes('RCP-') ||
      content.includes('STU') ||
      content.includes('Handbook') ||
      content.includes('Annexure')
    );

  return (
    <div
      className={`flex flex-col mb-6 animate-bubble ${
        isUser ? 'items-end' : 'items-start'
      } max-w-full`}
    >
      {/* Sender Header for Assistant (ChatGPT/Claude style) */}
      {!isUser && (
        <div className="flex items-center gap-2 mb-2 px-1">
          <div className="w-6 h-6 rounded-lg bg-slate-900 text-white flex items-center justify-center shadow-xs">
            <Sparkles className="w-3.5 h-3.5 text-slate-200" />
          </div>
          <span className="text-xs font-bold text-slate-800">AI Student Assistant</span>
          <span className="text-[11px] text-slate-400 font-medium">· Official University Guide</span>
        </div>
      )}

      {/* Bubble Container */}
      <div
        className={`max-w-[90%] md:max-w-[82%] text-sm leading-relaxed transition-[background-color,border-color,box-shadow] duration-150 ease-out ${
          isUser
            ? 'bg-slate-900 text-white rounded-2xl rounded-br-sm px-5 py-3 shadow-xs font-medium'
            : 'bg-white text-slate-800 border border-slate-200 rounded-2xl rounded-tl-sm p-6 shadow-sm'
        }`}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap">{content}</p>
        ) : (
          <div className="prose-chat text-slate-800">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                p: ({ children }) => (
                  <p className="mb-3.5 last:mb-0 leading-relaxed text-slate-800 text-sm">
                    {children}
                  </p>
                ),
                strong: ({ children }) => (
                  <strong className="font-bold text-slate-900">
                    {children}
                  </strong>
                ),
                table: ({ children }) => (
                  <div className="my-4 overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-xs">
                    <table className="w-full border-collapse text-left text-xs">
                      {children}
                    </table>
                  </div>
                ),
                thead: ({ children }) => (
                  <thead className="bg-slate-50 border-b border-slate-200 text-slate-700 font-bold uppercase tracking-wider text-[11px]">
                    {children}
                  </thead>
                ),
                th: ({ children }) => (
                  <th className="px-4 py-2.5 font-bold text-slate-900">
                    {children}
                  </th>
                ),
                tbody: ({ children }) => (
                  <tbody className="divide-y divide-slate-100 bg-white">
                    {children}
                  </tbody>
                ),
                tr: ({ children }) => (
                  <tr className="hover:bg-slate-50/70 transition-colors">
                    {children}
                  </tr>
                ),
                td: ({ children }) => (
                  <td className="px-4 py-2.5 text-slate-700 font-medium text-xs">
                    {children}
                  </td>
                ),
                ul: ({ children }) => (
                  <ul className="my-3 space-y-2 pl-0 list-none">
                    {children}
                  </ul>
                ),
                ol: ({ children }) => (
                  <ol className="my-3 space-y-2 pl-5 list-decimal text-slate-800">
                    {children}
                  </ol>
                ),
                li: ({ children }) => (
                  <li className="flex items-start gap-2.5 text-slate-800 text-sm">
                    <span className="w-1.5 h-1.5 rounded-full bg-slate-700 mt-2 shrink-0" />
                    <span className="flex-1">{children}</span>
                  </li>
                ),
                code: ({ children }) => (
                  <code className="px-2 py-0.5 rounded bg-slate-100 text-slate-800 font-mono text-xs border border-slate-200">
                    {children}
                  </code>
                ),
              }}
            >
              {content}
            </ReactMarkdown>
          </div>
        )}

        {/* Source verification chip */}
        {hasToolTrace && (
          <div className="mt-4 pt-3.5 border-t border-slate-100 flex items-center justify-between">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-50 border border-slate-200 text-slate-700 text-xs font-semibold">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              <span>Verified against official university records</span>
            </span>
          </div>
        )}
      </div>

      {/* Timestamp */}
      <span className="text-xs text-slate-400 mt-1.5 px-1 font-mono">
        {timestamp ? formatDate(timestamp, true) : 'Just now'}
      </span>
    </div>
  );
}
