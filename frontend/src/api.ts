const API =
  import.meta.env.VITE_API_BASE_URL ||
  'http://localhost:8000/api/v1';

const get = async (p: string) => {
  const token = sessionStorage.getItem('trinetra-access-token');
  const r = await fetch(API + p, {
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  });

  if (!r.ok) {
    throw Error(String(r.status));
  }

  return r.json();
};

const post = async (p: string, body: unknown) => {
  const token = sessionStorage.getItem('trinetra-access-token');
  const r = await fetch(API + p, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(body),
  });

  if (!r.ok) {
    const errorText = await r.text();
    throw Error(errorText || String(r.status));
  }

  return r.json();
};

const uploadVideo = async (cameraId: number, video: File) => {
  const body = new FormData();
  body.append('camera_id', String(cameraId));
  body.append('video', video);
  const response = await fetch(API + '/cameras/video/analyze', {
    method: 'POST',
    headers: sessionStorage.getItem('trinetra-access-token')
      ? { Authorization: `Bearer ${sessionStorage.getItem('trinetra-access-token')}` }
      : undefined,
    body,
  });
  if (!response.ok) {
    throw Error((await response.text()) || String(response.status));
  }
  return response.json();
};

export const api = {
  login: (operatorId: string, accessKey: string) =>
    post('/auth/login', {
      operator_id: operatorId,
      access_key: accessKey,
    }),
  // Cameras
  cameras: () => get('/cameras'),
  analyzeVideo: uploadVideo,

  // ANPR / vehicle events
  events: () => get('/vehicles/events'),

  // Traffic analytics
  analytics: () => get('/analytics/summary'),

  // Alerts
  alerts: () => get('/alerts'),

  blacklist: () => get('/vehicles/blacklist'),
  addToBlacklist: (plate_number: string, reason: string) =>
    post('/vehicles/blacklist', { plate_number, reason }),
  removeFromBlacklist: (plate_number: string) =>
    fetch(`${API}/vehicles/blacklist/${encodeURIComponent(plate_number)}`, {
      method: 'DELETE',
      headers: sessionStorage.getItem('trinetra-access-token')
        ? { Authorization: `Bearer ${sessionStorage.getItem('trinetra-access-token')}` }
        : undefined,
    }).then(async (response) => {
      if (!response.ok) {
        throw Error((await response.text()) || String(response.status));
      }
      return response.json();
    }),

  // Vehicle trajectory
  trajectory: (plate: string) =>
    get(`/vehicles/${encodeURIComponent(plate)}/trajectory`),

  // E-Challan
  challan: (data: {
    plate_number: string;
    violation_code: string;
    location: string;
    evidence_url?: string;
  }) =>
    post('/enforcement/challan', data),
};