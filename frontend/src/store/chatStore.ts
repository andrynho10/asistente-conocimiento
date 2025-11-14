import { create } from 'zustand';
import { Source } from '@/components/chat/SourcesList';

export interface ChatMessage {
  id: string;
  role: 'user' | 'ai';
  content: string;
  sources?: Source[];
  timestamp: Date;
}

export interface ChatStore {
  messages: ChatMessage[];
  isLoading: boolean;
  addMessage: (role: 'user' | 'ai', content: string, sources?: Source[]) => void;
  clearConversation: () => void;
  setLoading: (loading: boolean) => void;
  removeMessage: (id: string) => void;
}

export const useChatStore = create<ChatStore>((set) => ({
  messages: [],
  isLoading: false,

  addMessage: (role, content, sources) =>
    set((state) => ({
      messages: [
        ...state.messages,
        {
          id: `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
          role,
          content,
          sources,
          timestamp: new Date(),
        },
      ],
    })),

  clearConversation: () => set({ messages: [] }),

  setLoading: (loading) => set({ isLoading: loading }),

  removeMessage: (id) =>
    set((state) => ({
      messages: state.messages.filter((msg) => msg.id !== id),
    })),
}));
