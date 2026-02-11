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
      // Handle FastAPI validation errors (detail can be array or string)
      let message = "An error occurred";
      if (typeof error.detail === "string") {
        message = error.detail;
      } else if (Array.isArray(error.detail)) {
        // FastAPI validation errors are arrays of {loc, msg, type}
        message = error.detail.map((e) => e.msg || e.message).join(", ");
      } else if (error.detail) {
        message = JSON.stringify(error.detail);
      }
      throw new Error(message);
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

  async getAllCharacters() {
    const response = await fetch(`${API_BASE}/characters/all`, {
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

  // HP Management endpoints
  async updateHP(characterId, hpData) {
    const response = await fetch(`${API_BASE}/characters/${characterId}/hp`, {
      method: "PATCH",
      headers: this.getAuthHeaders(),
      body: JSON.stringify(hpData),
    });
    return this.handleResponse(response);
  }

  async applyDamageOrHealing(characterId, type, amount) {
    const response = await fetch(
      `${API_BASE}/characters/${characterId}/damage-healing`,
      {
        method: "POST",
        headers: this.getAuthHeaders(),
        body: JSON.stringify({ type, amount }),
      },
    );
    return this.handleResponse(response);
  }

  // Notes endpoints
  async getCampaignNotes(campaignId, noteType = null, tag = null) {
    let url = `${API_BASE}/notes/campaign/${campaignId}`;
    const params = new URLSearchParams();
    if (noteType) params.append("note_type", noteType);
    if (tag) params.append("tag", tag);
    if (params.toString()) url += `?${params.toString()}`;

    const response = await fetch(url, {
      headers: this.getAuthHeaders(),
    });
    return this.handleResponse(response);
  }

  async getMyNotes(noteType = null) {
    let url = `${API_BASE}/notes/`;
    if (noteType) url += `?note_type=${noteType}`;

    const response = await fetch(url, {
      headers: this.getAuthHeaders(),
    });
    return this.handleResponse(response);
  }

  async getNote(noteId) {
    const response = await fetch(`${API_BASE}/notes/${noteId}`, {
      headers: this.getAuthHeaders(),
    });
    return this.handleResponse(response);
  }

  async createNote(noteData) {
    const response = await fetch(`${API_BASE}/notes/`, {
      method: "POST",
      headers: this.getAuthHeaders(),
      body: JSON.stringify(noteData),
    });
    return this.handleResponse(response);
  }

  async updateNote(noteId, noteData) {
    const response = await fetch(`${API_BASE}/notes/${noteId}`, {
      method: "PUT",
      headers: this.getAuthHeaders(),
      body: JSON.stringify(noteData),
    });
    return this.handleResponse(response);
  }

  async deleteNote(noteId) {
    const response = await fetch(`${API_BASE}/notes/${noteId}`, {
      method: "DELETE",
      headers: this.getAuthHeaders(),
    });
    if (response.status === 204) {
      return { success: true };
    }
    return this.handleResponse(response);
  }

  // Maps endpoints
  async getCampaignMaps(campaignId) {
    const response = await fetch(`${API_BASE}/maps/campaign/${campaignId}`, {
      headers: this.getAuthHeaders(),
    });
    return this.handleResponse(response);
  }

  async getActiveMap(campaignId) {
    const response = await fetch(
      `${API_BASE}/maps/campaign/${campaignId}/active`,
      {
        headers: this.getAuthHeaders(),
      },
    );
    return this.handleResponse(response);
  }

  async getMap(mapId) {
    const response = await fetch(`${API_BASE}/maps/${mapId}`, {
      headers: this.getAuthHeaders(),
    });
    return this.handleResponse(response);
  }

  async createMap(mapData) {
    const response = await fetch(`${API_BASE}/maps/`, {
      method: "POST",
      headers: this.getAuthHeaders(),
      body: JSON.stringify(mapData),
    });
    return this.handleResponse(response);
  }

  async updateMap(mapId, mapData) {
    const response = await fetch(`${API_BASE}/maps/${mapId}`, {
      method: "PUT",
      headers: this.getAuthHeaders(),
      body: JSON.stringify(mapData),
    });
    return this.handleResponse(response);
  }

  async deleteMap(mapId) {
    const response = await fetch(`${API_BASE}/maps/${mapId}`, {
      method: "DELETE",
      headers: this.getAuthHeaders(),
    });
    if (response.status === 204) {
      return { success: true };
    }
    return this.handleResponse(response);
  }

  async activateMap(mapId) {
    const response = await fetch(`${API_BASE}/maps/${mapId}/activate`, {
      method: "POST",
      headers: this.getAuthHeaders(),
    });
    return this.handleResponse(response);
  }

  async updateMapTokens(mapId, tokens) {
    const response = await fetch(`${API_BASE}/maps/${mapId}/tokens`, {
      method: "PATCH",
      headers: this.getAuthHeaders(),
      body: JSON.stringify({ tokens }),
    });
    return this.handleResponse(response);
  }

  async moveToken(mapId, tokenId, x, y) {
    const response = await fetch(`${API_BASE}/maps/${mapId}/token/move`, {
      method: "PATCH",
      headers: this.getAuthHeaders(),
      body: JSON.stringify({ token_id: tokenId, x, y }),
    });
    return this.handleResponse(response);
  }

  async updateFog(mapId, revealedCells, action = "set") {
    const response = await fetch(`${API_BASE}/maps/${mapId}/fog`, {
      method: "PATCH",
      headers: this.getAuthHeaders(),
      body: JSON.stringify({ revealed_cells: revealedCells, action }),
    });
    return this.handleResponse(response);
  }
}

export default new ApiService();
