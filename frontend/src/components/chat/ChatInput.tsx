import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Send } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ChatInputProps {
  onSubmit: (query: string) => void;
  isLoading?: boolean;
  disabled?: boolean;
}

const MIN_CHARS = 10;
const MAX_CHARS = 500;

export const ChatInput: React.FC<ChatInputProps> = ({
  onSubmit,
  isLoading = false,
  disabled = false,
}) => {
  const [input, setInput] = useState('');
  const [error, setError] = useState<string | null>(null);

  const charCount = input.length;
  const isValid = charCount >= MIN_CHARS && charCount <= MAX_CHARS;
  const isDisabled = disabled || isLoading || !isValid;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const trimmed = input.trim();

    if (trimmed.length < MIN_CHARS) {
      setError(`Mínimo ${MIN_CHARS} caracteres requeridos`);
      return;
    }

    if (trimmed.length > MAX_CHARS) {
      setError(`Máximo ${MAX_CHARS} caracteres permitidos`);
      return;
    }

    onSubmit(trimmed);
    setInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey && !isDisabled) {
      e.preventDefault();
      handleSubmit(e as unknown as React.FormEvent);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-2">
      <div className="relative">
        <textarea
          value={input}
          onChange={(e) => {
            setInput(e.target.value);
            setError(null);
          }}
          onKeyDown={handleKeyDown}
          placeholder="Escribe tu pregunta aquí... (ej. ¿Cómo solicito vacaciones?)"
          disabled={disabled || isLoading}
          rows={3}
          className={cn(
            'w-full p-3 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500',
            'disabled:bg-gray-100 disabled:cursor-not-allowed',
            error ? 'border-red-500' : 'border-gray-300'
          )}
        />
        <div className="absolute bottom-2 right-2 text-xs text-gray-500">
          {charCount}/{MAX_CHARS}
        </div>
      </div>

      {error && <div className="text-sm text-red-600">{error}</div>}

      {charCount > 0 && charCount < MIN_CHARS && (
        <div className="text-xs text-gray-500">
          Mínimo {MIN_CHARS} caracteres requeridos ({charCount}/{MIN_CHARS})
        </div>
      )}

      <Button
        type="submit"
        disabled={isDisabled}
        className="w-full flex items-center justify-center gap-2"
      >
        {isLoading ? (
          <>
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            Enviando...
          </>
        ) : (
          <>
            <Send className="h-4 w-4" />
            Enviar
          </>
        )}
      </Button>
    </form>
  );
};
