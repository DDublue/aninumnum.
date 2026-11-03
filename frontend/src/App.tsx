import { Routes, Route } from 'react-router'
import HomePage from './pages/Homepage'
import Layout from './layouts/MainLayout'

function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<HomePage />} />
        <Route path="*" element={<p>Not found</p>} />
      </Route>
    </Routes>
  )
}

export default App;
