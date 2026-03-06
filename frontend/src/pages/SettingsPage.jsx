import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTonConnectUI, useTonWallet } from '@tonconnect/ui-react';
import { motion } from 'framer-motion';
import { 
  Building2, User, Mail, Lock, Wallet, 
  Camera, Save, Globe, Shield, LogOut, Link2, Unlink
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { languages, useTranslation } from '@/lib/translations';
import { toast } from 'sonner';
import Sidebar from '@/components/Sidebar';

export default function SettingsPage({ user: propUser, setUser: setAppUser, onLogout }) {
  const navigate = useNavigate();
  const [tonConnectUI] = useTonConnectUI();
  const wallet = useTonWallet();
  const [user, setUser] = useState(propUser);
  const [loading, setLoading] = useState(!propUser);
  const [lang, setLang] = useState(localStorage.getItem('ton_city_lang') || 'ru');
  const { t } = useTranslation(lang);

  // Form states
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [newPasswordConfirm, setNewPasswordConfirm] = useState('');
  const [saving, setSaving] = useState(false);
  const [linkingWallet, setLinkingWallet] = useState(false);
  
  // Telegram
  const [telegramUsername, setTelegramUsername] = useState('');
  const [savingTelegram, setSavingTelegram] = useState(false);

  useEffect(() => {
    if (propUser) {
      setUser(propUser);
      setUsername(propUser.username || '');
      setEmail(propUser.email || '');
      setTelegramUsername(propUser.telegram_username || '');
      setLoading(false);
    } else {
      checkAuth();
    }
  }, [propUser]);

  // Обработка привязки кошелька через TonConnect
  useEffect(() => {
    if (linkingWallet && wallet) {
      handleLinkWalletFromTonConnect();
    }
  }, [wallet, linkingWallet]);

  const checkAuth = async () => {
    const token = localStorage.getItem('token');
    if (!token) {
      navigate('/auth?mode=login');
      return;
    }

    try {
      const response = await fetch('/api/auth/me', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
        setUsername(userData.username || '');
        setEmail(userData.email || '');
      } else {
        localStorage.removeItem('token');
        navigate('/auth?mode=login');
      }
    } catch (error) {
      console.error("Auth check failed", error);
      navigate('/auth?mode=login');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateUsername = async () => {
    if (!username.trim() || username.length < 3) {
      toast.error(t('usernameTooShort') || 'Username too short');
      return;
    }

    setSaving(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/auth/update-username', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ username })
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data.detail);

      toast.success(t('usernameUpdated') || 'Username updated!');
      // Обновляем глобальное состояние
      if (setAppUser) {
        setAppUser(prev => ({ ...prev, username }));
      }
      checkAuth();
    } catch (error) {
      toast.error(error.message);
    } finally {
      setSaving(false);
    }
  };

  const handleUpdateEmail = async () => {
    if (!email.trim()) {
      toast.error(t('enterEmail') || 'Enter email');
      return;
    }
    if (!currentPassword) {
      toast.error(t('enterCurrentPassword') || 'Enter current password');
      return;
    }

    setSaving(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/auth/update-email', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ email, password: currentPassword })
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data.detail);

      toast.success(t('emailUpdated') || 'Email updated!');
      setCurrentPassword('');
      if (setAppUser) {
        setAppUser(prev => ({ ...prev, email }));
      }
      checkAuth();
    } catch (error) {
      toast.error(error.message);
    } finally {
      setSaving(false);
    }
  };

  const handleUpdatePassword = async () => {
    if (!currentPassword || !newPassword) {
      toast.error(t('fillAllFields') || 'Fill all fields');
      return;
    }
    if (newPassword !== newPasswordConfirm) {
      toast.error(t('passwordsNoMatch') || 'Passwords do not match');
      return;
    }
    if (newPassword.length < 6) {
      toast.error(t('passwordTooShort') || 'Password too short');
      return;
    }

    setSaving(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/auth/update-password', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ 
          current_password: currentPassword,
          new_password: newPassword
        })
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data.detail);

      toast.success(t('passwordUpdated') || 'Password updated!');
      setCurrentPassword('');
      setNewPassword('');
      setNewPasswordConfirm('');
    } catch (error) {
      toast.error(error.message);
    } finally {
      setSaving(false);
    }
  };

  // Привязка кошелька через TonConnect
  const handleConnectWallet = async () => {
    if (wallet) {
      // Уже подключен кошелек - просто привязываем
      await handleLinkWalletFromTonConnect();
    } else {
      // Открываем TonConnect модал
      setLinkingWallet(true);
      try {
        await tonConnectUI.openModal();
      } catch (e) {
        setLinkingWallet(false);
        toast.error(t('walletConnectionError') || 'Wallet connection error');
      }
    }
  };

  const handleLinkWalletFromTonConnect = async () => {
    if (!wallet) return;
    
    setLinkingWallet(false);
    setSaving(true);
    
    try {
      const token = localStorage.getItem('token');
      const walletAddress = wallet.account.address;
      
      const response = await fetch('/api/auth/link-wallet', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ wallet_address: walletAddress })
      });

      const data = await response.json();
      if (!response.ok) {
        // Disconnect the failed wallet so user can try another
        try { await tonConnectUI.disconnect(); } catch (e) {}
        throw new Error(data.detail);
      }

      toast.success(t('walletLinked') || 'Wallet linked!');
      if (setAppUser) {
        setAppUser(prev => ({ ...prev, wallet_address: walletAddress }));
      }
      checkAuth();
    } catch (error) {
      toast.error(error.message);
    } finally {
      setSaving(false);
    }
  };

  // Telegram
  const handleLinkTelegram = async () => {
    if (!telegramUsername.trim()) {
      toast.error('Укажите Telegram username');
      return;
    }
    setSavingTelegram(true);
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${BACKEND_URL}/api/auth/link-telegram?telegram_username=${encodeURIComponent(telegramUsername.trim())}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Ошибка');
      }
      toast.success('Telegram привязан!');
      setUser(prev => ({ ...prev, telegram_username: telegramUsername.trim().replace('@', '') }));
    } catch (e) { toast.error(e.message); }
    finally { setSavingTelegram(false); }
  };

  const handleUnlinkTelegram = async () => {
    setSavingTelegram(true);
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${BACKEND_URL}/api/auth/unlink-telegram`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Ошибка');
      toast.success('Telegram отвязан');
      setTelegramUsername('');
      setUser(prev => ({ ...prev, telegram_username: null }));
    } catch (e) { toast.error(e.message); }
    finally { setSavingTelegram(false); }
  };

  // Отвязка кошелька
  const handleUnlinkWallet = async () => {
    setSaving(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/auth/unlink-wallet', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data.detail);

      toast.success(t('walletUnlinked') || 'Wallet unlinked!');
      if (setAppUser) {
        setAppUser(prev => ({ ...prev, wallet_address: null }));
      }
      // Отключаем TonConnect тоже
      await tonConnectUI.disconnect();
      checkAuth();
    } catch (error) {
      toast.error(error.message);
    } finally {
      setSaving(false);
    }
  };

  const handleAvatarUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = async (event) => {
      const avatar_data = event.target?.result;
      
      setSaving(true);
      try {
        const token = localStorage.getItem('token');
        const response = await fetch('/api/auth/upload-avatar', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ avatar_data })
        });

        const data = await response.json();
        if (!response.ok) throw new Error(data.detail);

        toast.success(t('avatarUpdated') || 'Avatar updated!');
        if (setAppUser) {
          setAppUser(prev => ({ ...prev, avatar: avatar_data }));
        }
        checkAuth();
      } catch (error) {
        toast.error(error.message);
      } finally {
        setSaving(false);
      }
    };
    reader.readAsDataURL(file);
  };

  const handleLogout = async () => {
    try {
      // Отключаем TonConnect если подключен
      if (wallet) {
        await tonConnectUI.disconnect();
      }
    } catch (e) {
      console.error('TonConnect disconnect error:', e);
    }
    
    localStorage.removeItem('token');
    if (onLogout) {
      onLogout();
    } else if (setAppUser) {
      setAppUser(null);
    }
    toast.success(t('loggedOut') || 'Logged out');
    navigate('/');
  };

  const changeLang = (newLang) => {
    setLang(newLang);
    localStorage.setItem('ton_city_lang', newLang);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-void flex items-center justify-center font-rajdhani">
        <div className="text-cyber-cyan animate-pulse">
          {t('loading') || 'Loading...'}
        </div>
      </div>
    );
  }

  const isGoogleUser = user?.auth_type === 'google';
  const isWalletOnlyUser = user?.auth_type === 'wallet';
  const isEmailUser = user?.auth_type === 'email';

  return (
    <div className="flex h-screen bg-void">
      <Sidebar user={user} />
      
      <div className="flex-1 overflow-auto lg:ml-16">
        <div className="relative min-h-screen font-rajdhani pb-20 lg:pb-0">
          {/* Background grid */}
          <div className="absolute inset-0 opacity-10 pointer-events-none">
            <div 
              className="absolute inset-0"
              style={{
                backgroundImage: `
                  linear-gradient(rgba(0, 240, 255, 0.1) 1px, transparent 1px),
                  linear-gradient(90deg, rgba(0, 240, 255, 0.1) 1px, transparent 1px)
                `,
                backgroundSize: '50px 50px',
              }}
            />
          </div>

          {/* Header */}
          <div className="relative z-10 container mx-auto px-4 sm:px-6 py-4 sm:py-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-gradient-to-br from-cyber-cyan to-neon-purple rounded-xl flex items-center justify-center">
                  <User className="w-5 h-5 text-black" />
                </div>
                <div>
                  <h1 className="font-unbounded text-lg sm:text-xl font-bold text-white uppercase tracking-tight">
                    {t('settings') || 'Настройки'}
                  </h1>
                  <p className="text-text-muted text-xs">Управление аккаунтом</p>
                </div>
              </div>

              <Select value={lang} onValueChange={changeLang}>
                <SelectTrigger className="w-28 sm:w-36 bg-panel border-grid-border text-text-main text-sm">
                  <Globe className="w-4 h-4 mr-1 sm:mr-2" />
                  <SelectValue>
                    {languages.find(l => l.code === lang)?.flag} {lang.toUpperCase()}
                  </SelectValue>
                </SelectTrigger>
                <SelectContent>
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
          </div>

          {/* Main Content */}
          <div className="relative z-10 container mx-auto px-4 sm:px-6 py-6 sm:py-12 max-w-4xl">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-6 sm:space-y-8"
        >
          <div className="text-center mb-8 sm:mb-12">
            <h1 className="font-unbounded text-2xl sm:text-3xl font-bold text-white mb-2 uppercase tracking-tight">
              {t('settingsTitle') || 'Settings'}
            </h1>
            <p className="text-text-muted text-sm sm:text-base">
              {t('accountManagement') || 'Manage your account'}
            </p>
          </div>

          {/* Avatar Section */}
          <div className="glass-panel rounded-2xl p-4 sm:p-8 border border-white/10">
            <div className="flex flex-col sm:flex-row items-center gap-4 sm:gap-6">
              <div className="relative">
                {user?.avatar ? (
                  <img 
                    src={user.avatar} 
                    alt="Avatar"
                    className="w-20 h-20 sm:w-24 sm:h-24 rounded-full border-2 border-cyber-cyan object-cover"
                  />
                ) : (
                  <div className="w-20 h-20 sm:w-24 sm:h-24 bg-gradient-to-br from-cyber-cyan to-neon-purple rounded-full flex items-center justify-center text-2xl sm:text-3xl font-bold text-black">
                    {(user?.username || 'U')[0].toUpperCase()}
                  </div>
                )}
                <label className="absolute bottom-0 right-0 bg-cyber-cyan text-black p-2 rounded-full cursor-pointer hover:brightness-110 transition-all">
                  <Camera className="w-4 h-4" />
                  <input type="file" accept="image/*" className="hidden" onChange={handleAvatarUpload} />
                </label>
              </div>
              <div className="text-center sm:text-left">
                <h3 className="text-lg sm:text-xl font-bold text-white">{user?.display_name || user?.username}</h3>
                <p className="text-text-muted text-sm">{user?.email || (user?.wallet_address ? (() => { try { const { toUserFriendlyAddress, shortenAddress } = require('@/lib/tonAddress'); return shortenAddress(toUserFriendlyAddress(user.wallet_address)); } catch { return `${user.wallet_address.slice(0, 8)}...${user.wallet_address.slice(-6)}`; } })() : '')}</p>
                <div className="flex items-center gap-2 mt-2">
                  <span className="text-text-muted text-xs uppercase">ID:</span>
                  <code className="text-cyber-cyan text-xs font-mono bg-white/5 px-2 py-1 rounded">{user?.id}</code>
                  <button 
                    onClick={() => {
                      navigator.clipboard.writeText(user?.id || '');
                      toast.success('ID скопирован!');
                    }}
                    className="text-text-muted hover:text-cyber-cyan transition-colors"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Username */}
          <div className="glass-panel rounded-2xl p-4 sm:p-8 border border-white/10">
            <div className="flex items-center gap-2 mb-4">
              <User className="w-5 h-5 text-cyber-cyan" />
              <h3 className="text-base sm:text-lg font-bold text-white uppercase tracking-wide">
                {t('changeUsername') || 'Username'}
              </h3>
            </div>
            <div className="space-y-4">
              <input 
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Username"
                className="w-full bg-white/5 border border-white/10 p-3 rounded-xl text-white outline-none focus:border-cyber-cyan transition-all text-sm sm:text-base"
              />
              <Button 
                onClick={handleUpdateUsername}
                disabled={saving}
                className="w-full sm:w-auto bg-cyber-cyan text-black hover:brightness-110">
                <Save className="w-4 h-4 mr-2" />
                {t('save') || 'Save'}
              </Button>
            </div>
          </div>

          {/* Email (only for email users, not Google or wallet-only) */}
          {(isEmailUser || isWalletOnlyUser) && (
            <div className="glass-panel rounded-2xl p-4 sm:p-8 border border-white/10">
              <div className="flex items-center gap-2 mb-4">
                <Mail className="w-5 h-5 text-cyber-cyan" />
                <h3 className="text-base sm:text-lg font-bold text-white uppercase tracking-wide">
                  {t('changeEmail') || 'Email'}
                </h3>
              </div>
              <div className="space-y-4">
                <input 
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Email"
                  className="w-full bg-white/5 border border-white/10 p-3 rounded-xl text-white outline-none focus:border-cyber-cyan transition-all text-sm sm:text-base"
                />
                <input 
                  type="password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  placeholder={t('currentPasswordConfirm') || 'Current password to confirm'}
                  className="w-full bg-white/5 border border-white/10 p-3 rounded-xl text-white outline-none focus:border-cyber-cyan transition-all text-sm sm:text-base"
                />
                <Button 
                  onClick={handleUpdateEmail}
                  disabled={saving}
                  className="w-full sm:w-auto bg-cyber-cyan text-black hover:brightness-110">
                  <Save className="w-4 h-4 mr-2" />
                  {t('updateEmail') || 'Update Email'}
                </Button>
              </div>
            </div>
          )}

          {/* Password (only for email users, not Google or wallet-only) */}
          {isEmailUser && (
            <div className="glass-panel rounded-2xl p-4 sm:p-8 border border-white/10">
              <div className="flex items-center gap-2 mb-4">
                <Lock className="w-5 h-5 text-cyber-cyan" />
                <h3 className="text-base sm:text-lg font-bold text-white uppercase tracking-wide">
                  {t('changePassword') || 'Password'}
                </h3>
              </div>
              <div className="space-y-4">
                <input 
                  type="password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  placeholder={t('currentPassword') || 'Current password'}
                  className="w-full bg-white/5 border border-white/10 p-3 rounded-xl text-white outline-none focus:border-cyber-cyan transition-all text-sm sm:text-base"
                />
                <input 
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder={t('newPassword') || 'New password'}
                  className="w-full bg-white/5 border border-white/10 p-3 rounded-xl text-white outline-none focus:border-cyber-cyan transition-all text-sm sm:text-base"
                />
                <input 
                  type="password"
                  value={newPasswordConfirm}
                  onChange={(e) => setNewPasswordConfirm(e.target.value)}
                  placeholder={t('confirmPassword') || 'Confirm new password'}
                  className="w-full bg-white/5 border border-white/10 p-3 rounded-xl text-white outline-none focus:border-cyber-cyan transition-all text-sm sm:text-base"
                />
                <Button 
                  onClick={handleUpdatePassword}
                  disabled={saving}
                  className="w-full sm:w-auto bg-cyber-cyan text-black hover:brightness-110">
                  <Save className="w-4 h-4 mr-2" />
                  {t('changePassword') || 'Change Password'}
                </Button>
              </div>
            </div>
          )}

          {/* TON Wallet - через TonConnect */}
          <div className="glass-panel rounded-2xl p-4 sm:p-8 border border-white/10">
            <div className="flex items-center gap-2 mb-4">
              <Wallet className="w-5 h-5 text-cyber-cyan" />
              <h3 className="text-base sm:text-lg font-bold text-white uppercase tracking-wide">
                {t('tonWallet') || 'TON Wallet'}
              </h3>
            </div>
            <div className="space-y-4">
              {user?.wallet_address ? (
                <>
                  <div className="bg-white/5 border border-cyber-cyan/20 p-4 rounded-xl">
                    <p className="text-xs text-text-muted mb-1 uppercase tracking-wider">
                      {t('linkedWallet') || 'Linked Wallet'}
                    </p>
                    {/* User-friendly формат адреса */}
                    <div className="flex items-center gap-2">
                      <p className="text-cyber-cyan font-mono text-sm sm:text-base">
                        {(() => {
                          try {
                            const { toUserFriendlyAddress } = require('@/lib/tonAddress');
                            const friendly = toUserFriendlyAddress(user.wallet_address);
                            return friendly.slice(0, 6) + '...' + friendly.slice(-4);
                          } catch { return user.wallet_address.slice(0, 6) + '...' + user.wallet_address.slice(-4); }
                        })()}
                      </p>
                      <button 
                        onClick={() => {
                          try {
                            const { toUserFriendlyAddress } = require('@/lib/tonAddress');
                            const friendly = toUserFriendlyAddress(user.wallet_address);
                            navigator.clipboard.writeText(friendly);
                          } catch {
                            navigator.clipboard.writeText(user.wallet_address);
                          }
                          toast.success('Адрес скопирован!');
                        }}
                        className="p-1 rounded hover:bg-white/10 transition-colors"
                        title="Скопировать полный адрес"
                      >
                        <svg className="w-4 h-4 text-text-muted hover:text-cyber-cyan" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                        </svg>
                      </button>
                    </div>
                    <p className="text-xs text-text-muted mt-2 break-all font-mono opacity-60">
                      {(() => {
                        try {
                          const { toUserFriendlyAddress } = require('@/lib/tonAddress');
                          return toUserFriendlyAddress(user.wallet_address);
                        } catch { return user.wallet_address; }
                      })()}
                    </p>
                  </div>
                  <Button 
                    onClick={handleUnlinkWallet}
                    disabled={saving}
                    variant="outline"
                    className="w-full sm:w-auto border-red-500/50 text-red-400 hover:bg-red-500/10">
                    <Unlink className="w-4 h-4 mr-2" />
                    {t('unlinkWallet') || 'Unlink Wallet'}
                  </Button>
                </>
              ) : (
                <>
                  <p className="text-text-muted text-sm">
                    {t('connectWalletDesc') || 'Connect your TON wallet via TonConnect to link it to your account.'}
                  </p>
                  <Button 
                    onClick={handleConnectWallet}
                    disabled={saving || linkingWallet}
                    className="w-full sm:w-auto bg-gradient-to-r from-[#0098EA] to-[#0057FF] text-white hover:brightness-110">
                    <Link2 className="w-4 h-4 mr-2" />
                    {linkingWallet ? (t('connecting') || 'Connecting...') : (t('connectWallet') || 'Connect Wallet')}
                  </Button>
                </>
              )}
            </div>
          </div>

          {/* Telegram Notifications */}
          <div className="glass-panel rounded-2xl p-4 sm:p-8 border border-white/10">
            <div className="flex items-center gap-2 mb-4">
              <svg className="w-5 h-5 text-[#26A5E4]" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.562 8.161c-.18 1.897-.962 6.502-1.359 8.627-.168.9-.5 1.201-.82 1.23-.697.064-1.226-.461-1.901-.903-1.056-.692-1.653-1.123-2.678-1.799-1.185-.781-.417-1.21.258-1.911.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.139-5.062 3.345-.479.329-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.244-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.831-2.529 6.998-3.014 3.333-1.386 4.025-1.627 4.477-1.635.099-.002.321.023.465.141.12.098.153.229.169.339.016.11.035.324.019.5z"/></svg>
              <h3 className="text-base sm:text-lg font-bold text-white uppercase tracking-wide">
                Telegram уведомления
              </h3>
            </div>
            <div className="space-y-4">
              {user?.telegram_username ? (
                <>
                  <div className="bg-white/5 border border-[#26A5E4]/20 p-4 rounded-xl">
                    <p className="text-xs text-text-muted mb-1 uppercase tracking-wider">Привязанный Telegram</p>
                    <p className="text-[#26A5E4] font-mono text-sm">@{user.telegram_username}</p>
                  </div>
                  <Button 
                    onClick={handleUnlinkTelegram}
                    disabled={savingTelegram}
                    variant="outline"
                    className="w-full sm:w-auto border-red-500/50 text-red-400 hover:bg-red-500/10">
                    Отвязать Telegram
                  </Button>
                </>
              ) : (
                <>
                  <p className="text-text-muted text-sm">
                    Привяжите Telegram для получения уведомлений о кредитах, платежах и событиях.
                  </p>
                  <div className="flex gap-2">
                    <input
                      data-testid="telegram-input"
                      type="text"
                      value={telegramUsername}
                      onChange={(e) => setTelegramUsername(e.target.value)}
                      placeholder="@username"
                      className="flex-1 bg-white/5 border border-white/10 p-3 rounded-xl text-white outline-none focus:border-[#26A5E4] transition-all text-sm"
                    />
                    <Button 
                      data-testid="link-telegram-btn"
                      onClick={handleLinkTelegram}
                      disabled={savingTelegram || !telegramUsername.trim()}
                      className="bg-[#26A5E4] text-white hover:brightness-110">
                      {savingTelegram ? 'Привязка...' : 'Привязать'}
                    </Button>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Security Settings - 2FA & Passkey */}
          <div className="glass-panel rounded-2xl p-4 sm:p-8 border border-cyber-cyan/20 bg-cyber-cyan/5">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <Shield className="w-6 h-6 text-cyber-cyan" />
                <div>
                  <h3 className="text-base sm:text-lg font-bold text-white uppercase tracking-wide">
                    Безопасность
                  </h3>
                  <p className="text-text-muted text-sm">
                    2FA, Passkey и защита вывода средств
                  </p>
                </div>
              </div>
              <Button 
                data-testid="security-settings-btn"
                onClick={() => navigate('/security')}
                className="w-full sm:w-auto bg-cyber-cyan text-black hover:brightness-110">
                <Shield className="w-4 h-4 mr-2" />
                Настроить
              </Button>
            </div>
          </div>

          {/* Account Info for Google users */}
          {isGoogleUser && (
            <div className="glass-panel rounded-2xl p-4 sm:p-6 border border-neon-purple/20 bg-neon-purple/5">
              <div className="flex items-start gap-3">
                <Shield className="w-5 h-5 text-neon-purple mt-1 flex-shrink-0" />
                <div>
                  <h4 className="text-white font-bold mb-1">
                    {t('googleAccount') || 'Google Account'}
                  </h4>
                  <p className="text-text-muted text-sm">
                    {t('googleAccountDesc') || 'You signed in with Google. Email and password are managed through your Google account.'}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Logout Button */}
          <div className="glass-panel rounded-2xl p-4 sm:p-8 border border-red-500/20 bg-red-500/5">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div>
                <h3 className="text-base sm:text-lg font-bold text-white uppercase tracking-wide mb-1">
                  {t('logout') || 'Log Out'}
                </h3>
                <p className="text-text-muted text-sm">
                  {t('logoutDesc') || 'Sign out of your account on this device'}
                </p>
              </div>
              <Button 
                onClick={handleLogout}
                variant="outline"
                className="w-full sm:w-auto border-red-500/50 text-red-400 hover:bg-red-500/10 hover:text-red-300">
                <LogOut className="w-4 h-4 mr-2" />
                {t('logout') || 'Log Out'}
              </Button>
            </div>
          </div>
        </motion.div>
      </div>
        </div>
      </div>
    </div>
  );
}
