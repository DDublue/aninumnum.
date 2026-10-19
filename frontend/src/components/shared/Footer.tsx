const Footer = () => {
  return (
    <>
      <footer className="relative flex flex-col bg-secondary text-secondary-foreground">
        <section className="container mx-auto my-0 border-t border-secondary-foreground/20 bg-inherit">
          <div className="flex flex-row items-center max-w-7xl gap-4 px-4 py-8">
            <p className="mt-1 flex flex-col w-full items-start justify-center">
              Copyright © 2026 David Wu
            </p>
          </div>
        </section>
      </footer>
    </>
  )
}

export default Footer;
