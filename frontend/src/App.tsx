import { useState } from 'react'

function App() {
  const [count, setCount] = useState(0)

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Asistente de Conocimiento Corporativo
        </h1>
        <p className="text-gray-600 mb-8">
          Sistema de IA Generativa para Capacitación
        </p>
        <button
          onClick={() => setCount((count) => count + 1)}
          className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg transition-colors"
        >
          count is {count}
        </button>
        <p className="text-sm text-gray-500 mt-4">
          Frontend en desarrollo con Vite + React + TypeScript
        </p>
      </div>
    </div>
  )
}

export default App
