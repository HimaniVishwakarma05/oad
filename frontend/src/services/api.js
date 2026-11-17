/**
 * Centralized API client service for IIPS Attendance Management System
 */

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');
const TOKEN_KEY = 'iips_auth_token';
const USER_KEY = 'iips_auth_user';

export const authStorage = {
  getToken: () => localStorage.getItem(TOKEN_KEY),
  setToken: (token) => localStorage.setItem(TOKEN_KEY, token),
  removeToken: () => localStorage.removeItem(TOKEN_KEY),
  getUser: () => {
    try {
      const u = localStorage.getItem(USER_KEY);
      return u ? JSON.parse(u) : null;
    } catch {
      return null;
    }
  },
  setUser: (user) => localStorage.setItem(USER_KEY, JSON.stringify(user)),
  removeUser: () => localStorage.removeItem(USER_KEY),
  clear: () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  },
};

export async function apiRequest(endpoint, options = {}) {
  const { token = authStorage.getToken(), ...customOptions } = options;
  const isNetworkHost =
    typeof window !== 'undefined' &&
    window.location.origin &&
    window.location.hostname !== 'localhost' &&
    window.location.hostname !== '127.0.0.1';

  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(isNetworkHost ? { 'X-Frontend-Url': window.location.origin } : {}),
    ...customOptions.headers,
  };


  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...customOptions,
    headers,
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    let message = 'An unexpected error occurred';
    if (data?.detail) {
      if (Array.isArray(data.detail)) {
        message = data.detail.map((err) => `${err.loc?.slice(-1)[0] || 'Field'}: ${err.msg}`).join('. ');
      } else {
        message = data.detail;
      }
    } else if (response.status === 401) {
      message = 'Invalid email or password';
    } else if (response.status === 403) {
      message = 'Access forbidden: unauthorized action';
    } else if (response.status === 404) {
      message = 'Requested resource not found';
    } else if (response.status === 409) {
      message = 'A conflict occurred: record already exists';
    } else if (response.status >= 500) {
      message = 'Server error. Please ensure the backend is running on port 8000.';
    }
    const error = new Error(message);
    error.status = response.status;
    error.data = data;
    throw error;
  }

  return data;
}
