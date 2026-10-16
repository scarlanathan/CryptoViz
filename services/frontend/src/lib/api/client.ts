/**
 * Client API REST
 */

import axios, { AxiosInstance, AxiosError } from 'axios'
import { API_CONFIG } from './config'

class ApiClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: API_CONFIG.baseURL,
      timeout: API_CONFIG.timeout,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Intercepteur de requête
    this.client.interceptors.request.use(
      (config) => {
        // Ajouter un token d'authentification si disponible
        const token = this.getAuthToken()
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => {
        return Promise.reject(error)
      }
    )

    // Intercepteur de réponse
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        // Gestion centralisée des erreurs
        if (error.response) {
          switch (error.response.status) {
            case 401:
              console.error('Non autorisé - Token invalide ou expiré')
              break
            case 403:
              console.error('Accès interdit')
              break
            case 404:
              console.error('Ressource non trouvée')
              break
            case 500:
              console.error('Erreur serveur')
              break
            default:
              console.error('Erreur API:', error.message)
          }
        } else if (error.request) {
          console.error('Pas de réponse du serveur')
        } else {
          console.error('Erreur de configuration de la requête')
        }
        return Promise.reject(error)
      }
    )
  }

  private getAuthToken(): string | null {
    // Récupérer le token depuis localStorage ou autre
    if (typeof window !== 'undefined') {
      return localStorage.getItem('auth_token')
    }
    return null
  }

  async get<T>(url: string, params?: any): Promise<T> {
    const response = await this.client.get<T>(url, { params })
    return response.data
  }

  async post<T>(url: string, data?: any): Promise<T> {
    const response = await this.client.post<T>(url, data)
    return response.data
  }

  async put<T>(url: string, data?: any): Promise<T> {
    const response = await this.client.put<T>(url, data)
    return response.data
  }

  async delete<T>(url: string): Promise<T> {
    const response = await this.client.delete<T>(url)
    return response.data
  }
}

export const apiClient = new ApiClient()

