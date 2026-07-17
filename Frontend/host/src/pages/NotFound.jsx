function NotFound() {
  return (
    <div className="relative overflow-hidden flex flex-col items-center justify-center min-h-screen bg-white px-2 sm:px-4">
      {/* faint background wavy image */}
      <img
        src="/background_alternative_wavy.jpg"
        alt=""
        aria-hidden="true"
        className="absolute inset-0 w-full h-full object-cover opacity-5 pointer-events-none z-0"
      />

      <div className="relative z-10 flex flex-col items-center justify-center">
        <img
          src="/crying__chanak.png"
          alt="Crying Chanakya"
          className="
            w-32
            sm:w-40
            md:w-56
            lg:w-[28rem]
            xl:w-[32rem]
            max-w-full
            h-auto
            mb-2 sm:mb-3
            object-contain
          "
        />
        <h1
          className="
          text-2xl
          sm:text-3xl
          md:text-5xl
          lg:text-6xl
          font-bold
          text-black
          text-center
        "
        >
          Oops! Wrong page
        </h1>
      </div>
    </div>
  );
}

export default NotFound;
