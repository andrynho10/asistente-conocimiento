import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { ChatInterface } from '@/components/chat/ChatInterface';
import { useAuth } from '@/hooks/useAuth';
import { LogOut, User, ArrowLeft } from 'lucide-react';
import { queryAI } from '@/services/iaService';
import { useChatStore } from '@/store/chatStore';
import { Source } from '@/components/chat/SourcesList';

export const Chat = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { addMessage, setLoading } = useChatStore();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleQuery = async (query: string) => {
    setIsLoading(true);
    setError(null);
    setLoading(true);

    try {
      // Add user message immediately
      addMessage('user', query);

      // Call API
      const response = await queryAI(query);

      // Add AI response
      addMessage('ai', response.answer, response.sources);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error desconocido';
      setError(errorMessage);

      // Add error message to chat
      addMessage('ai', `⚠️ Error: ${errorMessage}`);
    } finally {
      setIsLoading(false);
      setLoading(false);
    }
  };

  const handleSourceClick = (source: Source) => {
    // Navigate to document detail page (can be implemented later)
    console.log('Source clicked:', source);
    // navigate(`/documents/${source.document_id}`);
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white shadow-sm border-b sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate('/dashboard')}
                className="flex items-center gap-2"
              >
                <ArrowLeft className="h-4 w-4" />
                Volver
              </Button>
              <h1 className="text-2xl font-bold text-gray-900">
                Chat con IA
              </h1>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 text-sm text-gray-700">
                <User className="h-4 w-4" />
                <span className="font-medium">{user?.role === 'admin' ? 'Admin' : 'Usuario'}</span>
              </div>
              <Button
                variant="outline"
                onClick={handleLogout}
                className="flex items-center gap-2"
              >
                <LogOut className="h-4 w-4" />
                Cerrar Sesión
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="h-full flex flex-col">
          {/* Error Message */}
          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-700 text-sm">{error}</p>
              <button
                onClick={() => setError(null)}
                className="text-red-600 text-xs underline mt-2"
              >
                Descartar
              </button>
            </div>
          )}

          {/* Chat Interface */}
          <div className="flex-1 min-h-0">
            <ChatInterface
              onQuery={handleQuery}
              isLoading={isLoading}
              onSourceClick={handleSourceClick}
            />
          </div>
        </div>
      </main>
    </div>
  );
};
