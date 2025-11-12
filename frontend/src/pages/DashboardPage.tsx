import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useAuth } from '@/hooks/useAuth';
import { LogOut, User } from 'lucide-react';

export const DashboardPage = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold text-gray-900">
                Asistente de Conocimiento
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
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Card>
          <CardHeader>
            <CardTitle>Dashboard</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <p className="text-lg text-gray-700">
                Bienvenido, <span className="font-semibold">{user?.role === 'admin' ? 'Admin' : 'Usuario'}</span>
              </p>
              <p className="text-sm text-gray-500">
                Has iniciado sesión exitosamente en el sistema de Asistente de Conocimiento.
              </p>
              <div className="pt-4 border-t">
                <h3 className="text-sm font-semibold text-gray-700 mb-2">Información de sesión:</h3>
                <dl className="space-y-1 text-sm">
                  <div className="flex gap-2">
                    <dt className="text-gray-500">ID:</dt>
                    <dd className="text-gray-900 font-medium">{user?.id}</dd>
                  </div>
                  <div className="flex gap-2">
                    <dt className="text-gray-500">Rol:</dt>
                    <dd className="text-gray-900 font-medium">{user?.role}</dd>
                  </div>
                </dl>
              </div>
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  );
};
