import React from "react";
import { Highlight, themes } from "prism-react-renderer";
import { Button } from "./ui/button";
import { Copy, CheckCheck } from "lucide-react";
import { toast } from "sonner";

interface CodeBlockProps {
  children: string;
  className?: string;
}

export const CodeBlock: React.FC<CodeBlockProps> = ({
  children,
  className,
}) => {
  const [copied, setCopied] = React.useState(false);

  // Extract language from className (format: "language-javascript")
  const language = className?.replace(/language-/, "") || "typescript";

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
    <div className="relative group max-w-[calc(100vw-2rem)] md:max-w-[calc(100vw-4rem)]">
      <Button
        variant="ghost"
        size="sm"
        className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity"
        onClick={copyToClipboard}
      >
        {copied ? (
          <CheckCheck className="h-4 w-4" />
        ) : (
          <Copy className="h-4 w-4" />
        )}
      </Button>
      <Highlight
        theme={themes.vsDark}
        code={children.trim()}
        language={language}
      >
        {({ className, style, tokens, getLineProps, getTokenProps }) => (
          <pre
            className={`${className} p-4 rounded-lg overflow-x-auto whitespace-pre-wrap break-all`}
            style={{
              ...style,
              maxWidth: "100%",
            }}
          >
            {tokens.map((line, i) => (
              <div key={i} {...getLineProps({ line })} className="break-words">
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
};
