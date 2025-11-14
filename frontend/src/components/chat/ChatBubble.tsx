import { ReactMarkdown } from '@/lib/markdown';
import { cn } from '@/lib/utils';

interface ChatBubbleProps {
  role: 'user' | 'ai';
  content: string;
  timestamp?: Date;
  isLoading?: boolean;
}

export const ChatBubble: React.FC<ChatBubbleProps> = ({
  role,
  content,
  timestamp,
  isLoading = false,
}) => {
  const isUser = role === 'user';

  return (
    <div
      className={cn(
        'flex w-full mb-4 animate-fade-in',
        isUser ? 'justify-end' : 'justify-start'
      )}
    >
      <div
        className={cn(
          'max-w-xs lg:max-w-md px-4 py-3 rounded-lg shadow-sm',
          isUser
            ? 'bg-blue-500 text-white rounded-br-none'
            : 'bg-gray-200 text-gray-900 rounded-bl-none'
        )}
      >
        {isLoading ? (
          <div className="space-y-2">
            <div className="h-4 bg-gray-400 rounded animate-pulse"></div>
            <div className="h-4 bg-gray-400 rounded animate-pulse w-5/6"></div>
          </div>
        ) : (
          <>
            <div className="prose prose-sm dark:prose-invert max-w-none">
              <ReactMarkdown>{content}</ReactMarkdown>
            </div>
            {timestamp && (
              <div className={cn('text-xs mt-2', isUser ? 'text-blue-100' : 'text-gray-500')}>
                {formatTime(timestamp)}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

const formatTime = (date: Date): string => {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);

  if (diffMins < 1) return 'Ahora';
  if (diffMins < 60) return `Hace ${diffMins} ${diffMins === 1 ? 'minuto' : 'minutos'}`;

  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `Hace ${diffHours} ${diffHours === 1 ? 'hora' : 'horas'}`;

  return date.toLocaleDateString('es-ES');
};
