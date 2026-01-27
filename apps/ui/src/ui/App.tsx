import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from '../components/Layout'
import { ControlPanelScreen } from '../screens/ControlPanel'
import { SimulationScreen } from '../screens/Simulation'

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/control" replace />} />
          <Route path="control" element={<ControlPanelScreen />} />
          <Route path="simulation" element={<SimulationScreen />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
