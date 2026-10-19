import { Routes, Route } from 'react-router'
import HomePage from './pages/Homepage'

function App() {
  return (
    <>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="*" element={<p>Not fount</p>} />
      </Routes>
    </>
  )
}

export default App;
