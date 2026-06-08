/** Lawny API Client */
const API = {
  base: '/api',

  async _fetch(path, options = {}) {
    const url = `${this.base}${path}`;
    const config = { headers: { 'Content-Type': 'application/json' }, ...options };
    try {
      const resp = await fetch(url, config);
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({ detail: resp.statusText }));
        throw new Error(err.detail || `HTTP ${resp.status}`);
      }
      return resp.json();
    } catch (e) {
      console.error(`API ${path}:`, e);
      throw e;
    }
  },

  // Dashboard
  getDashboard() { return this._fetch('/dashboard'); },

  // Lawn
  getLawn() { return this._fetch('/lawn'); },
  createLawn(data) { return this._fetch('/lawn', { method: 'POST', body: JSON.stringify(data) }); },
  updateLawn(data) { return this._fetch('/lawn', { method: 'PUT', body: JSON.stringify(data) }); },
  geocode(address) { return this._fetch('/lawn/geocode', { method: 'POST', body: JSON.stringify({ address }) }); },
  getGrassTypes() { return this._fetch('/lawn/grass-types'); },

  // Zones
  getZones() { return this._fetch('/zones'); },
  createZone(data) { return this._fetch('/zones', { method: 'POST', body: JSON.stringify(data) }); },
  updateZone(id, data) { return this._fetch(`/zones/${id}`, { method: 'PUT', body: JSON.stringify(data) }); },
  deleteZone(id) { return this._fetch(`/zones/${id}`, { method: 'DELETE' }); },

  // Activities
  getActivities(params = {}) {
    const qs = new URLSearchParams(params).toString();
    return this._fetch(`/activities${qs ? '?' + qs : ''}`);
  },
  createActivity(data) { return this._fetch('/activities', { method: 'POST', body: JSON.stringify(data) }); },
  updateActivity(id, data) { return this._fetch(`/activities/${id}`, { method: 'PUT', body: JSON.stringify(data) }); },
  deleteActivity(id) { return this._fetch(`/activities/${id}`, { method: 'DELETE' }); },
  getActivityTypes() { return this._fetch('/activities/types'); },
  getActivityStats() { return this._fetch('/activities/stats'); },

  // Schedules
  getSchedules() { return this._fetch('/schedules'); },
  createSchedule(data) { return this._fetch('/schedules', { method: 'POST', body: JSON.stringify(data) }); },
  updateSchedule(id, data) { return this._fetch(`/schedules/${id}`, { method: 'PUT', body: JSON.stringify(data) }); },
  deleteSchedule(id) { return this._fetch(`/schedules/${id}`, { method: 'DELETE' }); },
  completeSchedule(id) { return this._fetch(`/schedules/${id}/complete`, { method: 'POST' }); },
  getUpcoming(days = 14) { return this._fetch(`/schedules/upcoming?days=${days}`); },

  // Weather
  getCurrentWeather() { return this._fetch('/weather/current'); },
  getForecast(days = 7) { return this._fetch(`/weather/forecast?days=${days}`); },
  getWeatherHistory(days = 30) { return this._fetch(`/weather/history?days=${days}`); },
  getDroughtStatus() { return this._fetch('/weather/drought'); },
  getWateringRecommendation() { return this._fetch('/weather/watering'); },
  getHydrationBalance() { return this._fetch('/weather/hydration-balance'); },

  // Diagnosis
  async analyzeLawnPhoto(file, zoneId = null, aiProvider = null) {
    const formData = new FormData();
    formData.append('photo', file);
    if (zoneId) formData.append('zone_id', zoneId);
    if (aiProvider) formData.append('ai_provider', aiProvider);
    const resp = await fetch(`${this.base}/diagnosis/analyze`, { method: 'POST', body: formData });
    if (!resp.ok) throw new Error((await resp.json()).detail || 'Upload failed');
    return resp.json();
  },
  getDiagnosisHistory() { return this._fetch('/diagnosis/history'); },
  getDiagnosis(id) { return this._fetch(`/diagnosis/${id}`); },

  // Settings
  getSettings() { return this._fetch('/settings'); },
  updateAIProvider(provider) { return this._fetch('/settings/ai-provider', { method: 'PUT', body: JSON.stringify({ ai_provider: provider }) }); },
  updateAIConfig(data) { return this._fetch('/settings/ai-config', { method: 'PUT', body: JSON.stringify(data) }); },
  getAIModels(provider) { return this._fetch(`/ai/models?provider=${provider}`); },
  checkPinRequired() { return this._fetch('/settings/pin-check'); },
  verifyPin(pin) { return this._fetch('/settings/pin-verify', { method: 'POST', body: JSON.stringify({ pin }) }); },

  // Fertilizer Programs
  fertilizerPrograms() { return this._fetch('/fertilizer/programs'); },
  fertilizerProgramDetail(id) { return this._fetch(`/fertilizer/programs/${id}`); },
  fertilizerRefresh() { return this._fetch('/fertilizer/programs/refresh', { method: 'POST' }); },
  fertilizerAiRefresh(data = {}) { return this._fetch('/fertilizer/programs/ai-refresh', { method: 'POST', body: JSON.stringify(data) }); },
  fertilizerActive() { return this._fetch('/fertilizer/active'); },
  fertilizerActivate(programId) { return this._fetch('/fertilizer/active', { method: 'POST', body: JSON.stringify({ program_id: programId }) }); },
  fertilizerDeactivate() { return this._fetch('/fertilizer/active', { method: 'DELETE' }); },
  fertilizerApply(stepId, data) { return this._fetch(`/fertilizer/apply/${stepId}`, { method: 'POST', body: JSON.stringify(data) }); },
  fertilizerShoppingList() { return this._fetch('/fertilizer/shopping-list'); },
  fertilizerCreateCustom(data) { return this._fetch('/fertilizer/programs/custom', { method: 'POST', body: JSON.stringify(data) }); },
  fertilizerUpdateCustom(id, data) { return this._fetch(`/fertilizer/programs/custom/${id}`, { method: 'PUT', body: JSON.stringify(data) }); },
  fertilizerDeleteCustom(id) { return this._fetch(`/fertilizer/programs/custom/${id}`, { method: 'DELETE' }); },
  fertilizerAddStep(programId, data) { return this._fetch(`/fertilizer/programs/custom/${programId}/steps`, { method: 'POST', body: JSON.stringify(data) }); },
  fertilizerUpdateStep(programId, stepId, data) { return this._fetch(`/fertilizer/programs/custom/${programId}/steps/${stepId}`, { method: 'PUT', body: JSON.stringify(data) }); },
  fertilizerDeleteStep(programId, stepId) { return this._fetch(`/fertilizer/programs/custom/${programId}/steps/${stepId}`, { method: 'DELETE' }); },

  // Soil Tests
  getSoilTests(params = {}) {
    const qs = new URLSearchParams(params).toString();
    return this._fetch(`/soil-tests${qs ? '?' + qs : ''}`);
  },
  createSoilTest(data) { return this._fetch('/soil-tests', { method: 'POST', body: JSON.stringify(data) }); },
  getSoilTest(id) { return this._fetch(`/soil-tests/${id}`); },
  updateSoilTest(id, data) { return this._fetch(`/soil-tests/${id}`, { method: 'PUT', body: JSON.stringify(data) }); },
  deleteSoilTest(id) { return this._fetch(`/soil-tests/${id}`, { method: 'DELETE' }); },
  getLatestSoilTest() { return this._fetch('/soil-tests/latest'); },
  calculateAmendment(data) { return this._fetch('/soil-tests/calculate-amendment', { method: 'POST', body: JSON.stringify(data) }); },

  // Observations
  getObservations(params = {}) {
    const qs = new URLSearchParams(params).toString();
    return this._fetch(`/observations${qs ? '?' + qs : ''}`);
  },
  createObservation(data) { return this._fetch('/observations', { method: 'POST', body: JSON.stringify(data) }); },
  getObservation(id) { return this._fetch(`/observations/${id}`); },
  updateObservation(id, data) { return this._fetch(`/observations/${id}`, { method: 'PUT', body: JSON.stringify(data) }); },
  resolveObservation(id, data = {}) { return this._fetch(`/observations/${id}/resolve`, { method: 'POST', body: JSON.stringify(data) }); },
  deleteObservation(id) { return this._fetch(`/observations/${id}`, { method: 'DELETE' }); },
  getObservationTypes() { return this._fetch('/observations/types'); },

  // Products
  getProducts(params = {}) {
    const qs = new URLSearchParams(params).toString();
    return this._fetch(`/products${qs ? '?' + qs : ''}`);
  },
  getProduct(id) { return this._fetch(`/products/${id}`); },
  createProduct(data) { return this._fetch('/products', { method: 'POST', body: JSON.stringify(data) }); },
  getProductCategories() { return this._fetch('/products/categories'); },

  // Assessments
  getAssessments(limit = 20) { return this._fetch(`/assessments?limit=${limit}`); },
  createAssessment(data) { return this._fetch('/assessments', { method: 'POST', body: JSON.stringify(data) }); },
  getAssessment(id) { return this._fetch(`/assessments/${id}`); },
  updateAssessment(id, data) { return this._fetch(`/assessments/${id}`, { method: 'PUT', body: JSON.stringify(data) }); },
  deleteAssessment(id) { return this._fetch(`/assessments/${id}`, { method: 'DELETE' }); },
  addAssessmentFinding(id, data) { return this._fetch(`/assessments/${id}/findings`, { method: 'POST', body: JSON.stringify(data) }); },
  updateAssessmentFinding(id, fid, data) { return this._fetch(`/assessments/${id}/findings/${fid}`, { method: 'PUT', body: JSON.stringify(data) }); },
  deleteAssessmentFinding(id, fid) { return this._fetch(`/assessments/${id}/findings/${fid}`, { method: 'DELETE' }); },
  analyzeAssessment(id, data = {}) { return this._fetch(`/assessments/${id}/analyze`, { method: 'POST', body: JSON.stringify(data) }); },
  addAssessmentToProgram(id, data = {}) { return this._fetch(`/assessments/${id}/add-to-program`, { method: 'POST', body: JSON.stringify(data) }); },

  // Lawn Program
  getActiveProgram() { return this._fetch('/program/active'); },
  listPrograms() { return this._fetch('/program'); },
  createProgram(data) { return this._fetch('/program', { method: 'POST', body: JSON.stringify(data) }); },
  updateProgram(id, data) { return this._fetch(`/program/${id}`, { method: 'PUT', body: JSON.stringify(data) }); },
  deleteProgram(id) { return this._fetch(`/program/${id}`, { method: 'DELETE' }); },
  generateProgram(data = {}) { return this._fetch('/program/generate', { method: 'POST', body: JSON.stringify(data) }); },
  addProgramStep(id, data) { return this._fetch(`/program/${id}/steps`, { method: 'POST', body: JSON.stringify(data) }); },
  updateProgramStep(id, stepId, data) { return this._fetch(`/program/${id}/steps/${stepId}`, { method: 'PUT', body: JSON.stringify(data) }); },
  completeProgramStep(id, stepId) { return this._fetch(`/program/${id}/steps/${stepId}/complete`, { method: 'POST' }); },
  deleteProgramStep(id, stepId) { return this._fetch(`/program/${id}/steps/${stepId}`, { method: 'DELETE' }); },

  // Timeline
  getTimeline(params = {}) {
    const qs = new URLSearchParams(params).toString();
    return this._fetch(`/timeline${qs ? '?' + qs : ''}`);
  },

  // AI Consultation
  aiConsult(data) { return this._fetch('/ai/consult', { method: 'POST', body: JSON.stringify(data) }); },
  getConsultationHistory(limit = 20) { return this._fetch(`/ai/consultations?limit=${limit}`); },
  getConsultation(id) { return this._fetch(`/ai/consultations/${id}`); },
  getSeasonalAlerts() { return this._fetch('/ai/seasonal-alerts'); },
  getAIProviders() { return this._fetch('/ai/providers'); },
};
