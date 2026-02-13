import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_API || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('authToken');
  if (token) {
    config.headers.Authorization = `Token ${token}`;
  }
  return config;
});

// Handle errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('authToken');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// API functions
export const API = {
  // Users
  users: {
    register: (data: any) => apiClient.post('/users/register', data),
    getProfile: () => apiClient.get('/users/me'),
    updateProfile: (data: any) => apiClient.put('/users/update_profile', data),
    registerAsOperator: (data: any) => apiClient.post('/users/operators/register_as_operator', data),
  },

  // Buses
  buses: {
    list: (params?: any) => apiClient.get('/buses/', { params }),
    search: (data: any) => apiClient.post('/buses/search', data),
    get: (id: number) => apiClient.get(`/buses/${id}`),
    create: (data: any) => apiClient.post('/buses/', data),
    update: (id: number, data: any) => apiClient.put(`/buses/${id}`, data),
    myBuses: () => apiClient.get('/buses/my_buses'),
    addPhotos: (busId: number, data: any) => apiClient.post(`/buses/${busId}/photos/`, data),
    addAmenities: (busId: number, data: any) => apiClient.post(`/buses/${busId}/amenities/`, data),
  },

  // Bookings
  bookings: {
    create: (data: any) => apiClient.post('/bookings/create_booking', data),
    list: () => apiClient.get('/bookings/my_bookings'),
    get: (id: number) => apiClient.get(`/bookings/${id}`),
    cancel: (id: number, data: any) => apiClient.post(`/bookings/${id}/cancel`, data),
    getHistory: (id: number) => apiClient.get(`/bookings/${id}/history`),
  },

  // Payments
  payments: {
    initiate: (data: any) => apiClient.post('/bookings/payments/initiate_payment', data),
    confirm: (id: number, data: any) => apiClient.post(`/bookings/payments/${id}/confirm_payment`, data),
  },

  // Reviews
  reviews: {
    createBusReview: (data: any) => apiClient.post('/reviews/bus/create_review', data),
    getBusReviews: (busId: number) => apiClient.get('/reviews/bus/bus_reviews', { params: { bus_id: busId } }),
    createOperatorReview: (data: any) => apiClient.post('/reviews/operator/create_review', data),
    getOperatorReviews: (operatorId: number) => apiClient.get('/reviews/operator/operator_reviews', { params: { operator_id: operatorId } }),
  },
};
