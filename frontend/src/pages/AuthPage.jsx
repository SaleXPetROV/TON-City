import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { TonConnectButton, useTonWallet } from '@tonconnect/ui-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Building2, ArrowLeft, Globe, UserCircle, Mail, Lock, Chrome, CheckCircle2 } from 'lucide-react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useTranslation, languages } from '@/lib/translations';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

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
  const [agreementAccepted, setAgreementAccepted] = useState(false);
  
  // Email verification states
  const [showVerificationStep, setShowVerificationStep] = useState(false);
  const [verificationCode, setVerificationCode] = useState('');
  const [pendingEmail, setPendingEmail] = useState('');
  
  // 2FA states
  const [show2FAStep, setShow2FAStep] = useState(false);
  const [totpCode, setTotpCode] = useState('');
  const [pending2FAEmail, setPending2FAEmail] = useState('');
  const [pending2FAPassword, setPending2FAPassword] = useState('');
  
  const [showUsernameStep, setShowUsernameStep] = useState(false);
  const [googleLoaded, setGoogleLoaded] = useState(false);

  const finishAuth = async (data) => {
    localStorage.setItem('token', data.token);
    // Dispatch event for MaintenanceOverlay
    window.dispatchEvent(new Event('ton-city-auth'));
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
      const res = await fetch(`${API}/auth/google`, {
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

      if (mode === 'register' && !agreementAccepted) {
        toast.error(lang === 'ru' ? 'Необходимо принять пользовательское соглашение' : 'You must accept the terms of service');
        setIsVerifying(false);
        return;
      }

      // Для регистрации используем новый endpoint с верификацией email
      const endpoint = mode === 'register' ? `${API}/auth/register/initiate` : `${API}/auth/login`;
      
      const res = await fetch(endpoint, {
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

      // Проверяем статус ответа для регистрации
      if (mode === 'register') {
        if (data.status === 'verification_sent') {
          // Нужно ввести код верификации
          setPendingEmail(email);
          setShowVerificationStep(true);
          toast.success(lang === 'ru' ? 'Код отправлен на email' : 'Code sent to email');
          setIsVerifying(false);
          return;
        } else if (data.status === 'registered' && data.token) {
          // SMTP не настроен - регистрация прошла сразу
          await finishAuth(data);
          return;
        }
      }
      
      // Проверяем требуется ли 2FA
      if (data.requires_2fa) {
        setPending2FAEmail(email);
        setPending2FAPassword(password);
        setShow2FAStep(true);
        toast.info(lang === 'ru' ? 'Введите код из приложения аутентификации' : 'Enter code from authenticator app');
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

  // Подтверждение email кода
  const handleVerifyEmail = async () => {
    if (!verificationCode.trim()) {
      toast.error(lang === 'ru' ? 'Введите код' : 'Enter code');
      return;
    }
    
    setIsVerifying(true);
    try {
      const res = await fetch(`${API}/auth/register/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: pendingEmail, code: verificationCode.trim() })
      });
      
      const responseText = await res.text();
      let data = null;
      try {
        data = JSON.parse(responseText);
      } catch (jsonErr) {
        console.error("JSON parse error:", jsonErr);
        toast.error(lang === 'ru' ? 'Ошибка сервера' : 'Server error');
        return;
      }
      
      if (!res.ok) {
        toast.error(data?.detail || (lang === 'ru' ? 'Неверный код' : 'Invalid code'));
        return;
      }
      
      if (data.token) {
        toast.success(lang === 'ru' ? 'Email подтверждён!' : 'Email verified!');
        await finishAuth(data);
      }
    } catch (e) {
      console.error("Verify error:", e);
      toast.error(lang === 'ru' ? 'Ошибка подтверждения' : 'Verification failed');
    } finally {
      setIsVerifying(false);
    }
  };
  
  // Обработка входа с 2FA кодом
  const handle2FALogin = async () => {
    if (!totpCode.trim() || totpCode.length < 6) {
      toast.error(lang === 'ru' ? 'Введите 6-значный код' : 'Enter 6-digit code');
      return;
    }
    
    setIsVerifying(true);
    try {
      const res = await fetch(`${API}/auth/login-2fa`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          email: pending2FAEmail, 
          password: pending2FAPassword, 
          totp_code: totpCode.trim() 
        })
      });
      
      const data = await res.json();
      
      if (!res.ok) {
        toast.error(data?.detail || (lang === 'ru' ? 'Неверный код 2FA' : 'Invalid 2FA code'));
        return;
      }
      
      if (data.token) {
        toast.success(lang === 'ru' ? 'Вход выполнен!' : 'Logged in!');
        await finishAuth(data);
      }
    } catch (e) {
      console.error("2FA login error:", e);
      toast.error(lang === 'ru' ? 'Ошибка авторизации' : 'Auth failed');
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
          const response = await fetch(`${API}/auth/verify-wallet`, {
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

          const responseText = await response.text();
          let data = null;
          
          try {
            data = JSON.parse(responseText);
          } catch (jsonErr) {
            console.error("JSON parse error in verifyWallet:", jsonErr, "Response:", responseText);
            toast.error(lang === 'ru' ? 'Ошибка соединения с сервером' : 'Server connection error');
            return;
          }

          if (!response.ok) {
            throw new Error(data?.detail || 'Auth failed');
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
          if (error.message === 'Failed to fetch') {
            toast.error(lang === 'ru' ? "Ошибка соединения с сервером" : "Server connection error");
          } else {
            toast.error(error.message);
          }
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
      const response = await fetch(`${API}/auth/verify-wallet`, {
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

      const responseText = await response.text();
      let data = null;
      try {
        data = JSON.parse(responseText);
      } catch (jsonErr) {
        console.error("JSON parse error:", jsonErr, "Response:", responseText);
        toast.error(lang === 'ru' ? 'Ошибка сервера' : 'Server error');
        return;
      }

      if (response.ok && data.token) {
        // Используем finishAuth для корректной обработки
        finishAuth(data);
      } else {
        toast.error(data?.detail || "Error");
      }
    } catch (e) {
      console.error("Registration error:", e);
      toast.error(lang === 'ru' ? "Ошибка соединения с сервером" : "Server connection error");
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
          onClick={() => {
            if (showVerificationStep) {
              setShowVerificationStep(false);
            } else if (show2FAStep) {
              setShow2FAStep(false);
              setTotpCode('');
            } else if (showUsernameStep) {
              setShowUsernameStep(false);
            } else {
              navigate('/');
            }
          }} 
          className="absolute top-6 left-6 text-text-muted hover:text-white transition-colors"
        >
          <ArrowLeft className="w-6 h-6" />
        </button>
        
        <div className="w-16 h-16 bg-gradient-to-br from-cyber-cyan to-neon-purple rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-lg shadow-cyber-cyan/20">
          <Building2 className="text-black w-10 h-10" />
        </div>

        <h1 className="font-unbounded text-xl font-bold text-white mb-8 tracking-tighter uppercase">
          {showVerificationStep 
            ? (lang === 'ru' ? 'Подтверждение Email' : 'Verify Email')
            : show2FAStep
            ? (lang === 'ru' ? 'Проверка 2FA' : '2FA Verification')
            : title
          }
        </h1>

        <div className="space-y-4">
          <AnimatePresence mode="wait">
            {/* Email Verification Step */}
            {showVerificationStep ? (
              <motion.div 
                key="verification-step"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="space-y-4"
              >
                <div className="p-4 bg-cyber-cyan/10 border border-cyber-cyan/20 rounded-xl mb-4">
                  <p className="text-cyber-cyan text-sm">
                    {lang === 'ru' 
                      ? `Код отправлен на ${pendingEmail}` 
                      : `Code sent to ${pendingEmail}`
                    }
                  </p>
                </div>

                <div className="relative text-left">
                  <Mail className="absolute left-3 top-3.5 w-5 h-5 text-cyber-cyan" />
                  <Input
                    type="text"
                    value={verificationCode}
                    onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                    placeholder={lang === 'ru' ? "Код из email (6 цифр)" : "Code from email (6 digits)"}
                    className="w-full pl-10 pr-4 py-3.5 bg-panel border border-white/10 rounded-xl text-white placeholder-white/30 focus:border-cyber-cyan focus:ring-1 focus:ring-cyber-cyan/50 text-center text-2xl tracking-[0.5em] font-mono"
                    maxLength={6}
                  />
                </div>

                <Button 
                  data-testid="verify-email-btn"
                  onClick={handleVerifyEmail}
                  disabled={isVerifying || verificationCode.length !== 6}
                  className="w-full bg-cyber-cyan text-black font-bold py-4 rounded-xl uppercase tracking-widest hover:bg-cyber-cyan/90 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isVerifying 
                    ? (lang === 'ru' ? 'Проверка...' : 'Verifying...') 
                    : (lang === 'ru' ? 'Подтвердить' : 'Verify')
                  }
                </Button>

                <p className="text-text-muted text-xs mt-4">
                  {lang === 'ru' 
                    ? 'Не получили код? Проверьте папку "Спам"' 
                    : "Didn't receive code? Check your spam folder"
                  }
                </p>
              </motion.div>
            ) : show2FAStep ? (
              /* 2FA Verification Step */
              <motion.div 
                key="2fa-step"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="space-y-4"
              >
                <div className="p-4 bg-neon-purple/10 border border-neon-purple/20 rounded-xl mb-4">
                  <div className="flex items-center justify-center gap-2 mb-2">
                    <Lock className="w-5 h-5 text-neon-purple" />
                    <span className="text-neon-purple text-sm font-bold">
                      {lang === 'ru' ? 'Двухфакторная аутентификация' : 'Two-Factor Authentication'}
                    </span>
                  </div>
                  <p className="text-white/60 text-xs">
                    {lang === 'ru' 
                      ? 'Введите 6-значный код из приложения аутентификации (Google Authenticator, Authy)'
                      : 'Enter 6-digit code from your authenticator app'
                    }
                  </p>
                </div>

                <div className="relative text-left">
                  <Lock className="absolute left-3 top-3.5 w-5 h-5 text-neon-purple" />
                  <Input
                    type="text"
                    value={totpCode}
                    onChange={(e) => setTotpCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                    placeholder="000000"
                    autoFocus
                    className="w-full pl-10 pr-4 py-3.5 bg-panel border border-white/10 rounded-xl text-white placeholder-white/30 focus:border-neon-purple focus:ring-1 focus:ring-neon-purple/50 text-center text-2xl tracking-[0.5em] font-mono"
                    maxLength={6}
                  />
                </div>

                <Button 
                  data-testid="verify-2fa-btn"
                  onClick={handle2FALogin}
                  disabled={isVerifying || totpCode.length !== 6}
                  className="w-full bg-neon-purple text-white font-bold py-4 rounded-xl uppercase tracking-widest hover:bg-neon-purple/90 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isVerifying 
                    ? (lang === 'ru' ? 'Проверка...' : 'Verifying...') 
                    : (lang === 'ru' ? 'Войти' : 'Login')
                  }
                </Button>

                <button 
                  onClick={() => {
                    setShow2FAStep(false);
                    setTotpCode('');
                  }}
                  className="text-text-muted text-xs hover:text-white transition-colors"
                >
                  {lang === 'ru' ? '← Назад к форме входа' : '← Back to login'}
                </button>

                <p className="text-text-muted text-xs mt-2">
                  {lang === 'ru' 
                    ? 'Также можно использовать резервный код' 
                    : 'You can also use a backup code'
                  }
                </p>
              </motion.div>
            ) : showUsernameStep ? (
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

                {/* Agreement checkbox - only for registration */}
                {mode === 'register' && (
                  <div className="flex items-start gap-3 text-left">
                    <input
                      type="checkbox"
                      id="agreement"
                      checked={agreementAccepted}
                      onChange={(e) => setAgreementAccepted(e.target.checked)}
                      className="mt-1 w-4 h-4 rounded border-gray-500 bg-transparent accent-cyan-400 cursor-pointer"
                    />
                    <label htmlFor="agreement" className="text-xs text-gray-400 cursor-pointer leading-relaxed">
                      {lang === 'ru' 
                        ? 'Я согласен с Пользовательским соглашением и Политикой конфиденциальности TON-City. Я понимаю, что это экономическая стратегия с виртуальной валютой.'
                        : 'I agree to the Terms of Service and Privacy Policy of TON-City. I understand this is an economic strategy game with virtual currency.'
                      }
                    </label>
                  </div>
                )}

                <Button 
                  onClick={handleEmailAuth}
                  disabled={isVerifying || (mode === 'register' && !agreementAccepted)}
                  className="w-full bg-cyber-cyan text-black font-bold py-6 hover:brightness-110 transition-all uppercase tracking-widest shadow-lg shadow-cyber-cyan/20 disabled:opacity-50 disabled:cursor-not-allowed">
                  {isVerifying ? '...' : (mode === 'register' ? (lang === 'ru' ? 'Создать аккаунт' : 'Create Account') : (lang === 'ru' ? 'Войти' : 'Sign In'))}
                </Button>

                {/* Кнопки переключения между входом и регистрацией */}
                <div className="flex items-center justify-center gap-4 text-sm">
                  {mode !== 'register' ? (
                    <>
                      <button 
                        onClick={() => navigate('/forgot-password')}
                        className="text-text-muted hover:text-cyber-cyan transition-colors"
                      >
                        {lang === 'ru' ? 'Забыли пароль?' : 'Forgot password?'}
                      </button>
                      <span className="text-white/20">|</span>
                      <button 
                        onClick={() => navigate('/auth?mode=register')}
                        className="text-cyber-cyan hover:text-cyber-cyan/80 transition-colors font-medium"
                      >
                        {lang === 'ru' ? 'Зарегистрироваться' : 'Register'}
                      </button>
                    </>
                  ) : (
                    <button 
                      onClick={() => navigate('/auth?mode=login')}
                      className="text-cyber-cyan hover:text-cyber-cyan/80 transition-colors font-medium"
                    >
                      {lang === 'ru' ? 'Уже есть аккаунт? Войти' : 'Already have account? Sign In'}
                    </button>
                  )}
                </div>

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