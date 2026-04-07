import { createContext, useContext, useState, useEffect } from "react";
import { authService, customerService } from "../services";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [customer, setCustomer] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const stored = localStorage.getItem("customer");
    const token = localStorage.getItem("access_token");
    if (stored && token) {
      setCustomer(JSON.parse(stored));
    } else {
      // Token missing — clear stale customer data
      localStorage.removeItem("customer");
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
    }
    setLoading(false);
  }, []);

  const login = async (username, password) => {
    try {
      // Step 1: Get JWT tokens from auth-service
      const authResponse = await authService.login({
        username,
        password,
        role: "customer",
      });
      const { access, refresh, user_id } = authResponse.data;

      // Store tokens immediately so subsequent requests are authenticated
      localStorage.setItem("access_token", access);
      localStorage.setItem("refresh_token", refresh);

      // Step 2: Fetch full customer profile
      const profileResponse = await customerService.getProfile(user_id);
      const customerData = profileResponse.data;

      setCustomer(customerData);
      localStorage.setItem("customer", JSON.stringify(customerData));
      return { success: true };
    } catch (error) {
      // Clean up on failure
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      return {
        success: false,
        error: error.response?.data?.error || "Đăng nhập thất bại",
      };
    }
  };

  const register = async (data) => {
    try {
      // Step 1: Register the customer
      const response = await customerService.register(data);
      const customerData = response.data;

      // Step 2: Auto-login to get JWT tokens
      const authResponse = await authService.login({
        username: data.username,
        password: data.password,
        role: "customer",
      });
      const { access, refresh } = authResponse.data;

      localStorage.setItem("access_token", access);
      localStorage.setItem("refresh_token", refresh);
      setCustomer(customerData);
      localStorage.setItem("customer", JSON.stringify(customerData));
      return { success: true };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data || "Đăng ký thất bại",
      };
    }
  };

  const logout = () => {
    const refreshToken = localStorage.getItem("refresh_token");
    if (refreshToken) {
      authService.logout(refreshToken).catch(() => {});
    }
    setCustomer(null);
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("customer");
  };

  const updateCustomer = (data) => {
    const updated = { ...customer, ...data };
    setCustomer(updated);
    localStorage.setItem("customer", JSON.stringify(updated));
  };

  return (
    <AuthContext.Provider
      value={{
        customer,
        loading,
        login,
        register,
        logout,
        updateCustomer,
        isAuthenticated: !!customer,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
