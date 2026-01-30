import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { TonConnectButton, useTonWallet } from '@tonconnect/ui-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Building2, ArrowLeft, Globe, UserCircle, Mail, Lock, Chrome, CheckCircle2 } from 'lucide-react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useTranslation, languages } from '@/lib/translations';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';

// Load Google Identity Services
const loadGoogleScript = () => {
  return new Promise((resolve) => {
    if (window.google) {
      resolve(window.google);
      return;
    }
    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    script.onload = () => resolve(window.google);
    document.head.appendChild(script);
  });
};

export default function AuthPage({ setUser, onAuthSuccess }) {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const wallet = useTonWallet();
  const mode = searchParams.get('mode');
  
  const [lang, setLang] = useState(localStorage.getItem('ton_city_lang') || 'ru');
  const { t } = useTranslation(lang);
  const [isVerifying, setIsVerifying] = useState(false);

  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  
  const [showUsernameStep, setShowUsernameStep] = useState(false);
  const [googleLoaded, setGoogleLoaded] = useState(false);

  const finishAuth = async (data) => {
    localStorage.setItem('token', data.token);
    if (data.user) {
      setUser(data.user);
    }
    toast.success(lang === 'ru' ? 'Вход выполнен!' : 'Logged in!');
    
    // Вызываем checkAuth из App.js для обновления глобального состояния
    if (onAuthSuccess) {
      await onAuthSuccess();
    }
    
    // Переходим на главную после обновления состояния
    navigate('/');
  };

  // Load Google OAuth script
  useEffect(() => {
    loadGoogleScript().then(() => {
      setGoogleLoaded(true);
    });
  }, []);

  // Initialize Google Sign In button
  useEffect(() => {
    if (googleLoaded && window.google && !showUsernameStep) {
      try {
        window.google.accounts.id.initialize({
          client_id: 'YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com', // Will be configured by user
          callback: handleGoogleCallback,
        });
      } catch (e) {
        console.error('Google Sign In init error:', e);
      }
    }
  }, [googleLoaded, showUsernameStep]);

  const handleGoogleCallback = async (response) => {
    try {
      setIsVerifying(true);
      const res = await fetch('/api/auth/google', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ credential: response.credential })
      });
  
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail);
  
      finishAuth(data);
    } catch (e) {
      toast.error(e.message || 'Google auth failed');
    } finally {
      setIsVerifying(false);
    }
  };

  const handleGoogleSignIn = () => {
    if (window.google) {
      window.google.accounts.id.prompt();
    } else {
      toast.error('Google Sign In not loaded');
    }
  };

  const handleEmailAuth = async () => {
    try {
      setIsVerifying(true);
      
      // Validation
      if (mode === 'register' && !username.trim()) {
        toast.error(lang === 'ru' ? 'Введите username' : 'Enter username');
        setIsVerifying(false);
        return;
      }
      if (!email.trim()) {
        toast.error(lang === 'ru' ? 'Введите email или username' : 'Enter email or username');
        setIsVerifying(false);
        return;
      }
      if (!password.trim()) {
        toast.error(lang === 'ru' ? 'Введите пароль' : 'Enter password');
        setIsVerifying(false);
        return;
      }

      const res = await fetch(
        mode === 'register' ? '/api/auth/register' : '/api/auth/login',
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password, username })
        }
      );
  
      // Читаем текст ответа и парсим как JSON
      const responseText = await res.text();
      let data = null;
      try {
        data = JSON.parse(responseText);
      } catch (jsonErr) {
        console.error("JSON parse error:", jsonErr, "Response:", responseText);
      }
      
      if (!res.ok) {
        // Показываем ошибку от сервера
        const errorMsg = data?.detail || data?.message || (lang === 'ru' ? 'Неверные данные для входа' : 'Invalid credentials');
        toast.error(errorMsg);
        setIsVerifying(false);
        return;
      }
  
      if (!data) {
        toast.error(lang === 'ru' ? 'Ошибка сервера' : 'Server error');
        setIsVerifying(false);
        return;
      }

      await finishAuth(data);
    } catch (e) {
      console.error("Email auth error:", e);
      // Показываем понятное сообщение об ошибке
      if (e.message === 'Failed to fetch') {
        toast.error(lang === 'ru' ? 'Ошибка соединения с сервером' : 'Server connection error');
      } else if (e.message?.includes('body stream') || e.message?.includes('already read')) {
        // Техническая ошибка - показываем общее сообщение
        toast.error(lang === 'ru' ? 'Неверные данные для входа' : 'Invalid credentials');
      } else {
        toast.error(lang === 'ru' ? 'Ошибка авторизации' : 'Auth failed');
      }
    } finally {
      setIsVerifying(false);
    }
  };
  

  const changeLang = (newLang) => {
    setLang(newLang);
    localStorage.setItem('ton_city_lang', newLang);
  };

  const title = showUsernameStep 
    ? (lang === 'ru' ? 'Завершение регистрации' : 'Complete Registration')
    : (mode === 'register' ? t('registerTitle') : t('loginTitle'));

  useEffect(() => {
    const verifyWallet = async () => {
      if (wallet?.account?.address && !isVerifying && !showUsernameStep) {
        setIsVerifying(true);
        try {
          const response = await fetch('/api/auth/verify-wallet', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                address: wallet.account.address,
                language: lang,
                username: username,
                email: email,      
                password: password 
              })
          });

          const data = await response.json();

          if (!response.ok) {
            throw new Error(data.detail || 'Auth failed');
          }

          if (data.status === 'need_username') {
            setShowUsernameStep(true);
            toast.info(lang === 'ru' ? "Придумайте никнейм для вашего города" : "Create a username for your city");
          } else if (data.token) {
            // Используем finishAuth для правильной обработки
            finishAuth(data);
          }
        } catch (error) {
          console.error("Auth error:", error);
          toast.error(error.message === 'Failed to fetch' ? "Server Error" : error.message);
        } finally {
          setIsVerifying(false);
        }
      }
    };

    verifyWallet();
  }, [wallet?.account?.address, lang, navigate]);

  const handleFinalRegister = async () => {
    if (!username.trim()) {
      toast.error(lang === 'ru' ? "Введите никнейм" : "Enter username");
      return;
    }

    setIsVerifying(true);
    try {
      const response = await fetch('/api/auth/verify-wallet', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          address: wallet.account.address,
          language: lang,
          username: username.trim(),
          email: email,
          password: password
        })
      });

      const data = await response.json();

      if (response.ok && data.token) {
        // Используем finishAuth для корректной обработки
        finishAuth(data);
      } else {
        toast.error(data.detail || "Error");
      }
    } catch (e) {
      console.error("Registration error:", e);
      toast.error("Registration failed");
    } finally {
      setIsVerifying(false);
    }
  };

  return (
    <div className="min-h-screen bg-void flex items-center justify-center p-4 relative font-rajdhani">
      <div className="absolute top-6 right-6 z-20">
        <Select value={lang} onValueChange={changeLang}>
          <SelectTrigger className="w-36 bg-panel/50 border-grid-border text-white border-white/10">
            <Globe className="w-4 h-4 mr-2 text-cyber-cyan" />
            <SelectValue>
              {languages.find(l => l.code === lang)?.flag} {languages.find(l => l.code === lang)?.name}
            </SelectValue>
          </SelectTrigger>
          <SelectContent className="bg-panel border-white/10 text-white">
            {languages.map(language => (
              <SelectItem key={language.code} value={language.code}>
                <span className="flex items-center gap-2">
                  <span>{language.flag}</span>
                  <span>{language.name}</span>
                </span>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-panel p-8 rounded-3xl w-full max-w-md border border-white/10 text-center relative shadow-2xl"
      >
        <button 
          onClick={() => showUsernameStep ? setShowUsernameStep(false) : navigate('/')} 
          className="absolute top-6 left-6 text-text-muted hover:text-white transition-colors"
        >
          <ArrowLeft className="w-6 h-6" />
        </button>
        
        <div className="w-16 h-16 bg-gradient-to-br from-cyber-cyan to-neon-purple rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-lg shadow-cyber-cyan/20">
          <Building2 className="text-black w-10 h-10" />
        </div>

        <h1 className="font-unbounded text-xl font-bold text-white mb-8 tracking-tighter uppercase">
          {title}
        </h1>

        <div className="space-y-4">
          <AnimatePresence mode="wait">
            {showUsernameStep ? (
              <motion.div 
                key="username-step"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="space-y-4"
              >
                <div className="p-4 bg-cyber-cyan/10 border border-cyber-cyan/20 rounded-xl mb-4">
                  <p className="text-cyber-cyan text-xs uppercase tracking-widest flex items-center justify-center">
                    <CheckCircle2 className="w-4 h-4 mr-2" /> 
                    {lang === 'ru' ? 'Кошелек подключен' : 'Wallet Connected'}
                  </p>
                  <p className="text-white/40 text-[10px] mt-1 truncate">
                    {wallet?.account?.address}
                  </p>
                </div>

                <div className="relative text-left">
                  <UserCircle className="absolute left-3 top-3.5 w-5 h-5 text-cyber-cyan" />
                  <input 
                    placeholder={lang === 'ru' ? "Придумайте никнейм" : "Enter Username"}
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    autoFocus
                    className="w-full bg-white/5 border border-cyber-cyan/50 p-3 pl-10 rounded-xl text-white outline-none shadow-[0_0_15px_rgba(0,255,243,0.05)] focus:border-cyber-cyan transition-all"
                  />
                </div>

                <Button 
                  onClick={handleFinalRegister}
                  disabled={isVerifying}
                  className="w-full bg-cyber-cyan text-black font-bold py-6 hover:brightness-110 transition-all uppercase tracking-widest shadow-lg shadow-cyber-cyan/20"
                >
                  {isVerifying ? (lang === 'ru' ? 'Создание...' : 'Creating...') : (lang === 'ru' ? 'Начать игру' : 'Start Game')}
                </Button>
              </motion.div>
            ) : (
              <motion.div 
                key="login-step"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="space-y-4"
              >
                {mode === 'register' && (
                  <div className="relative text-left">
                    <UserCircle className="absolute left-3 top-3.5 w-5 h-5 text-cyber-cyan" />
                    <input 
                      placeholder={lang === 'ru' ? 'Придумайте никнейм' : 'Choose Username'}
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      className="w-full bg-white/5 border border-white/10 p-3 pl-10 rounded-xl text-white outline-none focus:border-cyber-cyan transition-all placeholder:text-white/20"
                    />
                  </div>
                )}

                <div className="relative text-left">
                  <Mail className="absolute left-3 top-3.5 w-5 h-5 text-text-muted" />
                  <input 
                    type="text"
                    placeholder={mode === 'register' ? 'Email' : (lang === 'ru' ? 'Email или Username' : 'Email or Username')}
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleEmailAuth()}
                    className="w-full bg-white/5 border border-white/10 p-3 pl-10 rounded-xl text-white outline-none focus:border-cyber-cyan transition-all placeholder:text-white/20"
                  />
                </div>

                <div className="relative text-left">
                  <Lock className="absolute left-3 top-3.5 w-5 h-5 text-text-muted" />
                  <input 
                    type="password"
                    placeholder="Password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleEmailAuth()}
                    className="w-full bg-white/5 border border-white/10 p-3 pl-10 rounded-xl text-white outline-none focus:border-cyber-cyan transition-all placeholder:text-white/20"
                  />
                </div>

                <Button 
                  onClick={handleEmailAuth}
                  disabled={isVerifying}
                  className="w-full bg-cyber-cyan text-black font-bold py-6 hover:brightness-110 transition-all uppercase tracking-widest shadow-lg shadow-cyber-cyan/20">
                  {isVerifying ? '...' : (mode === 'register' ? (lang === 'ru' ? 'Создать аккаунт' : 'Create Account') : (lang === 'ru' ? 'Войти' : 'Sign In'))}
                </Button>

                {mode !== 'register' && (
                  <button 
                    onClick={() => navigate('/forgot-password')}
                    className="text-text-muted text-sm hover:text-cyber-cyan transition-colors"
                  >
                    {lang === 'ru' ? 'Забыли пароль?' : 'Forgot password?'}
                  </button>
                )}

                <div className="relative flex py-2 items-center">
                  <div className="flex-grow border-t border-white/5"></div>
                  <span className="mx-4 text-text-muted text-[10px] uppercase tracking-[0.2em]">{lang === 'ru' ? 'Или через' : 'Or via'}</span>
                  <div className="flex-grow border-t border-white/5"></div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <Button 
                    onClick={handleGoogleSignIn}
                    disabled={!googleLoaded || isVerifying}
                    variant="outline" 
                    className="border-white/10 hover:bg-white/5 py-6 text-xs uppercase tracking-widest disabled:opacity-50">
                    <Chrome className="w-4 h-4 mr-2" /> Google
                  </Button>
                  <div className="relative bg-white/5 flex items-center justify-center rounded-xl border border-white/10 hover:border-cyber-cyan/50 transition-all overflow-hidden group">
                     <div className="scale-75 brightness-90 group-hover:brightness-110 transition-all">
                       <TonConnectButton />
                     </div>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          <div className="h-4 mt-2">
            {isVerifying && (
              <p className="text-cyber-cyan text-[10px] animate-pulse font-mono uppercase tracking-[0.3em]">
                {lang === 'ru' ? 'Проверка данных...' : 'Verifying data...'}
              </p>
            )}
          </div>
        </div>
      </motion.div>
    </div>
  );
}