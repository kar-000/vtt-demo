const API_BASE = "http://localhost:8000/api/v1";

class ApiService {
  constructor() {
    this.token = localStorage.getItem("token");
  }

  setToken(token) {
    this.token = token;
    if (token) {
      localStorage.setItem("token", token);
    } else {
      localStorage.removeItem("token");
    }
  }

  getAuthHeaders() {
    // Always get fresh token from localStorage to ensure we have the latest
    const token = localStorage.getItem("token");
    console.log(
      "[API] getAuthHeaders called, token:",
      token ? `${token.substring(0, 20)}...` : "null",
    );
    const headers = {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };
    console.log("[API] Returning headers:", headers);
    return headers;
  }

  async handleResponse(response) {
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || "An error occurred");
    }
    return response.json();
  }

  // Auth endpoints
  async register(username, email, password, isDm = false) {
    const response = await fetch(`${API_BASE}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, email, password, is_dm: isDm }),
    });
    const data = await this.handleResponse(response);
    this.setToken(data.access_token);
    return data;
  }

  async login(username, password) {
    const response = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    const data = await this.handleResponse(response);
    this.setToken(data.access_token);
    return data;
  }

  async getCurrentUser() {
    const response = await fetch(`${API_BASE}/auth/me`, {
      headers: this.getAuthHeaders(),
    });
    return this.handleResponse(response);
  }

  logout() {
    this.setToken(null);
  }

  // Character endpoints
  async getCharacters() {
    const response = await fetch(`${API_BASE}/characters/`, {
      headers: this.getAuthHeaders(),
    });
    return this.handleResponse(response);
  }

  async getCharacter(id) {
    const response = await fetch(`${API_BASE}/characters/${id}`, {
      headers: this.getAuthHeaders(),
    });
    return this.handleResponse(response);
  }

  async createCharacter(characterData) {
    const response = await fetch(`${API_BASE}/characters/`, {
      method: "POST",
      headers: this.getAuthHeaders(),
      body: JSON.stringify(characterData),
    });
    return this.handleResponse(response);
  }

  async updateCharacter(id, characterData) {
    const response = await fetch(`${API_BASE}/characters/${id}`, {
      method: "PUT",
      headers: this.getAuthHeaders(),
      body: JSON.stringify(characterData),
    });
    return this.handleResponse(response);
  }

  async deleteCharacter(id) {
    const response = await fetch(`${API_BASE}/characters/${id}`, {
      method: "DELETE",
      headers: this.getAuthHeaders(),
    });
    if (response.status === 204) {
      return { success: true };
    }
    return this.handleResponse(response);
  }
}

export default new ApiService();
