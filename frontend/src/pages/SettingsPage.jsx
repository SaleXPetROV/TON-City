import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  Building2, ArrowLeft, User, Mail, Lock, Wallet, 
  Camera, Save, Globe, Shield 
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { languages } from '@/lib/translations';
import { toast } from 'sonner';

export default function SettingsPage() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lang, setLang] = useState(localStorage.getItem('ton_city_lang') || 'ru');

  // Form states
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [newPasswordConfirm, setNewPasswordConfirm] = useState('');
  const [walletAddress, setWalletAddress] = useState('');

  const [saving, setSaving] = useState(false);

  useEffect(() => {
    checkAuth();
  }, []);

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
        setWalletAddress(userData.wallet_address || '');
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
      toast.error(lang === 'ru' ? 'Username слишком короткий' : 'Username too short');
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

      toast.success(lang === 'ru' ? 'Username обновлен!' : 'Username updated!');
      checkAuth(); // Refresh user data
    } catch (error) {
      toast.error(error.message);
    } finally {
      setSaving(false);
    }
  };

  const handleUpdateEmail = async () => {
    if (!email.trim()) {
      toast.error(lang === 'ru' ? 'Введите email' : 'Enter email');
      return;
    }
    if (!currentPassword) {
      toast.error(lang === 'ru' ? 'Введите текущий пароль' : 'Enter current password');
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

      toast.success(lang === 'ru' ? 'Email обновлен!' : 'Email updated!');
      setCurrentPassword('');
      checkAuth();
    } catch (error) {
      toast.error(error.message);
    } finally {
      setSaving(false);
    }
  };

  const handleUpdatePassword = async () => {
    if (!currentPassword || !newPassword) {
      toast.error(lang === 'ru' ? 'Заполните все поля' : 'Fill all fields');
      return;
    }
    if (newPassword !== newPasswordConfirm) {
      toast.error(lang === 'ru' ? 'Пароли не совпадают' : 'Passwords do not match');
      return;
    }
    if (newPassword.length < 6) {
      toast.error(lang === 'ru' ? 'Пароль слишком короткий' : 'Password too short');
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

      toast.success(lang === 'ru' ? 'Пароль обновлен!' : 'Password updated!');
      setCurrentPassword('');
      setNewPassword('');
      setNewPasswordConfirm('');
    } catch (error) {
      toast.error(error.message);
    } finally {
      setSaving(false);
    }
  };

  const handleLinkWallet = async () => {
    if (!walletAddress.trim()) {
      toast.error(lang === 'ru' ? 'Введите адрес кошелька' : 'Enter wallet address');
      return;
    }

    setSaving(true);
    try {
      const token = localStorage.getItem('token');
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

      toast.success(lang === 'ru' ? 'Кошелек привязан!' : 'Wallet linked!');
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

    // Convert to base64
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

        toast.success(lang === 'ru' ? 'Аватар обновлен!' : 'Avatar updated!');
        checkAuth();
      } catch (error) {
        toast.error(error.message);
      } finally {
        setSaving(false);
      }
    };
    reader.readAsDataURL(file);
  };

  const changeLang = (newLang) => {
    setLang(newLang);
    localStorage.setItem('ton_city_lang', newLang);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-void flex items-center justify-center font-rajdhani">
        <div className="text-cyber-cyan animate-pulse">
          {lang === 'ru' ? 'Загрузка...' : 'Loading...'}
        </div>
      </div>
    );
  }

  const isGoogleUser = user && !user.hashed_password;

  return (
    <div className="min-h-screen bg-void relative overflow-hidden font-rajdhani">
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
      <div className="relative z-10 container mx-auto px-6 py-6">
        <div className="flex items-center justify-between">
          <button 
            onClick={() => navigate('/')}
            className="flex items-center gap-3 text-white hover:text-cyber-cyan transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
            <span className="font-unbounded text-sm font-bold uppercase tracking-wider">
              {lang === 'ru' ? 'Назад' : 'Back'}
            </span>
          </button>

          <Select value={lang} onValueChange={changeLang}>
            <SelectTrigger className="w-28 bg-panel border-grid-border text-text-main">
              <Globe className="w-4 h-4 mr-2" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="en">EN</SelectItem>
              <SelectItem value="ru">RU</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Main Content */}
      <div className="relative z-10 container mx-auto px-6 py-12 max-w-4xl">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-8"
        >
          <div className="text-center mb-12">
            <h1 className="font-unbounded text-3xl font-bold text-white mb-2 uppercase tracking-tight">
              {lang === 'ru' ? 'Настройки' : 'Settings'}
            </h1>
            <p className="text-text-muted">
              {lang === 'ru' ? 'Управление аккаунтом' : 'Manage your account'}
            </p>
          </div>

          {/* Avatar Section */}
          <div className="glass-panel rounded-2xl p-8 border border-white/10">
            <div className="flex items-center gap-6">
              <div className="relative">
                {user?.avatar ? (
                  <img 
                    src={user.avatar} 
                    alt="Avatar"
                    className="w-24 h-24 rounded-full border-2 border-cyber-cyan"
                  />
                ) : (
                  <div className="w-24 h-24 bg-gradient-to-br from-cyber-cyan to-neon-purple rounded-full flex items-center justify-center text-3xl font-bold text-black">
                    {(user?.username || 'U')[0].toUpperCase()}
                  </div>
                )}
                <label className="absolute bottom-0 right-0 bg-cyber-cyan text-black p-2 rounded-full cursor-pointer hover:brightness-110 transition-all">
                  <Camera className="w-4 h-4" />
                  <input type="file" accept="image/*" className="hidden" onChange={handleAvatarUpload} />
                </label>
              </div>
              <div>
                <h3 className="text-xl font-bold text-white">{user?.display_name || user?.username}</h3>
                <p className="text-text-muted text-sm">{user?.email}</p>
              </div>
            </div>
          </div>

          {/* Username */}
          <div className="glass-panel rounded-2xl p-8 border border-white/10">
            <div className="flex items-center gap-2 mb-4">
              <User className="w-5 h-5 text-cyber-cyan" />
              <h3 className="text-lg font-bold text-white uppercase tracking-wide">
                {lang === 'ru' ? 'Никнейм' : 'Username'}
              </h3>
            </div>
            <div className="space-y-4">
              <input 
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Username"
                className="w-full bg-white/5 border border-white/10 p-3 rounded-xl text-white outline-none focus:border-cyber-cyan transition-all"
              />
              <Button 
                onClick={handleUpdateUsername}
                disabled={saving}
                className="bg-cyber-cyan text-black hover:brightness-110">
                <Save className="w-4 h-4 mr-2" />
                {lang === 'ru' ? 'Сохранить' : 'Save'}
              </Button>
            </div>
          </div>

          {/* Email (only for email users, not Google) */}
          {!isGoogleUser && (
            <div className="glass-panel rounded-2xl p-8 border border-white/10">
              <div className="flex items-center gap-2 mb-4">
                <Mail className="w-5 h-5 text-cyber-cyan" />
                <h3 className="text-lg font-bold text-white uppercase tracking-wide">Email</h3>
              </div>
              <div className="space-y-4">
                <input 
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Email"
                  className="w-full bg-white/5 border border-white/10 p-3 rounded-xl text-white outline-none focus:border-cyber-cyan transition-all"
                />
                <input 
                  type="password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  placeholder={lang === 'ru' ? 'Текущий пароль для подтверждения' : 'Current password to confirm'}
                  className="w-full bg-white/5 border border-white/10 p-3 rounded-xl text-white outline-none focus:border-cyber-cyan transition-all"
                />
                <Button 
                  onClick={handleUpdateEmail}
                  disabled={saving}
                  className="bg-cyber-cyan text-black hover:brightness-110">
                  <Save className="w-4 h-4 mr-2" />
                  {lang === 'ru' ? 'Обновить Email' : 'Update Email'}
                </Button>
              </div>
            </div>
          )}

          {/* Password (only for email users, not Google) */}
          {!isGoogleUser && (
            <div className="glass-panel rounded-2xl p-8 border border-white/10">
              <div className="flex items-center gap-2 mb-4">
                <Lock className="w-5 h-5 text-cyber-cyan" />
                <h3 className="text-lg font-bold text-white uppercase tracking-wide">
                  {lang === 'ru' ? 'Пароль' : 'Password'}
                </h3>
              </div>
              <div className="space-y-4">
                <input 
                  type="password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  placeholder={lang === 'ru' ? 'Текущий пароль' : 'Current password'}
                  className="w-full bg-white/5 border border-white/10 p-3 rounded-xl text-white outline-none focus:border-cyber-cyan transition-all"
                />
                <input 
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder={lang === 'ru' ? 'Новый пароль' : 'New password'}
                  className="w-full bg-white/5 border border-white/10 p-3 rounded-xl text-white outline-none focus:border-cyber-cyan transition-all"
                />
                <input 
                  type="password"
                  value={newPasswordConfirm}
                  onChange={(e) => setNewPasswordConfirm(e.target.value)}
                  placeholder={lang === 'ru' ? 'Подтвердите новый пароль' : 'Confirm new password'}
                  className="w-full bg-white/5 border border-white/10 p-3 rounded-xl text-white outline-none focus:border-cyber-cyan transition-all"
                />
                <Button 
                  onClick={handleUpdatePassword}
                  disabled={saving}
                  className="bg-cyber-cyan text-black hover:brightness-110">
                  <Save className="w-4 h-4 mr-2" />
                  {lang === 'ru' ? 'Изменить пароль' : 'Change Password'}
                </Button>
              </div>
            </div>
          )}

          {/* Wallet */}
          <div className="glass-panel rounded-2xl p-8 border border-white/10">
            <div className="flex items-center gap-2 mb-4">
              <Wallet className="w-5 h-5 text-cyber-cyan" />
              <h3 className="text-lg font-bold text-white uppercase tracking-wide">
                {lang === 'ru' ? 'TON Кошелек' : 'TON Wallet'}
              </h3>
            </div>
            <div className="space-y-4">
              {user?.wallet_address ? (
                <div className="bg-white/5 border border-cyber-cyan/20 p-4 rounded-xl">
                  <p className="text-xs text-text-muted mb-1 uppercase tracking-wider">
                    {lang === 'ru' ? 'Привязанный кошелек' : 'Linked Wallet'}
                  </p>
                  <p className="text-white font-mono text-sm break-all">{user.wallet_address}</p>
                </div>
              ) : (
                <>
                  <input 
                    type="text"
                    value={walletAddress}
                    onChange={(e) => setWalletAddress(e.target.value)}
                    placeholder="EQ..."
                    className="w-full bg-white/5 border border-white/10 p-3 rounded-xl text-white outline-none focus:border-cyber-cyan transition-all font-mono"
                  />
                  <Button 
                    onClick={handleLinkWallet}
                    disabled={saving}
                    className="bg-cyber-cyan text-black hover:brightness-110">
                    <Wallet className="w-4 h-4 mr-2" />
                    {lang === 'ru' ? 'Привязать кошелек' : 'Link Wallet'}
                  </Button>
                </>
              )}
            </div>
          </div>

          {/* Account Info */}
          {isGoogleUser && (
            <div className="glass-panel rounded-2xl p-6 border border-neon-purple/20 bg-neon-purple/5">
              <div className="flex items-start gap-3">
                <Shield className="w-5 h-5 text-neon-purple mt-1" />
                <div>
                  <h4 className="text-white font-bold mb-1">
                    {lang === 'ru' ? 'Google Аккаунт' : 'Google Account'}
                  </h4>
                  <p className="text-text-muted text-sm">
                    {lang === 'ru' 
                      ? 'Вы вошли через Google. Email и пароль управляются через ваш Google аккаунт.'
                      : 'You signed in with Google. Email and password are managed through your Google account.'}
                  </p>
                </div>
              </div>
            </div>
          )}
        </motion.div>
      </div>
    </div>
  );
}
