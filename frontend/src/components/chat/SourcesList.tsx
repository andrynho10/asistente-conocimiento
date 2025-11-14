import { FileText } from 'lucide-react';
import { Button } from '@/components/ui/button';

export interface Source {
  document_id: number;
  title: string;
  relevance_score: number;
}

interface SourcesListProps {
  sources?: Source[];
  onSourceClick?: (source: Source) => void;
}

export const SourcesList: React.FC<SourcesListProps> = ({
  sources = [],
  onSourceClick,
}) => {
  if (!sources || sources.length === 0) {
    return null;
  }

  // Sort by relevance score descending
  const sortedSources = [...sources].sort(
    (a, b) => b.relevance_score - a.relevance_score
  );

  return (
    <div className="mt-3 pt-3 border-t border-gray-300">
      <div className="text-xs font-semibold text-gray-700 mb-2">
        📄 Fuentes consultadas ({sources.length}):
      </div>
      <div className="space-y-2">
        {sortedSources.map((source, idx) => (
          <div key={source.document_id} className="flex items-start gap-2">
            <span className="text-xs text-gray-500 font-medium">{idx + 1}.</span>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onSourceClick?.(source)}
              className="h-auto p-0 justify-start text-left hover:text-blue-600 flex-1"
            >
              <div className="flex items-start gap-1 w-full">
                <FileText className="h-3 w-3 mt-0.5 flex-shrink-0 text-gray-600" />
                <div className="flex-1 min-w-0">
                  <div className="text-xs text-gray-900 font-medium truncate">
                    {source.title}
                  </div>
                  <div className="text-xs text-gray-500">
                    Relevancia: {Math.round(source.relevance_score * 100)}%
                  </div>
                </div>
              </div>
            </Button>
          </div>
        ))}
      </div>
    </div>
  );
};
