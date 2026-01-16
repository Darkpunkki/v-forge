import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Layout } from '../components/Layout'
import { HomeScreen } from '../screens/Home'
import { QuestionnaireScreen } from '../screens/Questionnaire'
import { PlanReviewScreen } from '../screens/PlanReview'
import { ProgressScreen } from '../screens/Progress'
import { ClarificationScreen } from '../screens/Clarification'
import { ResultScreen } from '../screens/Result'
import { ControlPanelScreen } from '../screens/ControlPanel'
import { SimulationScreen } from '../screens/Simulation'

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<HomeScreen />} />
          <Route path="questionnaire/:sessionId" element={<QuestionnaireScreen />} />
          <Route path="plan/:sessionId" element={<PlanReviewScreen />} />
          <Route path="progress/:sessionId" element={<ProgressScreen />} />
          <Route path="clarification/:sessionId" element={<ClarificationScreen />} />
          <Route path="result/:sessionId" element={<ResultScreen />} />
          <Route path="control" element={<ControlPanelScreen />} />
          <Route path="simulation" element={<SimulationScreen />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
