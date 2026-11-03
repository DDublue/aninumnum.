import Header from '../components/shared/Header'
import Footer from '../components/shared/Footer'
import { Outlet } from 'react-router'

const MainLayout = () => (
  <div className="min-h-svh flex flex-col">
    <Header />
    <main className="flex-1 max-w-7xl mx-auto w-full px-4">
      <Outlet />
    </main>
    <Footer />
  </div>
)

export default MainLayout;
