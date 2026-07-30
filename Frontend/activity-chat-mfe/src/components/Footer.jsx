function Footer() {
  return (
    <footer className="bg-[#ffffff]  border-2 border-[#000000] px-8 py-6">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Left - Brand */}
        <div className="text-center md:text-left">
          <h3 className="text-2xl font-bold text-[#000000]">Chanakya</h3>
          <p className="text-sm text-[#000000]">Your AI Classroom Companion</p>
        </div>

        {/* Center - Team Credit */}
        <div className="text-center">
          <p className="text-sm text-[#000000]">
            Designed and Developed by{" "}
            <span className="font-semibold">Team Mirage</span> for ShikshaLokam
          </p>
        </div>


        {/* Right - Copyright */}
        <div className="text-center md:text-right">
          <p className="text-sm text-[#000000]">For Teachers, By Students.</p>
        </div>
      </div>
    </footer>
  );
}

export default Footer;
