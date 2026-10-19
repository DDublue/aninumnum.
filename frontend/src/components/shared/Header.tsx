import { Button } from "../ui/button"

const Header = () => {
  return (
    <>
      <header className="flex items-center justify-between px-6 py-4 border-b-border bg-neutral-light">
        <h1 className="text-xl font-bold">
          aninumnum
        </h1>
        <Button>Login</Button>
      </header>
    </>
  )
}

export default Header;
