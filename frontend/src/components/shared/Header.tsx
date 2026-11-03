import { Link } from "react-router"
import { buttonVariants } from "../ui/button"

const Header = () => {
  return (
    <header className="border-b bg-neutral-light border-secondary-foreground/20">
      <div className="flex items-center justify-between max-w-7xl mx-auto px-4 py-4">
        <Link to="/" className="text-xl font-bold">aninumnum</Link>
        <a href="/api/auth/login" className={buttonVariants({ variant: "spotify" })}>Login</a>
      </div>
    </header>
  )
}

export default Header;
