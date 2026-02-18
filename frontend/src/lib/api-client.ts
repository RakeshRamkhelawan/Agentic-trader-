import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, InternalAxiosRequestConfig } from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8003';

/**
 * Standardized Axios API Client with JWT injection and Refresh logic
 */
export const apiClient: AxiosInstance = axios.create({
    baseURL: API_BASE_URL,
    timeout: 10000,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Flag to prevent multiple refresh calls
let isRefreshing = false;
let failedQueue: any[] = [];

const processQueue = (error: any, token: string | null = null) => {
    failedQueue.forEach((prom) => {
        if (error) {
            prom.reject(error);
        } else {
            prom.resolve(token);
        }
    });
    failedQueue = [];
};

// Request Interceptor: Inject JWT
apiClient.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
        const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
        if (token && config.headers) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// Response Interceptor: Handle errors and Token Refresh
apiClient.interceptors.response.use(
    (response: AxiosResponse) => response,
    async (error) => {
        const originalRequest = error.config;

        // If error is 401 and not a retry already
        if (error.response?.status === 401 && !originalRequest._retry) {
            if (isRefreshing) {
                return new Promise((resolve, reject) => {
                    failedQueue.push({ resolve, reject });
                })
                    .then((token) => {
                        originalRequest.headers.Authorization = `Bearer ${token}`;
                        return apiClient(originalRequest);
                    })
                    .catch((err) => Promise.reject(err));
            }

            originalRequest._retry = true;
            isRefreshing = true;

            const refreshToken = typeof window !== 'undefined' ? localStorage.getItem('refresh_token') : null;

            if (!refreshToken) {
                isRefreshing = false;
                // Redirect to login if needed or just reject
                return Promise.reject(error);
            }

            try {
                const response = await axios.post(`${API_BASE_URL}/api/v1/auth/refresh`, {
                    refresh_token: refreshToken,
                });

                const { access_token } = response.data;
                localStorage.setItem('access_token', access_token);
                
                apiClient.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
                processQueue(null, access_token);
                
                return apiClient(originalRequest);
            } catch (refreshError) {
                processQueue(refreshError, null);
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
                // Potential logout logic here
                return Promise.reject(refreshError);
            } finally {
                isRefreshing = false;
            }
        }

        // Standardized error handling
        const errorMessage = error.response?.data?.detail || error.message || 'An unexpected error occurred';
        return Promise.reject(new Error(errorMessage));
    }
);
