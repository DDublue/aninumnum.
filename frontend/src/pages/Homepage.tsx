import Header from '../components/shared/Header'
import Footer from '../components/shared/Footer'

const HomePage = () => {
  return (
    <>
      <body className="relative min-h-svh flex flex-col">
        <Header />
        <main className="min-h-svh flex-1 w-full bg-background">
          Hello World!
        </main>
        <Footer />
      </body>
    </>
  )
}

export default HomePage;
