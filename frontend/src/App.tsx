import { useEffect, useRef, useState } from 'react';
import type { FormEvent } from 'react';
import {
  MapContainer,
  TileLayer,
  CircleMarker,
  Marker,
  Polyline,
  Popup,
  useMap,
} from 'react-leaflet';
import { divIcon } from 'leaflet';
import { api } from './api';

const menu = [
  'Dashboard',
  'Live Tracking',
  'Video ANPR',
  'ANPR Events',
  'Traffic Analytics',
  'Alerts',
  'Blacklist',
  'E-Challan',
  'Settings',
];

function routeArrowIcon(angle: number, label: string) {
  return divIcon({
    className: 'route-direction-marker',
    html: `<span class="route-arrow" style="transform: rotate(${angle}deg)">➤</span><span class="route-label">${label}</span>`,
    iconSize: [30, 30],
    iconAnchor: [15, 15],
  });
}

function MapViewport({ center }: { center?: [number, number] }) {
  const map = useMap();

  useEffect(() => {
    if (center) {
      map.setView(center, 13);
    }
  }, [center, map]);

  return null;
}

function MapView({ cameras, route, center }: any) {
  const [roadRoute, setRoadRoute] = useState(route);
  const routeKey = JSON.stringify(route || []);

  useEffect(() => {
    setRoadRoute(route);

    if (!route || route.length < 2) {
      return;
    }

    const coordinates = route
      .map(([latitude, longitude]: [number, number]) => `${longitude},${latitude}`)
      .join(';');
    const routeUrl = `https://router.project-osrm.org/route/v1/driving/${coordinates}?overview=full&geometries=geojson`;

    fetch(routeUrl)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Routing request failed: ${response.status}`);
        }
        return response.json();
      })
      .then((data) => {
        const geometry = data.routes?.[0]?.geometry?.coordinates;
        if (geometry?.length > 1) {
          setRoadRoute(geometry.map(([longitude, latitude]: [number, number]) => [latitude, longitude]));
        }
      })
      .catch(() => {
        // Keep the direct trajectory when the road routing service is unavailable.
      });
  }, [routeKey]);

  return (
    <div className="map">
      <MapContainer
        center={center || [25.435, 81.852]}
        zoom={13}
        style={{ height: '100%', width: '100%' }}
      >
        <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        <MapViewport center={center} />

        {cameras.map((c: any) => (
          <CircleMarker
            key={c.id}
            center={[c.latitude, c.longitude]}
            radius={8}
            pathOptions={{ color: '#31d7a0' }}
          >
            <Popup>
              <b>{c.name}</b>
              <br />
              Status: {c.status}
            </Popup>
          </CircleMarker>
        ))}

        {roadRoute?.length > 1 && (
          <Polyline
            positions={roadRoute}
            pathOptions={{
              color: '#6ea8fe',
              weight: 5,
            }}
          />
        )}

        {roadRoute?.length > 1 && (
          <>
            <Marker
              position={roadRoute[0]}
              icon={routeArrowIcon(0, 'START')}
            />
            {roadRoute.slice(1, -1).map((point: [number, number], index: number) => {
              const arrowStep = Math.max(1, Math.ceil((roadRoute.length - 2) / 12));
              if (index % arrowStep !== 0) {
                return null;
              }

              const previousPoint = roadRoute[index];
              const latitudeDelta = point[0] - previousPoint[0];
              const longitudeDelta = point[1] - previousPoint[1];
              const angle = Math.atan2(longitudeDelta, latitudeDelta) * (180 / Math.PI);

              return (
                <Marker
                  key={`direction-${point[0]}-${point[1]}-${index}`}
                  position={point}
                  icon={routeArrowIcon(angle, '')}
                />
              );
            })}
            <Marker
              position={roadRoute[roadRoute.length - 1]}
              icon={routeArrowIcon(0, 'LATEST')}
            />
          </>
        )}
      </MapContainer>
    </div>
  );
}

export default function App() {
  const [page, setPage] = useState('Dashboard');
  const [globalSearch, setGlobalSearch] = useState('');
  const [selectedCity, setSelectedCity] = useState('');
  const [cities, setCities] = useState<string[]>([]);
  const [cityDataLoading, setCityDataLoading] = useState(false);
  const [cityDataError, setCityDataError] = useState('');

  const [authenticated, setAuthenticated] = useState(
    () => sessionStorage.getItem('trinetra-authenticated') === 'true'
      && Boolean(sessionStorage.getItem('trinetra-access-token'))
  );
  const [loginId, setLoginId] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [loginError, setLoginError] = useState('');

  const [theme, setTheme] = useState<'dark' | 'light'>(() => {
    const savedTheme = localStorage.getItem('trinetra-theme');

    return savedTheme === 'light' ? 'light' : 'dark';
  });

  const [trackingPlate, setTrackingPlate] =
    useState('UP32AB5698');

  const [trackingLoading, setTrackingLoading] =
    useState(false);
  const [intelligenceLoading, setIntelligenceLoading] = useState(false);
  const [intelligenceError, setIntelligenceError] = useState('');
  const [vehicleIntelligence, setVehicleIntelligence] = useState<any>(null);

  const [d, setD] = useState<any>({
    cameras: [],
    events: [],
    analytics: {},
    alerts: [],
    trajectory: null,
  });

  const [wsStatus, setWsStatus] = useState('CONNECTING');

  const [liveAlert, setLiveAlert] = useState<any>(null);

  const [videoCameraId, setVideoCameraId] = useState('');
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [videoLoading, setVideoLoading] = useState(false);
  const [videoResult, setVideoResult] = useState<any>(null);
  const [videoError, setVideoError] = useState('');
  const [blacklistPlate, setBlacklistPlate] = useState('');
  const [blacklistReason, setBlacklistReason] = useState('Manual review');
  const [blacklistLoading, setBlacklistLoading] = useState(false);
  const [blacklistMessage, setBlacklistMessage] = useState('');
  const [copilotOpen, setCopilotOpen] = useState(false);
  const [copilotInput, setCopilotInput] = useState('');
  const [copilotLoading, setCopilotLoading] = useState(false);
  const [copilotMessages, setCopilotMessages] = useState<any[]>([
    {
      role: 'assistant',
      content: 'Namaste. I can help with vehicle history, detections, camera timeline, and blacklist checks using authorized database records only.',
      time: new Date().toISOString(),
    },
  ]);
  const [copilotFailedMessage, setCopilotFailedMessage] = useState('');
  const copilotMessagesRef = useRef<HTMLDivElement | null>(null);

  /* =====================================================
     THEME
  ===================================================== */

  useEffect(() => {
    localStorage.setItem('trinetra-theme', theme);

    document.documentElement.setAttribute(
      'data-theme',
      theme
    );
  }, [theme]);

  useEffect(() => {
    copilotMessagesRef.current?.scrollTo({
      top: copilotMessagesRef.current.scrollHeight,
      behavior: 'smooth',
    });
  }, [copilotMessages, copilotLoading]);

  /* =====================================================
     INITIAL API DATA
  ===================================================== */

  useEffect(() => {
    if (!authenticated) {
      return;
    }

    Promise.all([
      api.cities(),
    ])
      .then(([cityResponse]) => {
        setCities(cityResponse.cities || []);
      })
      .catch((error) => console.error('City list loading failed:', error));
  }, [authenticated]);

  useEffect(() => {
    if (!authenticated) {
      return;
    }

    const city = selectedCity || undefined;
    setCityDataLoading(true);
    setCityDataError('');
    Promise.all([
      api.cameras(city),
      api.events(city),
      api.analytics(city),
      api.alerts(city),
      api.trajectory('UP32AB5698', city),
      api.blacklist(),
    ])
      .then(
        ([
          cameras,
          events,
          analytics,
          alerts,
          trajectory,
          blacklist,
        ]) => {
          setD({
            cameras,
            events,
            analytics,
            alerts,
            trajectory,
            blacklist,
          });
        }
      )
      .catch((error) => {
        setD((previous: any) => ({ ...previous, cameras: [], events: [], analytics: {}, alerts: [], trajectory: null }));
        setCityDataError(error.message || 'City data could not be loaded.');
        console.error(
          'Initial API loading failed:',
          error
        );
      })
      .finally(() => setCityDataLoading(false));
  }, [authenticated, selectedCity]);

  /* =====================================================
     REAL-TIME WEBSOCKET
  ===================================================== */

  useEffect(() => {
    if (!authenticated) {
      return;
    }

    const wsUrl =
      import.meta.env.VITE_WS_URL ||
      'ws://localhost:8000/ws/events';

    let socket: WebSocket | null = null;
    let reconnectTimer: number | undefined;
    let stopped = false;

    const connect = () => {
      if (stopped) {
        return;
      }

      setWsStatus('CONNECTING');
      socket = new WebSocket(wsUrl);

      socket.onopen = () => {
        setWsStatus('CONNECTED');
        socket?.send(selectedCity ? `CITY:${selectedCity}` : 'HQ_CONNECTED');
      };

      socket.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          const incomingAlert = message.alert || message;

          if (message.type === 'alert' || incomingAlert.title) {
            setD((previous: any) => {
              if (previous.alerts.some((a: any) => a.id === incomingAlert.id)) {
                return previous;
              }

              return {
                ...previous,
                alerts: [incomingAlert, ...previous.alerts],
              };
            });

            setLiveAlert(incomingAlert);
            window.setTimeout(() => setLiveAlert(null), 6000);
          }
        } catch (error) {
          console.error('Invalid WebSocket message:', event.data);
        }
      };

      socket.onclose = () => {
        if (!stopped) {
          setWsStatus('DISCONNECTED');
          reconnectTimer = window.setTimeout(connect, 3000);
        }
      };

      socket.onerror = () => {
        setWsStatus('ERROR');
      };
    };

    connect();

    return () => {
      stopped = true;
      if (reconnectTimer !== undefined) {
        window.clearTimeout(reconnectTimer);
      }
      socket?.close();
    };
  }, [authenticated, selectedCity]);

  useEffect(() => {
    if (!liveAlert) {
      return;
    }

    const audioContext = new window.AudioContext();
    const now = audioContext.currentTime;
    const gain = audioContext.createGain();
    gain.gain.setValueAtTime(0.0001, now);
    gain.gain.exponentialRampToValueAtTime(0.16, now + 0.02);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.42);
    gain.connect(audioContext.destination);

    [880, 660].forEach((frequency, index) => {
      const oscillator = audioContext.createOscillator();
      oscillator.type = 'sine';
      oscillator.frequency.value = frequency;
      oscillator.connect(gain);
      oscillator.start(now + index * 0.14);
      oscillator.stop(now + 0.42);
    });

    void audioContext.resume().catch(() => {
      // Browsers may block audio until the operator interacts with the page.
    });

    return () => {
      void audioContext.close();
    };
  }, [liveAlert]);

  const route =
    d.trajectory?.points?.map((p: any) => [
      p.latitude,
      p.longitude,
    ]) || [];

  const mapCenter = d.cameras.length
    ? [
        d.cameras.reduce((sum: number, camera: any) => sum + camera.latitude, 0) / d.cameras.length,
        d.cameras.reduce((sum: number, camera: any) => sum + camera.longitude, 0) / d.cameras.length,
      ]
    : undefined;

  /* =====================================================
     HEADER
  ===================================================== */

  const Header = ({
    title,
  }: {
    title: string;
  }) => (
    <header>
      <div>
        <small>
          CITYWIDE COMMAND CENTER
        </small>

        <h1>{title}</h1>
        <label className="city-filter">
          <span>DATABASE CITY</span>
          <select value={selectedCity} onChange={(event) => setSelectedCity(event.target.value)}>
            <option value="">All cities</option>
            {cities.map((city) => <option key={city} value={city}>{city}</option>)}
          </select>
        </label>
        {cityDataLoading && <small className="city-loading">Loading city data...</small>}
        {cityDataError && <small className="city-error">{cityDataError}</small>}
      </div>

      <div className="header-actions">
        <label className="header-search">
          <span aria-hidden="true">⌕</span>
          <input
            value={globalSearch}
            onChange={(event) => setGlobalSearch(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter' && globalSearch.trim()) {
                setTrackingPlate(globalSearch.trim().toUpperCase());
                setPage('Live Tracking');
              }
            }}
            placeholder="Search vehicle..."
            aria-label="Search vehicle"
          />
        </label>
        <button className="header-icon-button" type="button" onClick={() => setPage('Alerts')} title="Open alerts" aria-label="Open alerts">
          ♢<span>{d.alerts.length}</span>
        </button>
        <span
          className={`connection-status ${wsStatus.toLowerCase()}`}
          style={{
            color:
              wsStatus === 'CONNECTED'
                ? '#31d7a0'
                : '#ffc857',
          }}
        >
          ● {wsStatus}
        </span>
      </div>
    </header>
  );

  /* =====================================================
     DASHBOARD
  ===================================================== */

  const Dashboard = () => (
    <>
      <Header title="Traffic Intelligence Dashboard" />

      <section className="dashboard-hero">
        <div className="hero-copy">
          <span className="hero-kicker">CITYWIDE TRAFFIC OPERATIONS</span>
          <h2>See the road ahead.</h2>
          <p>
            Monitor live cameras, analyze uploaded traffic video and act on verified vehicle intelligence from one command center.
          </p>
          <div className="hero-actions">
            <button className="primary-button" onClick={() => setPage('Video ANPR')}>
              ANALYZE VIDEO
            </button>
            <button className="quiet-button" onClick={() => setPage('Live Tracking')}>
              TRACK A VEHICLE
            </button>
          </div>
        </div>
        <div className="hero-signal">
          <span className="signal-ring" />
          <strong>{d.cameras.length || 0}</strong>
          <small>monitoring points</small>
          <em>{wsStatus === 'CONNECTED' ? 'SYSTEM ONLINE' : 'RECONNECTING'}</em>
        </div>
      </section>

      <section className="quick-services" aria-label="Quick services">
        <button onClick={() => setPage('Video ANPR')}>
          <span className="service-icon">↑</span>
          <span><b>Analyze a video</b><small>Upload traffic footage</small></span>
          <strong>→</strong>
        </button>
        <button onClick={() => setPage('Live Tracking')}>
          <span className="service-icon">⌖</span>
          <span><b>Track a vehicle</b><small>View camera trajectory</small></span>
          <strong>→</strong>
        </button>
        <button onClick={() => setPage('ANPR Events')}>
          <span className="service-icon">▣</span>
          <span><b>Review detections</b><small>Search ANPR event stream</small></span>
          <strong>→</strong>
        </button>
        <button onClick={() => setPage('Alerts')}>
          <span className="service-icon">!</span>
          <span><b>Open alerts</b><small>See active intelligence</small></span>
          <strong>→</strong>
        </button>
      </section>

      <section className="stats">
        {[
          [
            'ACTIVE CAMERAS',
            d.analytics.active_cameras || 0,
          ],
          [
            'VEHICLES TODAY',
            (
              d.analytics.vehicles_today || 0
            ).toLocaleString(),
          ],
          [
            'OPEN ALERTS',
            d.alerts.length,
          ],
          [
            'CONGESTION INDEX',
            `${d.analytics.congestion_index || 0}%`,
          ],
        ].map(([a, b]) => (
          <div
            className="card"
            key={String(a)}
          >
            <label>{a}</label>

            <strong>{b}</strong>

            <small>
              Real-time intelligence
            </small>
          </div>
        ))}
      </section>

      <section className="grid">
        <div className="panel">
          <h3>
            Citywide Vehicle Trajectory
            <i>REAL-TIME</i>
          </h3>

          <MapView
            cameras={d.cameras}
            route={route}
            center={mapCenter}
          />
        </div>

        <div className="panel">
          <h3>
            Live Alerts
            <i>LIVE</i>
          </h3>

          {d.alerts.map((a: any) => (
            <div
              className="alert"
              key={a.id}
            >
              <b>{a.title}</b>

              <p>{a.message}</p>

              <small>
                {a.plate_number ||
                  'CITYWIDE'}
              </small>
            </div>
          ))}
        </div>
      </section>

      <section className="panel table">
        <h3>Recent ANPR Events</h3>

        <table>
          <thead>
            <tr>
              <th>PLATE</th>
              <th>CAMERA</th>
              <th>CONFIDENCE</th>
              <th>TIME</th>
            </tr>
          </thead>

          <tbody>
            {d.events.map((e: any) => (
              <tr key={e.id}>
                <td>
                  <b>{e.plate_number}</b>
                </td>

                <td>
                  CAM-{e.camera_id}
                </td>

                <td>
                  {Math.round(
                    e.confidence * 100
                  )}
                  %
                </td>

                <td>
                  {new Date(
                    e.captured_at
                  ).toLocaleTimeString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );

  /* =====================================================
     LIVE TRACKING
  ===================================================== */

  const LiveTracking = () => {
    const points =
      d.trajectory?.points || [];

    const averageConfidence =
      points.length
        ? Math.round(
            (points.reduce(
              (
                sum: number,
                point: any
              ) =>
                sum + point.confidence,
              0
            ) /
              points.length) *
              100
          )
        : 0;

    const trackVehicle = async () => {
      const plate =
        trackingPlate
          .trim()
          .toUpperCase();

      if (!plate) {
        return;
      }

      try {
        setTrackingLoading(true);

        const trajectory =
          await api.trajectory(
            plate,
            selectedCity || undefined
          );

        setD(
          (previous: any) => ({
            ...previous,
            trajectory,
          })
        );
      } catch (error) {
        console.error(
          'Vehicle tracking failed:',
          error
        );

        setD(
          (previous: any) => ({
            ...previous,
            trajectory: null,
          })
        );
      } finally {
        setTrackingLoading(false);
      }
    };

    const verifyVehicle = async () => {
      const plate = trackingPlate.trim().toUpperCase();
      if (!plate) return;
      try {
        setIntelligenceLoading(true);
        setIntelligenceError('');
        setVehicleIntelligence(await api.vehicleIntelligence(plate));
      } catch (error: any) {
        setVehicleIntelligence(null);
        setIntelligenceError(error.message || 'Vehicle intelligence lookup failed.');
      } finally {
        setIntelligenceLoading(false);
      }
    };

    return (
      <>
        <Header title="Live Vehicle Tracking" />

        <section className="panel">
          <h3>
            Vehicle Trajectory Search
            <i>ANPR</i>
          </h3>

          <div
            className="tracking-search"
          >
            <input
              value={trackingPlate}
              onChange={(e) =>
                setTrackingPlate(
                  e.target.value.toUpperCase()
                )
              }
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  trackVehicle();
                }
              }}
              placeholder="Enter vehicle number"
            />

            <button
              className="primary-button"
              onClick={trackVehicle}
              disabled={
                trackingLoading
              }
            >
              {trackingLoading
                ? 'TRACKING...'
                : 'TRACK VEHICLE'}
            </button>
            <button
              className="quiet-button"
              onClick={verifyVehicle}
              disabled={intelligenceLoading}
            >
              {intelligenceLoading ? 'VERIFYING...' : 'VERIFY VEHICLE'}
            </button>
          </div>
          {intelligenceError && <div className="notice error-notice">{intelligenceError}</div>}
        </section>

        {vehicleIntelligence && (
          <section className="intelligence-grid">
            <div className="panel intelligence-card">
              <h3>Vehicle Verification <i>{vehicleIntelligence.vehicle_verification.is_demo ? 'DEMO' : 'LIVE'}</i></h3>
              <strong>{vehicleIntelligence.plate_number}</strong>
              <p>Status: {vehicleIntelligence.vehicle_verification.status}</p>
              <small>Source: {vehicleIntelligence.vehicle_verification.source}</small>
            </div>
            <div className="panel intelligence-card">
              <h3>Stolen Vehicle Status <i>{vehicleIntelligence.stolen_status.is_demo ? 'DEMO' : 'AUTHORIZED'}</i></h3>
              <strong>{vehicleIntelligence.stolen_status.status}</strong>
              <p>Source: {vehicleIntelligence.stolen_status.source}</p>
              <small>Demo data is not a police or government determination.</small>
            </div>
            <div className="panel intelligence-card">
              <h3>Audit Reference</h3>
              <strong>{vehicleIntelligence.audit_reference}</strong>
              <p>{vehicleIntelligence.trajectory.length} observed events</p>
              <small>Only authorized database fields are displayed.</small>
            </div>
          </section>
        )}

        <section className="stats">
          <div className="card">
            <label>
              TRACKED VEHICLE
            </label>

            <strong>
              {d.trajectory
                ?.plate_number ||
                trackingPlate}
            </strong>

            <small>
              Multi-camera trajectory
            </small>
          </div>

          <div className="card">
            <label>
              CAMERAS MATCHED
            </label>

            <strong>
              {points.length}
            </strong>

            <small>
              Trajectory points
            </small>
          </div>

          <div className="card">
            <label>
              TRACK CONFIDENCE
            </label>

            <strong>
              {averageConfidence}%
            </strong>

            <small>
              Average ANPR confidence
            </small>
          </div>

          <div className="card">
            <label>
              TRACK STATUS
            </label>

            <strong>
              {points.length > 0
                ? 'ACTIVE'
                : 'NO DATA'}
            </strong>

            <small>
              Multi-camera tracking
            </small>
          </div>
        </section>

        <section className="tracking-layout">
          <div className="panel tracking-map">
            <h3>
              Vehicle Route —{' '}
              {d.trajectory
                ?.plate_number ||
                trackingPlate}

              {points.length > 1 && (
                <i> LIVE</i>
              )}
            </h3>

            {points.length > 0 ? (
              <MapView
                cameras={d.cameras}
                route={route}
                center={mapCenter}
              />
            ) : (
              <div className="notice">
                No trajectory data found
                for{' '}
                <b>
                  {trackingPlate}
                </b>
                .
              </div>
            )}
          </div>

          <div className="panel">
            <h3>
              Trajectory Timeline
            </h3>

            {points.length === 0 ? (
              <div className="notice">
                Enter a vehicle number
                and click
                <b>
                  {' '}
                  TRACK VEHICLE
                </b>
                .
              </div>
            ) : (
              points.map(
                (
                  p: any,
                  i: number
                ) => (
                  <div
                    className="timeline-item"
                    key={`${p.camera_id}-${i}`}
                  >
                    <strong>
                      {p.camera_name}
                    </strong>

                    <p>
                      📍{' '}
                      {p.latitude.toFixed(
                        4
                      )}
                      {', '}
                      {p.longitude.toFixed(
                        4
                      )}
                    </p>

                    <small>
                      Camera ID:{' '}
                      {p.camera_id}
                    </small>

                    <br />

                    <small>
                      Confidence:{' '}
                      {Math.round(
                        p.confidence * 100
                      )}
                      %
                    </small>

                    <br />

                    <small>
                      {new Date(
                        p.timestamp
                      ).toLocaleString()}
                    </small>
                  </div>
                )
              )
            )}
          </div>
        </section>
      </>
    );
  };

  /* =====================================================
     ANPR
  ===================================================== */

  const ANPR = () => (
    <>
      <Header title="ANPR Event Monitoring" />

      <section className="stats">
        <div className="card">
          <label>TOTAL EVENTS</label>

          <strong>
            {d.events.length}
          </strong>

          <small>
            Current API records
          </small>
        </div>

        <div className="card">
          <label>UNIQUE VEHICLES</label>

          <strong>
            {
              new Set(
                d.events.map(
                  (e: any) =>
                    e.plate_number
                )
              ).size
            }
          </strong>

          <small>
            Detected plates
          </small>
        </div>
      </section>

      <section className="panel table">
        <h3>
          ANPR Detection Stream
          <i>LIVE</i>
        </h3>

        <table>
          <thead>
            <tr>
              <th>PLATE</th>
              <th>CAMERA</th>
              <th>LOCATION</th>
              <th>CONFIDENCE</th>
              <th>TIME</th>
            </tr>
          </thead>

          <tbody>
            {d.events.map((e: any) => (
              <tr key={e.id}>
                <td>
                  <b>
                    {e.plate_number}
                  </b>
                </td>

                <td>
                  CAM-{e.camera_id}
                </td>

                <td>
                  {e.latitude.toFixed(
                    4
                  )}
                  ,{' '}
                  {e.longitude.toFixed(
                    4
                  )}
                </td>

                <td>
                  {Math.round(
                    e.confidence * 100
                  )}
                  %
                </td>

                <td>
                  {new Date(
                    e.captured_at
                  ).toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );

  const VideoANPR = () => {
    const analyzeVideo = async () => {
      if (!videoFile || !videoCameraId) {
        setVideoError('Select a camera and a video first.');
        return;
      }

      try {
        setVideoLoading(true);
        setVideoError('');
        setVideoResult(
          await api.analyzeVideo(
            Number(videoCameraId),
            videoFile
          )
        );
        const events = await api.events();
        setD((previous: any) => ({ ...previous, events }));
      } catch (error: any) {
        setVideoError(error.message || 'Video processing failed.');
      } finally {
        setVideoLoading(false);
      }
    };

    return (
      <>
        <Header title="Video ANPR Processing" />
        <section className="panel video-upload-panel">
          <h3>Analyze Uploaded Traffic Video <i>OPTIONAL INPUT</i></h3>
          <p className="notice">
            Live camera monitoring remains active. Uploaded video detections use the selected camera context.
          </p>
          <div className="video-upload-controls">
            <select
              className="source-select"
              value={videoCameraId}
              onChange={(event) => setVideoCameraId(event.target.value)}
            >
              <option value="">Select camera</option>
              {d.cameras.map((camera: any) => (
                <option key={camera.id} value={camera.id}>
                  {camera.name}
                </option>
              ))}
            </select>
            <label className="video-dropzone">
              <span className="dropzone-icon">+</span>
              <span>
                <b>{videoFile ? videoFile.name : 'Choose traffic video'}</b>
                <small>MP4, AVI or MOV</small>
              </span>
              <input
                type="file"
                accept="video/*"
                onChange={(event) => setVideoFile(event.target.files?.[0] || null)}
              />
            </label>
            <button
              className="primary-button"
              onClick={analyzeVideo}
              disabled={videoLoading}
            >
              {videoLoading ? 'PROCESSING...' : 'ANALYZE VIDEO'}
            </button>
          </div>
          {videoError && <div className="notice error-notice">{videoError}</div>}
        </section>

        {videoResult && (
          <section className="panel table">
            <h3>Video Processing Result <i>COMPLETE</i></h3>
            <p className="notice">
              {videoResult.frames_processed} frames scanned, {videoResult.frames_sampled} analyzed, {videoResult.detections.length} unique plates saved.
            </p>
            {videoResult.message && (
              <p className={videoResult.detections.length ? 'result-message success' : 'result-message warning'}>
                {videoResult.message}
              </p>
            )}
            <table>
              <thead><tr><th>PLATE</th><th>CONFIDENCE</th><th>FRAME</th><th>EVENT ID</th></tr></thead>
              <tbody>
                {videoResult.detections.map((detection: any) => (
                  <tr key={detection.event_id}>
                    <td><b>{detection.plate_number}</b></td>
                    <td>{Math.round(detection.confidence * 100)}%</td>
                    <td>{detection.frame}</td>
                    <td>{detection.event_id}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        )}
      </>
    );
  };

  /* =====================================================
     ANALYTICS
  ===================================================== */

  const Analytics = () => {
    const events = d.events || [];
    const cameras = d.cameras || [];

    const cameraEventCounts =
      cameras.map((camera: any) => {
        const count =
          events.filter(
            (event: any) =>
              event.camera_id ===
              camera.id
          ).length;

        return {
          ...camera,
          eventCount: count,
        };
      });

    const totalDetections =
      events.length;

    const activeCameras =
      cameras.filter(
        (camera: any) =>
          camera.status === 'online'
      ).length ||
      cameras.length;

    const averageEventsPerCamera =
      activeCameras > 0
        ? totalDetections /
          activeCameras
        : 0;

    const congestionIndex =
      Math.min(
        100,
        Math.round(
          averageEventsPerCamera *
            20
        )
      );

    const congestionLevel =
      congestionIndex >= 76
        ? 'CRITICAL'
        : congestionIndex >= 51
        ? 'HIGH'
        : congestionIndex >= 26
        ? 'MODERATE'
        : 'LOW';

    const analyticsPoints =
      cameraEventCounts
        .filter(
          (camera: any) =>
            camera.eventCount > 0
        )
        .map((camera: any) => [
          camera.latitude,
          camera.longitude,
        ]);

    return (
      <>
        <Header title="Traffic Analytics" />

        <section className="stats">
          <div className="card">
            <label>
              ACTIVE CAMERAS
            </label>

            <strong>
              {activeCameras}
            </strong>

            <small>
              Citywide monitoring
            </small>
          </div>

          <div className="card">
            <label>
              VEHICLE DETECTIONS
            </label>

            <strong>
              {totalDetections.toLocaleString()}
            </strong>

            <small>
              Current ANPR events
            </small>
          </div>

          <div className="card">
            <label>
              CONGESTION INDEX
            </label>

            <strong>
              {congestionIndex}%
            </strong>

            <small>
              {congestionLevel}
            </small>
          </div>

          <div className="card">
            <label>
              OPEN ALERTS
            </label>

            <strong>
              {d.alerts.length}
            </strong>

            <small>
              Active intelligence alerts
            </small>
          </div>
        </section>

        <section className="panel">
          <h3>
            Citywide Congestion Map
            <i>LIVE</i>
          </h3>

          <div className="map">
            <MapContainer
              center={[
                25.435,
                81.852,
              ]}
              zoom={13}
              style={{
                height: '100%',
                width: '100%',
              }}
            >
              <TileLayer
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />

              {cameraEventCounts.map(
                (camera: any) => {
                  const intensity =
                    Math.min(
                      100,
                      camera.eventCount *
                        20
                    );

                  const level =
                    intensity >= 76
                      ? 'CRITICAL'
                      : intensity >= 51
                      ? 'HIGH'
                      : intensity >= 26
                      ? 'MODERATE'
                      : 'LOW';

                  return (
                    <CircleMarker
                      key={
                        camera.id
                      }
                      center={[
                        camera.latitude,
                        camera.longitude,
                      ]}
                      radius={
                        8 +
                        Math.min(
                          camera.eventCount *
                            2,
                          12
                        )
                      }
                      pathOptions={{
                        color:
                          level ===
                          'CRITICAL'
                            ? '#ff4d4f'
                            : level ===
                              'HIGH'
                            ? '#ff9f43'
                            : level ===
                              'MODERATE'
                            ? '#ffc857'
                            : '#31d7a0',
                        fillOpacity: 0.65,
                      }}
                    >
                      <Popup>
                        <b>
                          {camera.name}
                        </b>

                        <br />

                        Status:{' '}
                        {camera.status}

                        <br />

                        Vehicle
                        detections:{' '}
                        {
                          camera.eventCount
                        }

                        <br />

                        Congestion:{' '}
                        {intensity}%

                        <br />

                        Level:{' '}
                        <b>
                          {level}
                        </b>
                      </Popup>
                    </CircleMarker>
                  );
                }
              )}

              {analyticsPoints.length >
                1 && (
                <Polyline
                  positions={
                    analyticsPoints
                  }
                  pathOptions={{
                    color:
                      '#6ea8fe',
                    weight: 3,
                    dashArray:
                      '8 8',
                  }}
                />
              )}
            </MapContainer>
          </div>
        </section>

        <section className="panel table">
          <h3>
            Camera-wise Traffic Analytics
          </h3>

          <table>
            <thead>
              <tr>
                <th>CAMERA</th>
                <th>STATUS</th>
                <th>DETECTIONS</th>
                <th>CONGESTION</th>
                <th>LEVEL</th>
              </tr>
            </thead>

            <tbody>
              {cameraEventCounts.map(
                (camera: any) => {
                  const intensity =
                    Math.min(
                      100,
                      camera.eventCount *
                        20
                    );

                  const level =
                    intensity >= 76
                      ? 'CRITICAL'
                      : intensity >= 51
                      ? 'HIGH'
                      : intensity >= 26
                      ? 'MODERATE'
                      : 'LOW';

                  return (
                    <tr
                      key={
                        camera.id
                      }
                    >
                      <td>
                        <b>
                          {camera.name}
                        </b>
                      </td>

                      <td>
                        {camera.status}
                      </td>

                      <td>
                        {camera.eventCount}
                      </td>

                      <td>
                        {intensity}%
                      </td>

                      <td>
                        <b>
                          {level}
                        </b>
                      </td>
                    </tr>
                  );
                }
              )}
            </tbody>
          </table>
        </section>

        <section className="grid">
          <div className="panel">
            <h3>
              Congestion Intelligence
            </h3>

            <div className="metric">
              <span>
                Overall congestion
              </span>

              <b>
                {congestionIndex}%
              </b>
            </div>

            <div className="metric">
              <span>
                Traffic level
              </span>

              <b>
                {congestionLevel}
              </b>
            </div>

            <div className="metric">
              <span>
                Average detections /
                camera
              </span>

              <b>
                {averageEventsPerCamera.toFixed(
                  1
                )}
              </b>
            </div>

            <div className="metric">
              <span>
                Monitored cameras
              </span>

              <b>
                {activeCameras}
              </b>
            </div>
          </div>

          <div className="panel">
            <h3>
              Traffic Intelligence Status
            </h3>

            <div className="notice">
              <b>
                {congestionLevel}
              </b>

              <br />

              Current congestion
              index:{' '}
              {congestionIndex}%

              <br />

              Vehicle detections:{' '}
              {totalDetections}

              <br />

              Camera coverage:{' '}
              {activeCameras}
            </div>
          </div>
        </section>
      </>
    );
  };

  /* =====================================================
     ALERTS
  ===================================================== */

  const Alerts = () => {
    const triggerDemoAlert = () => {
      const demoAlert = {
        id: `demo-${Date.now()}`,
        severity: 'high',
        title: 'Demo Blacklist Alert',
        message: 'Vehicle UP32AB5698 matched the blacklist.',
        plate_number: 'UP32AB5698',
        resolved: false,
        created_at: new Date().toISOString(),
      };

      setD((previous: any) => ({
        ...previous,
        alerts: [demoAlert, ...(previous.alerts || [])],
      }));
      setLiveAlert(demoAlert);
      window.setTimeout(() => setLiveAlert(null), 6000);
    };

    return (
    <>
      <Header title="Alert Management" />

      <section className="stats">
        <div className="card">
          <label>
            OPEN ALERTS
          </label>

          <strong>
            {d.alerts.length}
          </strong>

          <small>
            Live alert stream
          </small>
        </div>

        <div className="card">
          <label>
            HQ CONNECTION
          </label>

          <strong
            style={{
              color:
                wsStatus === 'CONNECTED'
                  ? '#31d7a0'
                  : '#ffc857',
            }}
          >
            {wsStatus}
          </strong>

          <small>
            WebSocket status
          </small>
        </div>
      </section>

      <section className="panel alerts-page">
        <h3>
          Active Intelligence Alerts
          <i>LIVE</i>
        </h3>

        <button className="demo-alert-button" type="button" onClick={triggerDemoAlert}>
          TEST ALERT + SOUND
        </button>

        {d.alerts.length === 0 ? (
          <div className="notice">
            No active intelligence
            alerts.
          </div>
        ) : (
          d.alerts.map((a: any) => (
            <div
              className="alert alert-large"
              key={a.id}
            >
              <div>
                <b>{a.title}</b>

                <p>
                  {a.message}
                </p>

                <small>
                  Vehicle:{' '}
                  {a.plate_number ||
                    'CITYWIDE'}
                </small>
              </div>

              <strong
                className={`severity ${a.severity}`}
              >
                {a.severity.toUpperCase()}
              </strong>
            </div>
          ))
        )}
      </section>
    </>
    );
  };

  const Blacklist = () => {
    const entries = d.blacklist || [];

    const addVehicle = async (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      const plate = blacklistPlate.trim().toUpperCase();

      if (!plate) {
        setBlacklistMessage('Enter a vehicle number first.');
        return;
      }

      try {
        setBlacklistLoading(true);
        setBlacklistMessage('');
        const entry = await api.addToBlacklist(plate, blacklistReason);
        setD((previous: any) => ({
          ...previous,
          blacklist: [entry, ...(previous.blacklist || [])],
        }));
        setBlacklistPlate('');
        setBlacklistReason('Manual review');
        setBlacklistMessage(`${plate} added to the blacklist.`);
      } catch (error: any) {
        setBlacklistMessage(error.message || 'Unable to update the blacklist.');
      } finally {
        setBlacklistLoading(false);
      }
    };

    const removeVehicle = async (plate: string) => {
      try {
        await api.removeFromBlacklist(plate);
        setD((previous: any) => ({
          ...previous,
          blacklist: (previous.blacklist || []).filter(
            (entry: any) => entry.plate_number !== plate,
          ),
        }));
      } catch (error: any) {
        setBlacklistMessage(error.message || 'Unable to remove vehicle.');
      }
    };

    return (
      <>
        <Header title="Vehicle Blacklist" />

        <section className="blacklist-layout">
          <form className="panel blacklist-form" onSubmit={addVehicle}>
            <div className="blacklist-form-heading">
              <div>
                <span className="hero-kicker">WATCHLIST CONTROL</span>
                <h2>Flag a vehicle</h2>
              </div>
              <span className="blacklist-symbol">!</span>
            </div>
            <p className="blacklist-copy">
              Add a registration number to keep it visible to operators during future reviews.
            </p>
            <label htmlFor="blacklist-plate">Vehicle number</label>
            <input
              id="blacklist-plate"
              value={blacklistPlate}
              onChange={(event) => setBlacklistPlate(event.target.value.toUpperCase())}
              placeholder="e.g. UP32AB5698"
              required
            />
            <label htmlFor="blacklist-reason">Reason</label>
            <input
              id="blacklist-reason"
              value={blacklistReason}
              onChange={(event) => setBlacklistReason(event.target.value)}
              placeholder="Why is this vehicle being watched?"
            />
            <button className="primary-button" type="submit" disabled={blacklistLoading}>
              {blacklistLoading ? 'ADDING...' : 'ADD TO BLACKLIST'}
            </button>
            {blacklistMessage && <p className="blacklist-message">{blacklistMessage}</p>}
          </form>

          <section className="panel blacklist-list">
            <h3>Active watchlist <i>{entries.length} VEHICLES</i></h3>
            {entries.length === 0 ? (
              <div className="notice">No vehicles are currently blacklisted.</div>
            ) : (
              entries.map((entry: any) => (
                <div className="blacklist-entry" key={entry.id}>
                  <div>
                    <strong>{entry.plate_number}</strong>
                    <p>{entry.reason}</p>
                    <small>Added {new Date(entry.created_at).toLocaleString()}</small>
                  </div>
                  <button type="button" onClick={() => removeVehicle(entry.plate_number)}>
                    REMOVE
                  </button>
                </div>
              ))
            )}
          </section>
        </section>
      </>
    );
  };

  /* =====================================================
     E-CHALLAN
  ===================================================== */

  const EChallan = () => {
    const [
      challanStatus,
      setChallanStatus,
    ] = useState('READY');

    const [
      challanMessage,
      setChallanMessage,
    ] = useState('');

    const [
      challanLoading,
      setChallanLoading,
    ] = useState(false);

    const [
      challanNumber,
      setChallanNumber,
    ] = useState('');

    const [
      challanCreatedAt,
      setChallanCreatedAt,
    ] = useState('');

    const vehicleNumber =
      'UP32AB5698';

    const violationCode =
      'SPEEDING';

    const location =
      'Prayagraj, Uttar Pradesh';

    const evidenceUrl =
      'https://example.com/evidence/UP32AB5698.jpg';

    const generateChallan =
      async () => {
        try {
          setChallanLoading(true);
          setChallanStatus(
            'SUBMITTING'
          );
          setChallanMessage('');
          setChallanNumber('');
          setChallanCreatedAt('');

          const response =
            await api.challan({
              plate_number:
                vehicleNumber,
              violation_code:
                violationCode,
              location,
              evidence_url:
                evidenceUrl,
            });

          setChallanStatus(
            response.status?.toUpperCase() ||
              'QUEUED'
          );

          setChallanMessage(
            response.message ||
              'Enforcement request accepted successfully.'
          );

          if (
            response.challan_number
          ) {
            setChallanNumber(
              response.challan_number
            );
          }

          if (
            response.created_at
          ) {
            setChallanCreatedAt(
              response.created_at
            );
          }
        } catch (error: any) {
          console.error(
            'Challan generation failed:',
            error
          );

          setChallanStatus(
            'FAILED'
          );

          setChallanMessage(
            error?.message ||
              'Unable to submit challan request.'
          );
        } finally {
          setChallanLoading(false);
        }
      };

    return (
      <>
        <Header title="E-Challan Enforcement" />

        <section className="panel challan-panel">
          <h3>
            Automated Enforcement
          </h3>

          <div className="challan-info">
            <div>
              <label>
                Detected Vehicle
              </label>

              <strong>
                {vehicleNumber}
              </strong>
            </div>

            <div>
              <label>
                Violation
              </label>

              <strong>
                {violationCode}
              </strong>
            </div>

            <div>
              <label>
                Detection Source
              </label>

              <strong>
                Multi-Camera ANPR
              </strong>
            </div>

            <div>
              <label>
                System Status
              </label>

              <strong
                style={{
                  color:
                    challanStatus ===
                    'FAILED'
                      ? '#ff4d4f'
                      : challanStatus ===
                        'SUBMITTING'
                      ? '#ffc857'
                      : '#31d7a0',
                }}
              >
                {challanStatus}
              </strong>
            </div>
          </div>

          <div className="notice">
            <b>
              Violation Location:
            </b>{' '}
            {location}
            <br />

            <b>
              Evidence:
            </b>{' '}
            Enforcement evidence
            attached to the request.
          </div>

          <div className="challan-actions">
            <button
              className="primary-button"
              onClick={
                generateChallan
              }
              disabled={
                challanLoading
              }
            >
              {challanLoading
                ? 'SUBMITTING...'
                : 'GENERATE CHALLAN'}
            </button>

            {challanMessage && (
              <span
                className={
                  challanStatus ===
                  'FAILED'
                    ? 'error-message'
                    : 'success-message'
                }
              >
                {challanMessage}
              </span>
            )}
          </div>

          {challanNumber &&
            challanStatus ===
              'QUEUED' && (
              <div className="challan-receipt">
                <div className="receipt-header">
                  <div>
                    <div className="receipt-label">
                      E-CHALLAN RECEIPT
                    </div>

                    <h3>
                      Enforcement Record
                      Created
                    </h3>
                  </div>

                  <span className="queued-badge">
                    QUEUED
                  </span>
                </div>

                <div className="receipt-grid">
                  <div>
                    <label>
                      Challan Number
                    </label>

                    <strong>
                      {challanNumber}
                    </strong>
                  </div>

                  <div>
                    <label>
                      Vehicle Number
                    </label>

                    <strong>
                      {vehicleNumber}
                    </strong>
                  </div>

                  <div>
                    <label>
                      Violation
                    </label>

                    <strong>
                      {violationCode}
                    </strong>
                  </div>

                  <div>
                    <label>
                      Location
                    </label>

                    <strong>
                      {location}
                    </strong>
                  </div>

                  <div>
                    <label>
                      Generated At
                    </label>

                    <strong>
                      {challanCreatedAt
                        ? new Date(
                            challanCreatedAt
                          ).toLocaleString()
                        : '—'}
                    </strong>
                  </div>

                  <div>
                    <label>
                      Evidence
                    </label>

                    <a
                      href={
                        evidenceUrl
                      }
                      target="_blank"
                      rel="noreferrer"
                    >
                      View Evidence
                    </a>
                  </div>
                </div>
              </div>
            )}
        </section>
      </>
    );
  };

  const Settings = () => (
    <>
      <Header title="Command Center Settings" />
      <section className="settings-grid">
        <div className="panel settings-profile">
          <div className="settings-avatar">TA</div>
          <div>
            <span className="hero-kicker">ACTIVE OPERATOR</span>
            <h2>Trinetra Administrator</h2>
            <p>Command center operations and traffic intelligence monitoring.</p>
          </div>
          <span className="settings-status">VERIFIED</span>
        </div>
        <div className="panel settings-card">
          <h3>Appearance <i>LOCAL</i></h3>
          <div className="settings-row">
            <div><strong>Interface theme</strong><small>Choose the display mode for this workstation.</small></div>
            <button className="settings-control" type="button" onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}>
              {theme === 'dark' ? 'DARK MODE' : 'LIGHT MODE'}
            </button>
          </div>
        </div>
        <div className="panel settings-card">
          <h3>Notifications <i>LIVE</i></h3>
          <div className="settings-row">
            <div><strong>Alert sound</strong><small>Play a beep when a live alert arrives.</small></div>
            <span className="settings-enabled">ENABLED</span>
          </div>
          <div className="settings-row">
            <div><strong>WebSocket feed</strong><small>Real-time command center event channel.</small></div>
            <span className={`settings-enabled ${wsStatus !== 'CONNECTED' ? 'offline' : ''}`}>{wsStatus}</span>
          </div>
        </div>
        <div className="panel settings-card">
          <h3>System Configuration <i>READ ONLY</i></h3>
          <div className="settings-detail"><span>API service</span><b>FastAPI / v1</b></div>
          <div className="settings-detail"><span>Map provider</span><b>OpenStreetMap + Leaflet</b></div>
          <div className="settings-detail"><span>Monitoring points</span><b>{d.cameras.length} cameras</b></div>
        </div>
      </section>
    </>
  );

  /* =====================================================
     PAGE CONTENT
  ===================================================== */

  const content = {
    Dashboard: <Dashboard />,
    'Live Tracking': LiveTracking(),
    'Video ANPR': VideoANPR(),
    'ANPR Events': ANPR(),
    'Traffic Analytics': Analytics(),
    Alerts: Alerts(),
    Blacklist: Blacklist(),
    'E-Challan': <EChallan />,
    Settings: Settings(),
  }[page as (typeof menu)[number]];

  const submitLogin = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    try {
      const response = await api.login(loginId, loginPassword);
      sessionStorage.setItem('trinetra-access-token', response.access_token);
      sessionStorage.setItem('trinetra-authenticated', 'true');
      setAuthenticated(true);
      setLoginError('');
    } catch (error: any) {
      setLoginError(error.message || 'Invalid command center credentials.');
    }
  };

  const logout = () => {
    sessionStorage.removeItem('trinetra-authenticated');
    sessionStorage.removeItem('trinetra-access-token');
    setAuthenticated(false);
    setPage('Dashboard');
  };
  const sendCopilotMessage = async (messageOverride?: string) => {
    const text = (messageOverride ?? copilotInput).trim();
    if (!text || copilotLoading) return;

    const userMessage = {
      role: 'user',
      content: text,
      time: new Date().toISOString(),
    };
    setCopilotMessages((previous) => [...previous, userMessage]);
    setCopilotInput('');
    setCopilotLoading(true);
    setCopilotFailedMessage('');

    try {
      const response = await api.copilotChat(text);
      const assistantMessage = {
        role: 'assistant',
        content: response.answer || 'Database mein is request ke liye sufficient records available nahi hain.',
        time: new Date().toISOString(),
        data: response.data,
      };
      setCopilotMessages((previous) => [...previous, assistantMessage]);
    } catch (error: any) {
      setCopilotMessages((previous) => [
        ...previous,
        {
          role: 'assistant',
          content: error?.message || 'AI Copilot is temporarily unavailable. Please retry after a moment.',
          time: new Date().toISOString(),
        },
      ]);
      setCopilotFailedMessage(text);
    } finally {
      setCopilotLoading(false);
    }
  };

  const openCopilotTrajectory = async (plate: string) => {
    setTrackingPlate(plate);
    setPage('Live Tracking');
    try {
      const trajectory = await api.trajectory(plate, selectedCity || undefined);
      setD((previous: any) => ({ ...previous, trajectory }));
    } catch (error) {
      console.error('Copilot trajectory opening failed:', error);
    }
  };

  if (!authenticated) {
    return (
      <main className={`login-screen ${theme}-theme`}>
        <div className="login-visual">
          <div className="login-grid" />
          <div className="login-orbit orbit-one" />
          <div className="login-orbit orbit-two" />
          <div className="login-brand-mark">
            <img src="/team-logo.png" alt="Trinetra AI team logo" />
          </div>
          <span className="login-kicker">CITYWIDE TRAFFIC OPERATIONS</span>
          <h1>Trinetra AI</h1>
          <p>One command center for every road, camera and vehicle signal.</p>
          <div className="login-live-indicator"><span /> SYSTEM READY</div>
        </div>

        <form className="login-panel" onSubmit={submitLogin}>
          <div className="login-panel-top">
            <span className="login-kicker">SECURE ACCESS</span>
            <span className="login-lock">◈</span>
          </div>
          <h2>Welcome back</h2>
          <p className="login-subtitle">Sign in to your traffic intelligence workspace.</p>

          <label htmlFor="login-id">Operator ID</label>
          <input
            id="login-id"
            value={loginId}
            onChange={(event) => setLoginId(event.target.value)}
            placeholder="Enter operator ID"
            autoComplete="username"
            required
          />

          <label htmlFor="login-password">Access key</label>
          <input
            id="login-password"
            type="password"
            value={loginPassword}
            onChange={(event) => setLoginPassword(event.target.value)}
            placeholder="Enter access key"
            autoComplete="current-password"
            required
          />

          {loginError && <div className="login-error">{loginError}</div>}

          <button className="primary-button login-button" type="submit">
            ENTER COMMAND CENTER <span>→</span>
          </button>
          <small className="login-footer">Protected operations environment · v1.0</small>
        </form>
      </main>
    );
  }

  /* =====================================================
     FINAL UI
  ===================================================== */

  return (
    <div
      className={`shell ${theme}-theme`}
    >
      {/* =================================================
          LIVE ALERT POPUP
      ================================================= */}

      {liveAlert && (
        <div className="live-alert-popup">
          <div className="live-alert-label">
            ● LIVE INTELLIGENCE ALERT
          </div>

          <strong>
            {liveAlert.title}
          </strong>

          <p>
            {liveAlert.message}
          </p>

          <small>
            Vehicle:{' '}
            {liveAlert.plate_number ||
              'CITYWIDE'}
          </small>
        </div>
      )}

      {/* =================================================
          SIDEBAR
      ================================================= */}

      <aside>
        <div className="brand-block">
          <div className="logo">
            <img src="/team-logo.png" alt="Trinetra AI team logo" />
          </div>

          <div className="brand-name">
            TRENETRA AI
          </div>

          <div className="brand-subtitle">
            AI COMMAND CENTER
          </div>
        </div>

        <button
          className="theme-toggle"
          aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
          title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
          onClick={() =>
            setTheme(
              theme === 'dark'
                ? 'light'
                : 'dark'
            )
          }
        >
          <span>
            {theme === 'dark'
              ? '☀'
              : '☾'}
          </span>
          <i aria-hidden="true" />
        </button>

        <button className="logout-button" onClick={logout}>
          <span>↪</span> Sign out
        </button>

        {menu.map((x, i) => (
          <div
            className={
              page === x
                ? 'nav active'
                : 'nav'
            }
            key={x}
            onClick={() =>
              setPage(x)
            }
          >
            {
              [
                '⌂',
                '⌖',
                '▶',
                '▣',
                '◌',
                '⚠',
                '!',
                '₹',
                '⚙',
              ][i]
            }{' '}
            {x}
          </div>
        ))}

        <footer>
          Team Trinetra Ai
          <br />
          BBDITM, LUCKNOW
          <br />
          SIH 2026
        </footer>
      </aside>

      {/* =================================================
          MAIN
      ================================================= */}

      <main>{content}</main>
      <div className="copilot-shell">
        {!copilotOpen ? (
          <button
            type="button"
            className="copilot-toggle"
            onClick={() => setCopilotOpen(true)}
          >
            <span>✦</span>
            Trinetra AI Copilot
          </button>
        ) : (
          <div className="copilot-panel">
            <div className="copilot-header">
              <div>
                <strong>Trinetra AI Copilot</strong>
                <small>Intelligent Vehicle Investigation Assistant</small>
              </div>
              <button type="button" className="copilot-close" onClick={() => setCopilotOpen(false)}>
                ×
              </button>
            </div>

            <div className="copilot-quick-actions">
              {['Vehicle History', 'Last Seen', 'Camera Timeline', 'Blacklist Status'].map((label) => (
                <button key={label} type="button" onClick={() => sendCopilotMessage(label)}>
                  {label}
                </button>
              ))}
            </div>

            <div className="copilot-messages" ref={copilotMessagesRef}>
              {copilotMessages.map((message: any, index: number) => (
                <div key={`${message.time}-${index}`} className={`copilot-message ${message.role}`}>
                  <div className="copilot-avatar">{message.role === 'user' ? 'U' : 'AI'}</div>
                  <div className="copilot-bubble">
                    <p>{message.content}</p>
                    {message.data?.events?.length ? (
                      <ul>
                        {message.data.events.slice(0, 3).map((event: any) => (
                          <li key={event.id}>
                            {event.camera_name} · {new Date(event.captured_at).toLocaleString()}
                          </li>
                        ))}
                      </ul>
                    ) : null}
                    {message.data?.vehicle_number && message.data?.events?.length ? (
                      <button
                        type="button"
                        className="copilot-map-action"
                        onClick={() => void openCopilotTrajectory(message.data.vehicle_number)}
                      >
                        Open observed trajectory
                      </button>
                    ) : null}
                    <small>{new Date(message.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</small>
                  </div>
                </div>
              ))}
              {copilotLoading && (
                <div className="copilot-message assistant">
                  <div className="copilot-avatar">AI</div>
                  <div className="copilot-bubble typing">
                    <span />
                    <span />
                    <span />
                  </div>
                </div>
              )}
              {copilotFailedMessage && !copilotLoading && (
                <button
                  type="button"
                  className="copilot-retry"
                  onClick={() => void sendCopilotMessage(copilotFailedMessage)}
                >
                  Retry last request
                </button>
              )}
            </div>

            <div className="copilot-input-row">
              <textarea
                value={copilotInput}
                rows={1}
                onChange={(event) => setCopilotInput(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter' && !event.shiftKey) {
                    event.preventDefault();
                    void sendCopilotMessage();
                  }
                }}
                placeholder="Ask about a vehicle, camera, or blacklist status..."
              />
              <button type="button" className="primary-button" onClick={() => void sendCopilotMessage()} disabled={copilotLoading}>
                Send
              </button>
            </div>
            <button
              type="button"
              className="copilot-clear"
              onClick={() => {
                setCopilotMessages([]);
                setCopilotFailedMessage('');
              }}
            >
              Clear conversation
            </button>
          </div>
        )}
      </div>
    </div>
  );
}