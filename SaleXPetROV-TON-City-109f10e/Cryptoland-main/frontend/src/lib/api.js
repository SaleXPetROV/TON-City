import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API_URL = `${BACKEND_URL}/api`;

// Create axios instance
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('ton_city_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('ton_city_token');
      // Don't redirect, let the app handle it
    }
    return Promise.reject(error);
  }
);

// Auth
export const verifyWallet = async (address, proof = null, language = 'en') => {
  const response = await api.post('/auth/verify-wallet', {
    address,
    proof,
    language,
  });
  if (response.data.token) {
    localStorage.setItem('ton_city_token', response.data.token);
  }
  return response.data;
};

export const getCurrentUser = async () => {
  const response = await api.get('/auth/me');
  return response.data;
};

// Plots
export const getAllPlots = async () => {
  const response = await api.get('/plots');
  return response.data;
};

export const getPlotByCoords = async (x, y) => {
  const response = await api.get(`/plots/coords/${x}/${y}`);
  return response.data;
};

export const purchasePlot = async (x, y) => {
  const response = await api.post('/plots/purchase', {
    plot_x: x,
    plot_y: y,
  });
  return response.data;
};

export const confirmPlotPurchase = async (transactionId, blockchainHash = null) => {
  const response = await api.post('/plots/confirm-purchase', {
    transaction_id: transactionId,
    blockchain_hash: blockchainHash,
  });
  return response.data;
};

// Businesses
export const getBusinessTypes = async () => {
  const response = await api.get('/businesses/types');
  return response.data;
};

export const getAllBusinesses = async () => {
  const response = await api.get('/businesses');
  return response.data;
};

export const buildBusiness = async (plotId, businessType) => {
  const response = await api.post('/businesses/build', {
    plot_id: plotId,
    business_type: businessType,
  });
  return response.data;
};

export const confirmBusinessBuild = async (transactionId, blockchainHash = null) => {
  const response = await api.post('/businesses/confirm-build', {
    transaction_id: transactionId,
    blockchain_hash: blockchainHash,
  });
  return response.data;
};

// Transactions
export const getTransactions = async () => {
  const response = await api.get('/transactions');
  return response.data;
};

export const getTransaction = async (txId) => {
  const response = await api.get(`/transactions/${txId}`);
  return response.data;
};

// Stats
export const getGameStats = async () => {
  const response = await api.get('/stats');
  return response.data;
};

export const getLeaderboard = async () => {
  const response = await api.get('/leaderboard');
  return response.data;
};

// Utils
export const tonToNano = (ton) => Math.floor(ton * 1e9).toString();
export const nanoToTon = (nano) => Number(nano) / 1e9;

export default api;
