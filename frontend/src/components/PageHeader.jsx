/**
 * PageHeader component - renders title with space for mobile burger menu
 * The burger button itself is in MobileNav (fixed position)
 * Usage: <PageHeader icon={<Building2 />} title="МОИ БИЗНЕСЫ" rightContent={...} />
 */
export default function PageHeader({ icon, title, rightContent, className = '' }) {
  return (
    <div className={`flex items-center justify-between gap-3 ${className}`}>
      <div className="flex items-center gap-2">
        {/* Space for burger button on mobile (44px ~ w-10 + left-3 + gap) */}
        <div className="lg:hidden w-11 flex-shrink-0" />
        <h1 className="text-lg lg:text-2xl font-bold text-white flex items-center gap-2 font-unbounded uppercase tracking-tight">
          {icon}
          {title}
        </h1>
      </div>
      {rightContent && <div className="flex items-center gap-2 flex-shrink-0">{rightContent}</div>}
    </div>
  );
}
