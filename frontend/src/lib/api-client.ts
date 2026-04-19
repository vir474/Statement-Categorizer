/**
 * Axios instance pre-configured with the backend base URL.
 * All API calls go through this so switching environments only requires changing VITE_API_URL.
 */
import axios from "axios";

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
  headers: { "Content-Type": "application/json" },
});

export default apiClient;
