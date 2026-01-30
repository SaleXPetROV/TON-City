import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  GraduationCap, ChevronRight, ChevronLeft, MapPin, Building2,
  Coins, Package, Link2, TrendingUp, CheckCircle2, Play
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import Sidebar from '@/components/Sidebar';

const TUTORIAL_STEPS = [
  {
    title: 'Добро пожаловать в TON City Builder!',
    icon: GraduationCap,
    color: 'text-cyber-cyan',
    content: `TON City Builder — это экономическая стратегия на блокчейне TON, где вы можете:
    
• Покупать участки земли в разных городах
• Строить и развивать бизнесы
• Торговать ресурсами с другими игроками
• Зарабатывать настоящую криптовалюту TON`,
    tip: 'Ваш прогресс и активы хранятся в блокчейне — они действительно ваши!'
  },
  {
    title: 'Шаг 1: Покупка земли',
    icon: MapPin,
    color: 'text-amber-400',
    content: `Первый шаг — купить участок земли в одном из городов.

• Откройте карту городов
• Выберите город (цены зависят от зоны)
• Центр дороже, но даёт больше дохода
• Кликните на свободный участок для покупки`,
    tip: 'Новичкам рекомендуем начать с окраин — там дешевле!'
  },
  {
    title: 'Шаг 2: Строительство бизнеса',
    icon: Building2,
    color: 'text-purple-400',
    content: `После покупки земли постройте бизнес:

• Ферма — производит урожай
• Завод — производит товары из материалов  
• Магазин — продаёт товары
• Ресторан — использует урожай
• Банк — пассивный доход

Каждый бизнес имеет свои особенности и требования.`,
    tip: 'Связывайте бизнесы друг с другом для увеличения дохода!'
  },
  {
    title: 'Шаг 3: Производство и торговля',
    icon: Package,
    color: 'text-green-400',
    content: `Ваши бизнесы производят ресурсы:

• Ресурсы можно продавать на маркетплейсе
• Цену устанавливаете вы сами
• Другие игроки могут покупать ваши ресурсы
• С продаж взимается подоходный налог`,
    tip: 'Следите за ценами на маркете — выгодно покупать дёшево и продавать дорого!'
  },
  {
    title: 'Шаг 4: Связи между бизнесами',
    icon: Link2,
    color: 'text-blue-400',
    content: `Связи увеличивают доход ваших бизнесов:

• Соседние бизнесы получают бонус
• Завод рядом с карьером работает эффективнее
• Магазин рядом с заводом продаёт больше
• Чем больше связей — тем больше доход`,
    tip: 'Планируйте расположение бизнесов заранее!'
  },
  {
    title: 'Шаг 5: Сбор дохода',
    icon: Coins,
    color: 'text-yellow-400',
    content: `Ваши бизнесы генерируют доход:

• Доход накапливается со временем
• Собирайте вручную или настройте автосбор
• С дохода взимается подоходный налог
• Чем выше уровень бизнеса — тем больше доход`,
    tip: 'Собирайте доход регулярно, чтобы не терять прибыль!'
  },
  {
    title: 'Шаг 6: Развитие и рост',
    icon: TrendingUp,
    color: 'text-red-400',
    content: `Развивайте свою империю:

• Повышайте уровень бизнесов
• Покупайте больше земли
• Торгуйте на маркетплейсе
• Поднимайтесь в рейтинге игроков
• Выводите заработанные TON на кошелёк`,
    tip: 'Топ игроки получают особые бонусы и статусы!'
  }
];

export default function TutorialPage({ user }) {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(0);

  const step = TUTORIAL_STEPS[currentStep];
  const Icon = step.icon;

  return (
    <div className="flex h-screen bg-void">
      <Sidebar user={user} />
      
      <div className="flex-1 overflow-hidden">
        <ScrollArea className="h-full">
          <div className="p-6 max-w-3xl mx-auto">
            {/* Header */}
            <div className="text-center mb-8">
              <h1 className="font-unbounded text-2xl font-bold text-white flex items-center justify-center gap-3 mb-2">
                <GraduationCap className="w-8 h-8 text-cyber-cyan" />
                ОБУЧЕНИЕ
              </h1>
              <p className="text-text-muted">Узнайте как играть в TON City Builder</p>
            </div>

            {/* Progress */}
            <div className="flex gap-2 mb-8">
              {TUTORIAL_STEPS.map((_, idx) => (
                <div 
                  key={idx}
                  onClick={() => setCurrentStep(idx)}
                  className={`flex-1 h-2 rounded-full cursor-pointer transition-all ${
                    idx === currentStep ? 'bg-cyber-cyan' : idx < currentStep ? 'bg-cyber-cyan/50' : 'bg-white/10'
                  }`}
                />
              ))}
            </div>

            {/* Step Content */}
            <motion.div
              key={currentStep}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
            >
              <Card className="glass-panel border-white/10 mb-6">
                <CardContent className="p-8">
                  <div className="flex items-center gap-4 mb-6">
                    <div className={`w-16 h-16 rounded-2xl bg-white/5 flex items-center justify-center ${step.color}`}>
                      <Icon className="w-8 h-8" />
                    </div>
                    <div>
                      <div className="text-xs text-text-muted mb-1">Шаг {currentStep + 1} из {TUTORIAL_STEPS.length}</div>
                      <h2 className="text-xl font-bold text-white">{step.title}</h2>
                    </div>
                  </div>

                  <div className="text-text-muted whitespace-pre-line mb-6 leading-relaxed">
                    {step.content}
                  </div>

                  <div className="p-4 bg-cyber-cyan/10 border border-cyber-cyan/20 rounded-xl flex items-start gap-3">
                    <CheckCircle2 className="w-5 h-5 text-cyber-cyan flex-shrink-0 mt-0.5" />
                    <div>
                      <div className="text-xs text-cyber-cyan mb-1 font-bold">СОВЕТ</div>
                      <div className="text-sm text-white">{step.tip}</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>

            {/* Navigation */}
            <div className="flex justify-between">
              <Button
                onClick={() => setCurrentStep(Math.max(0, currentStep - 1))}
                variant="outline"
                className="border-white/10"
                disabled={currentStep === 0}
              >
                <ChevronLeft className="w-4 h-4 mr-2" />
                Назад
              </Button>

              {currentStep < TUTORIAL_STEPS.length - 1 ? (
                <Button
                  onClick={() => setCurrentStep(currentStep + 1)}
                  className="bg-cyber-cyan text-black"
                >
                  Далее
                  <ChevronRight className="w-4 h-4 ml-2" />
                </Button>
              ) : (
                <Button
                  onClick={() => navigate('/map')}
                  className="bg-green-600 hover:bg-green-700"
                >
                  <Play className="w-4 h-4 mr-2" />
                  Начать играть
                </Button>
              )}
            </div>
          </div>
        </ScrollArea>
      </div>
    </div>
  );
}
