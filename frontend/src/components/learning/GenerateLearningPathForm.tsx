/**
 * GenerateLearningPathForm Component
 * Story 4.4: Form to generate a new learning path
 * Collects topic and user level, shows loading state and errors
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card } from '../ui/card';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Button } from '../ui/button';
import { UserLevel } from '../../types/learning';

interface GenerateLearningPathFormProps {
  onSuccess?: (pathId: number) => void;
}

export const GenerateLearningPathForm: React.FC<GenerateLearningPathFormProps> = ({
  onSuccess,
}) => {
  const navigate = useNavigate();
  const [topic, setTopic] = useState('');
  const [userLevel, setUserLevel] = useState<UserLevel>('intermediate');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMessage(null);

    // Validate inputs
    if (!topic.trim()) {
      setError('El tema es requerido');
      return;
    }

    if (topic.trim().length < 5) {
      setError('El tema debe tener al menos 5 caracteres');
      return;
    }

    try {
      setIsLoading(true);

      const token = localStorage.getItem('auth_token');
      if (!token) {
        setError('No estás autenticado');
        return;
      }

      const response = await fetch('/api/ia/generate/learning-path', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          topic: topic.trim(),
          user_level: userLevel,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        // Handle specific error message from backend
        if (data.detail) {
          setError(data.detail);
        } else {
          setError('Error al generar la ruta de aprendizaje. Intenta nuevamente.');
        }
        return;
      }

      setSuccessMessage(`¡Ruta de aprendizaje generada exitosamente!`);
      const pathId = data.learning_path_id;

      // Clear form
      setTopic('');
      setUserLevel('intermediate');

      // Redirect after a short delay
      setTimeout(() => {
        if (onSuccess) {
          onSuccess(pathId);
        } else {
          navigate(`/learning-path/${pathId}`);
        }
      }, 1500);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Error de conexión. Intenta nuevamente.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card className="p-8 max-w-md w-full mx-auto">
      <div className="space-y-6">
        <div className="text-center space-y-2">
          <h2 className="text-2xl font-bold text-gray-900">
            Generar Ruta de Aprendizaje
          </h2>
          <p className="text-sm text-gray-600">
            Indica un tema y tu nivel para recibir una ruta personalizada
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Topic Input */}
          <div className="space-y-2">
            <Label htmlFor="topic" className="text-gray-700">
              Tema de aprendizaje
            </Label>
            <Input
              id="topic"
              type="text"
              placeholder="Ej: procedimientos de reembolsos"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              disabled={isLoading}
              className="w-full"
              minLength={5}
              maxLength={200}
            />
            <p className="text-xs text-gray-500">
              Mínimo 5 caracteres, máximo 200
            </p>
          </div>

          {/* User Level Select */}
          <div className="space-y-2">
            <Label htmlFor="userLevel" className="text-gray-700">
              Mi nivel
            </Label>
            <select
              id="userLevel"
              value={userLevel}
              onChange={(e) => setUserLevel(e.target.value as UserLevel)}
              disabled={isLoading}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
            >
              <option value="beginner">Principiante</option>
              <option value="intermediate">Intermedio</option>
              <option value="advanced">Avanzado</option>
            </select>
            <p className="text-xs text-gray-500">
              Tu nivel afectará el contenido sugerido
            </p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          {/* Success Message */}
          {successMessage && (
            <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
              <p className="text-sm text-green-700">{successMessage}</p>
            </div>
          )}

          {/* Submit Button */}
          <Button
            type="submit"
            disabled={isLoading || topic.trim().length < 5}
            className="w-full py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-medium rounded-lg transition-colors"
          >
            {isLoading ? (
              <span className="flex items-center justify-center gap-2">
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Generando...
              </span>
            ) : (
              'Generar Ruta'
            )}
          </Button>
        </form>
      </div>
    </Card>
  );
};
