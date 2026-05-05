import { Routes, Route, Navigate } from "react-router-dom"
import Sidebar from "./components/layout/Sidebar"
import Dashboard from "./pages/Dashboard"
import ScreenTime from "./pages/ScreenTime"
import FocusMode from "./pages/FocusMode"
import Blocklist from "./pages/Blocklist"
import Insights from "./pages/Insights"
import Chat from "./pages/Chat"
import Profile from "./pages/Profile"
import Login from "./pages/Login"
import Register from "./pages/Register"
import { useAuth } from "./context/AuthContext"

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated } = useAuth()
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" />
}

function App() {
  const { isAuthenticated } = useAuth()

  return (
    <div className="flex min-h-screen bg-background">
      {isAuthenticated && <Sidebar />}
      <main className={`flex-1 ${isAuthenticated ? 'ml-64' : ''} p-8`}>
        <div className="max-w-7xl mx-auto">
          <Routes>
            <Route path="/login" element={!isAuthenticated ? <Login /> : <Navigate to="/" />} />
            <Route path="/register" element={!isAuthenticated ? <Register /> : <Navigate to="/" />} />
            
            <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
            <Route path="/screen-time" element={<ProtectedRoute><ScreenTime /></ProtectedRoute>} />
            <Route path="/focus-mode" element={<ProtectedRoute><FocusMode /></ProtectedRoute>} />
            <Route path="/blocklist" element={<ProtectedRoute><Blocklist /></ProtectedRoute>} />
            <Route path="/insights" element={<ProtectedRoute><Insights /></ProtectedRoute>} />
            <Route path="/chat" element={<ProtectedRoute><Chat /></ProtectedRoute>} />
            <Route path="/profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />
          </Routes>
        </div>
      </main>
      
      {/* Simplified Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none -z-10 bg-[radial-gradient(circle_at_top_right,rgba(124,58,237,0.08),transparent)]">
        <div className="absolute top-1/4 -left-20 w-96 h-96 bg-primary/5 rounded-full blur-[100px]"></div>
        <div className="absolute bottom-1/4 -right-20 w-96 h-96 bg-secondary/5 rounded-full blur-[100px]"></div>
      </div>
    </div>
  )
}

export default App
