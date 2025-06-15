import React from "react";
import { Highlight, themes } from "prism-react-renderer";
import { Button } from "./ui/button";
import { Copy, CheckCheck, Maximize2 } from "lucide-react";
import { toast } from "sonner";

interface CodeBlockProps {
  children: string;
  className?: string;
  onExpand?: () => void;
  language: string;
  showExpand?: boolean;
}

export const CodeBlock: React.FC<CodeBlockProps> = React.memo(
  ({
    children,
    className,
    onExpand,
    showExpand = false,
    language: propLanguage,
  }) => {
    console.log(propLanguage);
    const [copied, setCopied] = React.useState(false);

    // Extract language from className (format: "language-javascript")
    // Extract language from className (format: "language-javascript")
    const language =
      propLanguage || className?.replace(/language-/, "") || "typescript";

    const copyToClipboard = async () => {
      try {
        await navigator.clipboard.writeText(children);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
        toast.success("Code copied to clipboard");
      } catch (err) {
        toast.error("Failed to copy code");
      }
    };

    return (
      <div className="contain-inline-size rounded-md border-[0.5px]  relative ">
        <div className="sticky top-0 ">
          <div className="absolute right-0 flex items-center ">
            <div className="flex gap-2 bg-primary/40 rounded-sm">
              <Button variant="ghost" size="sm" onClick={copyToClipboard}>
                {copied ? (
                  <CheckCheck className="h-4 w-4" />
                ) : (
                  <Copy className="h-4 w-4" />
                )}
              </Button>
              {showExpand && onExpand && (
                <Button variant="ghost" size="sm" onClick={onExpand}>
                  <Maximize2 className="h-4 w-4" />
                </Button>
              )}
            </div>
          </div>
        </div>
        <div className="flex items-center justify-between px-4 py-2 border-b bg-muted">
          <span className="text-sm text-muted-foreground">{language}</span>
        </div>
        <Highlight
          theme={themes.vsDark}
          code={children.trim()}
          language={language}
        >
          {({ className, style, tokens, getLineProps, getTokenProps }) => (
            <pre
              className={`${className} p-4 overflow-x-auto whitespace-pre-wrap break-all`}
              style={{
                ...style,
                maxWidth: "100%",
                margin: 0,
                borderRadius: 0,
              }}
            >
              {tokens.map((line, i) => (
                <div
                  key={i}
                  {...getLineProps({ line })}
                  className="break-words"
                >
                  <span className="select-none opacity-50 mr-4">{i + 1}</span>
                  {line.map((token, key) => (
                    <span key={key} {...getTokenProps({ token })} />
                  ))}
                </div>
              ))}
            </pre>
          )}
        </Highlight>
      </div>
    );
  }
);

CodeBlock.displayName = "CodeBlock";
