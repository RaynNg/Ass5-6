import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
})

// Request interceptor - attach JWT Bearer token
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('access_token')
        if (token) {
            config.headers['Authorization'] = `Bearer ${token}`
        }
        return config
    },
    (error) => Promise.reject(error)
)

// Response interceptor - auto refresh token on 401
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config

        // If 401 and we haven't retried yet, try refreshing the token
        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true

            const refreshToken = localStorage.getItem('refresh_token')
            if (refreshToken) {
                try {
                    const response = await axios.post(
                        `${API_BASE_URL}/auth/auth/token/refresh/`,
                        { refresh: refreshToken }
                    )
                    const { access } = response.data
                    localStorage.setItem('access_token', access)
                    originalRequest.headers['Authorization'] = `Bearer ${access}`
                    return api(originalRequest)
                } catch {
                    // Refresh failed — clear tokens and redirect to login
                }
            }

            localStorage.removeItem('access_token')
            localStorage.removeItem('refresh_token')
            localStorage.removeItem('customer')
            window.location.href = '/login'
        }
        return Promise.reject(error)
    }
)

export default api
