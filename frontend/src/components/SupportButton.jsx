import { MessageCircle } from 'lucide-react';

export default function SupportButton() {
  return (
    <a
      href="https://t.me/your_support_bot"
      target="_blank"
      rel="noopener noreferrer"
      className="fixed bottom-6 right-6 z-50 flex items-center gap-2 px-4 py-3 bg-gradient-to-r from-[#0088cc] to-[#00a2e8] text-white rounded-full shadow-lg shadow-[#0088cc]/30 hover:scale-105 transition-transform"
    >
      <MessageCircle className="w-5 h-5" />
      <span className="font-bold text-sm hidden sm:inline">Поддержка</span>
    </a>
  );
}
