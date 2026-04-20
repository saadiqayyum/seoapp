"use client";

import { useMemo } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface MarkdownRendererProps {
  content: string;
}

export function MarkdownRenderer({ content }: MarkdownRendererProps) {
  const toc = useMemo(() => {
    const headings: { level: number; text: string; id: string }[] = [];
    const lines = content.split("\n");
    for (const line of lines) {
      const match = line.match(/^(#{1,3})\s+(.+)/);
      if (match) {
        const level = match[1].length;
        const text = match[2].replace(/[*_`]/g, "");
        const id = text
          .toLowerCase()
          .replace(/[^\w\s-]/g, "")
          .replace(/\s+/g, "-");
        headings.push({ level, text, id });
      }
    }
    return headings;
  }, [content]);

  return (
    <div className="flex gap-8">
      {/* Table of Contents */}
      {toc.length > 3 && (
        <nav className="hidden xl:block w-56 shrink-0 sticky top-20 self-start max-h-[calc(100vh-120px)] overflow-y-auto">
          <p className="mb-3 text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
            On this page
          </p>
          <div className="space-y-1 border-l">
            {toc.map((heading, i) => (
              <a
                key={i}
                href={`#${heading.id}`}
                className={`block text-xs transition-colors hover:text-foreground ${
                  heading.level === 1
                    ? "pl-3 font-semibold text-foreground/80"
                    : heading.level === 2
                      ? "pl-5 text-muted-foreground"
                      : "pl-7 text-muted-foreground/70"
                }`}
              >
                {heading.text}
              </a>
            ))}
          </div>
        </nav>
      )}

      {/* Content */}
      <div className="min-w-0 flex-1 prose prose-slate dark:prose-invert max-w-none prose-headings:scroll-mt-20 prose-h1:text-2xl prose-h1:border-b prose-h1:pb-3 prose-h1:mb-6 prose-h2:text-xl prose-h3:text-lg prose-table:text-sm prose-a:text-primary prose-strong:text-foreground">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            h1: ({ children, ...props }) => {
              const text = String(children);
              const id = text
                .toLowerCase()
                .replace(/[^\w\s-]/g, "")
                .replace(/\s+/g, "-");
              return (
                <h1 id={id} {...props}>
                  {children}
                </h1>
              );
            },
            h2: ({ children, ...props }) => {
              const text = String(children);
              const id = text
                .toLowerCase()
                .replace(/[^\w\s-]/g, "")
                .replace(/\s+/g, "-");
              return (
                <h2 id={id} {...props}>
                  {children}
                </h2>
              );
            },
            h3: ({ children, ...props }) => {
              const text = String(children);
              const id = text
                .toLowerCase()
                .replace(/[^\w\s-]/g, "")
                .replace(/\s+/g, "-");
              return (
                <h3 id={id} {...props}>
                  {children}
                </h3>
              );
            },
          }}
        >
          {content}
        </ReactMarkdown>
      </div>
    </div>
  );
}
