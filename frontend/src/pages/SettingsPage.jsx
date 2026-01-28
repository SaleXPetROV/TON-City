import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTonConnectUI, useTonWallet } from '@tonconnect/ui-react';
import { motion } from 'framer-motion';
import { 
  Building2, ArrowLeft, User, Mail, Lock, Wallet, 
  Camera, Save, Globe, Shield, LogOut, Link2, Unlink
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { languages, useTranslation } from '@/lib/translations';
import { toast } from 'sonner';

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

  useEffect(() => {
    if (propUser) {
      setUser(propUser);
      setUsername(propUser.username || '');
      setEmail(propUser.email || '');
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
      if (!response.ok) throw new Error(data.detail);

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
    <div className="min-h-screen bg-void relative overflow-hidden font-rajdhani pb-20 lg:pb-0">
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
          <button 
            onClick={() => navigate('/')}
            className="flex items-center gap-2 sm:gap-3 text-white hover:text-cyber-cyan transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
            <span className="font-unbounded text-xs sm:text-sm font-bold uppercase tracking-wider">
              {t('back') || 'Back'}
            </span>
          </button>

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
                <p className="text-text-muted text-sm">{user?.email || (user?.wallet_address ? `${user.wallet_address.slice(0, 8)}...${user.wallet_address.slice(-6)}` : '')}</p>
                <p className="text-cyber-cyan text-xs mt-1 uppercase tracking-wider">ID: {user?.id?.slice(0, 8)}...</p>
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
          {!isGoogleUser && !isWalletOnlyUser && (
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
                    <p className="text-white font-mono text-xs sm:text-sm break-all">{user.wallet_address}</p>
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
  );
}
