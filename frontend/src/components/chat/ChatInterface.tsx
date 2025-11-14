import { useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Trash2 } from 'lucide-react';
import { ChatBubble } from './ChatBubble';
import { ChatInput } from './ChatInput';
import { SourcesList, Source } from './SourcesList';
import { cn } from '@/lib/utils';
import { useChatStore } from '@/store/chatStore';

interface ChatInterfaceProps {
  onQuery: (query: string) => Promise<void>;
  isLoading?: boolean;
  onSourceClick?: (source: Source) => void;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  onQuery,
  isLoading = false,
  onSourceClick,
}) => {
  const { messages, clearConversation } = useChatStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to newest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = async (query: string) => {
    try {
      await onQuery(query);
    } catch (error) {
      console.error('Error submitting query:', error);
    }
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow-md overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b bg-gray-50">
        <h2 className="text-xl font-bold text-gray-900">Consultas IA</h2>
        {messages.length > 0 && (
          <Button
            variant="outline"
            size="sm"
            onClick={clearConversation}
            className="flex items-center gap-2"
          >
            <Trash2 className="h-4 w-4" />
            Limpiar
          </Button>
        )}
      </div>

      {/* Messages Area */}
      <div className={cn('flex-1 overflow-y-auto p-4 bg-white', messages.length === 0 && 'flex items-center justify-center')}>
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 max-w-xs">
            <p className="text-lg font-medium mb-2">¡Comienza a preguntar!</p>
            <p className="text-sm">
              Escribe tu pregunta sobre los documentos de la empresa y obtén respuestas instantáneas powered by IA.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {messages.map((msg) => (
              <div key={msg.id}>
                <ChatBubble
                  role={msg.role}
                  content={msg.content}
                  timestamp={msg.timestamp}
                  isLoading={msg.role === 'ai' && isLoading}
                />
                {msg.role === 'ai' && msg.sources && !isLoading && (
                  <SourcesList
                    sources={msg.sources}
                    onSourceClick={onSourceClick}
                  />
                )}
              </div>
            ))}
            {isLoading && (
              <div className="flex justify-center items-center gap-2 py-4">
                <div className="text-gray-600 text-sm">IA está pensando</div>
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                </div>
                <div className="text-gray-500 text-sm">~2 segundos</div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="border-t bg-gray-50 p-4">
        <ChatInput
          onSubmit={handleSubmit}
          isLoading={isLoading}
          disabled={false}
        />
      </div>
    </div>
  );
};
