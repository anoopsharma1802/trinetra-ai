import { useEffect, useState } from 'react';
import {
  MapContainer,
  TileLayer,
  CircleMarker,
  Polyline,
  Popup,
} from 'react-leaflet';
import { api } from './api';

const menu = [
  'Dashboard',
  'Live Tracking',
  'ANPR Events',
  'Traffic Analytics',
  'Alerts',
  'E-Challan',
];

function MapView({ cameras, route }: any) {
  return (
    <div className="map">
      <MapContainer
        center={[25.435, 81.852]}
        zoom={13}
        style={{ height: '100%', width: '100%' }}
      >
        <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />

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

        {route?.length > 1 && (
          <Polyline
            positions={route}
            pathOptions={{
              color: '#6ea8fe',
              weight: 5,
            }}
          />
        )}
      </MapContainer>
    </div>
  );
}

export default function App() {
  const [page, setPage] = useState('Dashboard');
  const [trackingPlate, setTrackingPlate] =
  useState('UP32AB5698');

const [trackingLoading, setTrackingLoading] =
  useState(false);

  const [d, setD] = useState<any>({
    cameras: [],
    events: [],
    analytics: {},
    alerts: [],
    trajectory: null,
  });

  // WebSocket status
  const [wsStatus, setWsStatus] = useState('CONNECTING');

  // Latest live alert popup
  const [liveAlert, setLiveAlert] = useState<any>(null);

  // ---------------------------------------------------------
  // Initial API data
  // ---------------------------------------------------------
  useEffect(() => {
    Promise.all([
      api.cameras(),
      api.events(),
      api.analytics(),
      api.alerts(),
      api.trajectory('UP32AB5698'),
    ]).then(([cameras, events, analytics, alerts, trajectory]) => {
      setD({
        cameras,
        events,
        analytics,
        alerts,
        trajectory,
      });
    });
  }, []);

  // ---------------------------------------------------------
  // REAL-TIME WEBSOCKET
  // ---------------------------------------------------------
  useEffect(() => {
    const wsUrl =
      import.meta.env.VITE_WS_URL ||
      'ws://localhost:8000/ws/events';

    const socket = new WebSocket(wsUrl);

    socket.onopen = () => {
      console.log('TRENETRA WebSocket connected');
      setWsStatus('CONNECTED');

      // Keep the connection alive
      socket.send('HQ_CONNECTED');
    };

    socket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);

        console.log('LIVE ALERT RECEIVED:', message);

        // Expected backend message:
        // {
        //   type: "alert",
        //   alert: {
        //      id,
        //      severity,
        //      title,
        //      message,
        //      plate_number,
        //      resolved,
        //      created_at
        //   }
        // }

        const incomingAlert = message.alert || message;

        if (
          message.type === 'alert' ||
          incomingAlert.title
        ) {
          setD((previous: any) => {
            const alreadyExists = previous.alerts.some(
              (a: any) => a.id === incomingAlert.id
            );

            if (alreadyExists) {
              return previous;
            }

            return {
              ...previous,
              alerts: [incomingAlert, ...previous.alerts],
            };
          });

          setLiveAlert(incomingAlert);

          // Automatically hide popup after 6 seconds
          setTimeout(() => {
            setLiveAlert(null);
          }, 6000);
        }
      } catch (error) {
        console.error(
          'Invalid WebSocket message:',
          event.data
        );
      }
    };

    socket.onclose = () => {
      console.log('TRENETRA WebSocket disconnected');
      setWsStatus('DISCONNECTED');
    };

    socket.onerror = (error) => {
      console.error('TRENETRA WebSocket error:', error);
      setWsStatus('ERROR');
    };

    return () => {
      socket.close();
    };
  }, []);

  const route =
    d.trajectory?.points?.map((p: any) => [
      p.latitude,
      p.longitude,
    ]) || [];

  // ---------------------------------------------------------
  // Header
  // ---------------------------------------------------------
  const Header = ({ title }: { title: string }) => (
    <header>
      <div>
        <small>CITYWIDE COMMAND CENTER</small>
        <h1>{title}</h1>
      </div>

      <span
        style={{
          color:
            wsStatus === 'CONNECTED'
              ? '#31d7a0'
              : '#ffc857',
        }}
      >
        ● {wsStatus}
      </span>
    </header>
  );

  // ---------------------------------------------------------
  // Dashboard
  // ---------------------------------------------------------
  const Dashboard = () => (
    <>
      <Header title="Traffic Intelligence Dashboard" />

      <section className="stats">
        {[
          [
            'ACTIVE CAMERAS',
            d.analytics.active_cameras || 0,
          ],
          [
            'VEHICLES TODAY',
            (d.analytics.vehicles_today || 0).toLocaleString(),
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
          <div className="card" key={String(a)}>
            <label>{a}</label>
            <strong>{b}</strong>
            <small>Real-time intelligence</small>
          </div>
        ))}
      </section>

      <section className="grid">
        <div className="panel">
          <h3>
            Citywide Vehicle Trajectory <i>REAL-TIME</i>
          </h3>

          <MapView
            cameras={d.cameras}
            route={route}
          />
        </div>

        <div className="panel">
          <h3>
            Live Alerts <i>LIVE</i>
          </h3>

          {d.alerts.map((a: any) => (
            <div className="alert" key={a.id}>
              <b>{a.title}</b>
              <p>{a.message}</p>
              <small>
                {a.plate_number || 'CITYWIDE'}
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

                <td>CAM-{e.camera_id}</td>

                <td>
                  {Math.round(e.confidence * 100)}%
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

  // ---------------------------------------------------------
  // Live Tracking
  // ---------------------------------------------------------
const LiveTracking = () => {
  const points = d.trajectory?.points || [];

  const averageConfidence = points.length
    ? Math.round(
        (points.reduce(
          (sum: number, point: any) =>
            sum + point.confidence,
          0
        ) /
          points.length) *
          100
      )
    : 0;

  const trackVehicle = async () => {
    const plate = trackingPlate.trim().toUpperCase();

    if (!plate) {
      return;
    }

    try {
      setTrackingLoading(true);

      const trajectory =
        await api.trajectory(plate);

      setD((previous: any) => ({
        ...previous,
        trajectory,
      }));
    } catch (error) {
      console.error(
        'Vehicle tracking failed:',
        error
      );

      setD((previous: any) => ({
        ...previous,
        trajectory: null,
      }));
    } finally {
      setTrackingLoading(false);
    }
  };

  return (
    <>
      <Header title="Live Vehicle Tracking" />

      {/* VEHICLE SEARCH */}
      <section className="panel">
        <h3>
          Vehicle Trajectory Search <i>ANPR</i>
        </h3>

        <div
          style={{
            display: 'flex',
            gap: 12,
            marginTop: 16,
            alignItems: 'center',
          }}
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
            style={{
              flex: 1,
              padding: '12px 14px',
              borderRadius: 8,
              border: '1px solid #29404d',
              background: '#08151c',
              color: '#f4f8fa',
              fontSize: 15,
              outline: 'none',
            }}
          />

          <button
            onClick={trackVehicle}
            disabled={trackingLoading}
            style={{
              padding: '12px 22px',
              borderRadius: 8,
              border: 'none',
              background: '#31d7a0',
              color: '#061014',
              fontWeight: 700,
              cursor: 'pointer',
            }}
          >
            {trackingLoading
              ? 'TRACKING...'
              : 'TRACK VEHICLE'}
          </button>
        </div>
      </section>

      {/* TRACKING STATS */}
      <section className="stats">
        <div className="card">
          <label>TRACKED VEHICLE</label>

          <strong>
            {d.trajectory?.plate_number ||
              trackingPlate}
          </strong>

          <small>
            Multi-camera trajectory
          </small>
        </div>

        <div className="card">
          <label>CAMERAS MATCHED</label>

          <strong>{points.length}</strong>

          <small>
            Trajectory points
          </small>
        </div>

        <div className="card">
          <label>TRACK CONFIDENCE</label>

          <strong>
            {averageConfidence}%
          </strong>

          <small>
            Average ANPR confidence
          </small>
        </div>

        <div className="card">
          <label>TRACK STATUS</label>

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

      {/* MAP + TIMELINE */}
      <section className="tracking-layout">
        <div className="panel tracking-map">
          <h3>
            Vehicle Route —{' '}
            {d.trajectory?.plate_number ||
              trackingPlate}

            {points.length > 1 && (
              <i> LIVE</i>
            )}
          </h3>

          {points.length > 0 ? (
            <MapView
              cameras={d.cameras}
              route={route}
            />
          ) : (
            <div className="notice">
              No trajectory data found for{' '}
              <b>{trackingPlate}</b>.
            </div>
          )}
        </div>

        <div className="panel">
          <h3>Trajectory Timeline</h3>

          {points.length === 0 ? (
            <div className="notice">
              Enter a vehicle number and click
              <b> TRACK VEHICLE</b>.
            </div>
          ) : (
            points.map(
              (p: any, i: number) => (
                <div
                  className="timeline-item"
                  key={`${p.camera_id}-${i}`}
                >
                  <strong>
                    {p.camera_name}
                  </strong>

                  <p>
                    📍{' '}
                    {p.latitude.toFixed(4)}
                    {', '}
                    {p.longitude.toFixed(4)}
                  </p>

                  <small>
                    Camera ID: {p.camera_id}
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
  // ---------------------------------------------------------
  // ANPR
  // ---------------------------------------------------------
  const ANPR = () => (
    <>
      <Header title="ANPR Event Monitoring" />

      <section className="stats">
        <div className="card">
          <label>TOTAL EVENTS</label>
          <strong>{d.events.length}</strong>
          <small>Current API records</small>
        </div>

        <div className="card">
          <label>UNIQUE VEHICLES</label>
          <strong>
            {
              new Set(
                d.events.map(
                  (e: any) => e.plate_number
                )
              ).size
            }
          </strong>
          <small>Detected plates</small>
        </div>
      </section>

      <section className="panel table">
        <h3>
          ANPR Detection Stream <i>LIVE</i>
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
                  <b>{e.plate_number}</b>
                </td>

                <td>CAM-{e.camera_id}</td>

                <td>
                  {e.latitude.toFixed(4)},{' '}
                  {e.longitude.toFixed(4)}
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

  // ---------------------------------------------------------
  // Analytics
  // ---------------------------------------------------------
  const Analytics = () => {
  const events = d.events || [];
  const cameras = d.cameras || [];

  // -----------------------------------------
  // CONGESTION CALCULATION
  // -----------------------------------------
  const cameraEventCounts = cameras.map((camera: any) => {
    const count = events.filter(
      (event: any) => event.camera_id === camera.id
    ).length;

    return {
      ...camera,
      eventCount: count,
    };
  });

  const totalDetections = events.length;

  const activeCameras =
    cameras.filter(
      (camera: any) => camera.status === 'online'
    ).length || cameras.length;

  /*
   * Demo congestion model:
   *
   * 0-25   = Low
   * 26-50  = Moderate
   * 51-75  = High
   * 76-100 = Critical
   *
   * The index is derived from current event density
   * relative to active camera coverage.
   */
  const averageEventsPerCamera =
    activeCameras > 0
      ? totalDetections / activeCameras
      : 0;

  const congestionIndex = Math.min(
    100,
    Math.round(
      averageEventsPerCamera * 20
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

  // -----------------------------------------
  // MAP ROUTE
  // -----------------------------------------
  const analyticsPoints = cameraEventCounts
    .filter((camera: any) => camera.eventCount > 0)
    .map((camera: any) => [
      camera.latitude,
      camera.longitude,
    ]);

  return (
    <>
      <Header title="Traffic Analytics" />

      {/* ---------------------------------- */}
      {/* ANALYTICS CARDS */}
      {/* ---------------------------------- */}

      <section className="stats">

        <div className="card">
          <label>ACTIVE CAMERAS</label>

          <strong>
            {activeCameras}
          </strong>

          <small>
            Citywide monitoring
          </small>
        </div>

        <div className="card">
          <label>VEHICLE DETECTIONS</label>

          <strong>
            {totalDetections.toLocaleString()}
          </strong>

          <small>
            Current ANPR events
          </small>
        </div>

        <div className="card">
          <label>CONGESTION INDEX</label>

          <strong>
            {congestionIndex}%
          </strong>

          <small>
            {congestionLevel}
          </small>
        </div>

        <div className="card">
          <label>OPEN ALERTS</label>

          <strong>
            {d.alerts.length}
          </strong>

          <small>
            Active intelligence alerts
          </small>
        </div>

      </section>

      {/* ---------------------------------- */}
      {/* CONGESTION MAP */}
      {/* ---------------------------------- */}

      <section className="panel">

        <h3>
          Citywide Congestion Map
          <i>LIVE</i>
        </h3>

        <div className="map">

          <MapContainer
            center={[25.435, 81.852]}
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

                const intensity = Math.min(
                  100,
                  camera.eventCount * 20
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
                    key={camera.id}
                    center={[
                      camera.latitude,
                      camera.longitude,
                    ]}
                    radius={
                      8 +
                      Math.min(
                        camera.eventCount * 2,
                        12
                      )
                    }
                    pathOptions={{
                      color:
                        level === 'CRITICAL'
                          ? '#ff4d4f'
                          : level === 'HIGH'
                          ? '#ff9f43'
                          : level === 'MODERATE'
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

                      Vehicle detections:{' '}
                      {camera.eventCount}

                      <br />

                      Congestion:{' '}
                      {intensity}%

                      <br />

                      Level:{' '}
                      <b>{level}</b>

                    </Popup>

                  </CircleMarker>
                );
              }
            )}

            {analyticsPoints.length > 1 && (
              <Polyline
                positions={analyticsPoints}
                pathOptions={{
                  color: '#6ea8fe',
                  weight: 3,
                  dashArray: '8 8',
                }}
              />
            )}

          </MapContainer>

        </div>

      </section>

      {/* ---------------------------------- */}
      {/* CAMERA ANALYTICS */}
      {/* ---------------------------------- */}

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
                    camera.eventCount * 20
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
                  <tr key={camera.id}>

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

      {/* ---------------------------------- */}
      {/* TRAFFIC INTELLIGENCE */}
      {/* ---------------------------------- */}

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
              Average detections / camera
            </span>

            <b>
              {averageEventsPerCamera.toFixed(1)}
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

            Current congestion index:
            {' '}
            {congestionIndex}%

            <br />

            Vehicle detections:
            {' '}
            {totalDetections}

            <br />

            Camera coverage:
            {' '}
            {activeCameras}

          </div>

        </div>

      </section>
    </>
  );
};

  // ---------------------------------------------------------
  // Alerts
  // ---------------------------------------------------------
  const Alerts = () => (
    <>
      <Header title="Alert Management" />

      <section className="stats">
        <div className="card">
          <label>OPEN ALERTS</label>
          <strong>{d.alerts.length}</strong>
          <small>Live alert stream</small>
        </div>

        <div className="card">
          <label>HQ CONNECTION</label>
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
          <small>WebSocket status</small>
        </div>
      </section>

      <section className="panel alerts-page">
        <h3>
          Active Intelligence Alerts <i>LIVE</i>
        </h3>

        {d.alerts.length === 0 ? (
          <div className="notice">
            No active intelligence alerts.
          </div>
        ) : (
          d.alerts.map((a: any) => (
            <div
              className="alert alert-large"
              key={a.id}
            >
              <div>
                <b>{a.title}</b>

                <p>{a.message}</p>

                <small>
                  Vehicle:{' '}
                  {a.plate_number || 'CITYWIDE'}
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

  // ---------------------------------------------------------
  // E-Challan
  // ---------------------------------------------------------
 const EChallan = () => {
  const [challanStatus, setChallanStatus] = useState('READY');
  const [challanMessage, setChallanMessage] = useState('');
  const [challanLoading, setChallanLoading] = useState(false);

  const vehicleNumber = 'UP32AB5698';
  const violationCode = 'SPEEDING';
  const location = 'Prayagraj, Uttar Pradesh';
  const evidenceUrl =
    'https://example.com/evidence/UP32AB5698.jpg';

  const generateChallan = async () => {
    try {
      setChallanLoading(true);
      setChallanStatus('SUBMITTING');
      setChallanMessage('');

      const response = await api.challan({
        plate_number: vehicleNumber,
        violation_code: violationCode,
        location,
        evidence_url: evidenceUrl,
      });

      setChallanStatus(
        response.status?.toUpperCase() || 'QUEUED'
      );

      setChallanMessage(
        response.message ||
          'Enforcement request accepted successfully.'
      );
    } catch (error: any) {
      console.error(
        'Challan generation failed:',
        error
      );

      setChallanStatus('FAILED');

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
        <h3>Automated Enforcement</h3>

        <div className="challan-info">

          <div>
            <label>Detected Vehicle</label>

            <strong>
              {vehicleNumber}
            </strong>
          </div>

          <div>
            <label>Violation</label>

            <strong>
              {violationCode}
            </strong>
          </div>

          <div>
            <label>Detection Source</label>

            <strong>
              Multi-Camera ANPR
            </strong>
          </div>

          <div>
            <label>System Status</label>

            <strong
              className={
                challanStatus === 'FAILED'
                  ? ''
                  : 'status-online'
              }
              style={{
                color:
                  challanStatus === 'FAILED'
                    ? '#ff4d4f'
                    : challanStatus === 'SUBMITTING'
                    ? '#ffc857'
                    : '#31d7a0',
              }}
            >
              {challanStatus}
            </strong>
          </div>

        </div>

        <div className="notice">
          <b>Violation Location:</b>{' '}
          {location}
          <br />

          <b>Evidence:</b>{' '}
          Enforcement evidence attached to the
          request.
        </div>

        <div
          style={{
            marginTop: 20,
            display: 'flex',
            alignItems: 'center',
            gap: 16,
          }}
        >
          <button
            onClick={generateChallan}
            disabled={challanLoading}
            style={{
              padding: '12px 24px',
              borderRadius: 8,
              border: 'none',
              background: challanLoading
                ? '#29404d'
                : '#31d7a0',
              color: '#061014',
              fontWeight: 700,
              cursor: challanLoading
                ? 'not-allowed'
                : 'pointer',
            }}
          >
            {challanLoading
              ? 'SUBMITTING...'
              : 'GENERATE CHALLAN'}
          </button>

          {challanMessage && (
            <span
              style={{
                color:
                  challanStatus === 'FAILED'
                    ? '#ff4d4f'
                    : '#9ab0bd',
                fontSize: 13,
              }}
            >
              {challanMessage}
            </span>
          )}
        </div>

      </section>
    </>
  );
};
  const content = {
  Dashboard: <Dashboard />,
  'Live Tracking': <LiveTracking />,
  'ANPR Events': <ANPR />,
  'Traffic Analytics': <Analytics />,
  Alerts: <Alerts />,
  'E-Challan': <EChallan />,
}[page as (typeof menu)[number]];

  return (
    <div className="shell">

      {/* LIVE ALERT POPUP */}
      {liveAlert && (
        <div
          style={{
            position: 'fixed',
            top: 20,
            right: 20,
            width: 360,
            zIndex: 9999,
            padding: '18px 20px',
            borderRadius: 10,
            border: '1px solid #31d7a0',
            background: '#08151c',
            boxShadow:
              '0 10px 40px rgba(0,0,0,.45)',
          }}
        >
          <div
            style={{
              color: '#31d7a0',
              fontSize: 11,
              letterSpacing: 1.5,
              marginBottom: 8,
            }}
          >
            ● LIVE INTELLIGENCE ALERT
          </div>

          <strong
            style={{
              fontSize: 18,
              color: '#f4f8fa',
            }}
          >
            {liveAlert.title}
          </strong>

          <p
            style={{
              color: '#9ab0bd',
              margin: '8px 0',
            }}
          >
            {liveAlert.message}
          </p>

          <small
            style={{
              color: '#6ea8fe',
            }}
          >
            Vehicle:{' '}
            {liveAlert.plate_number ||
              'CITYWIDE'}
          </small>
        </div>
      )}

      <aside>
        <div className="logo">T</div>

        <h2>TRENETRA</h2>

        <small>AI COMMAND CENTER</small>

        {menu.map((x, i) => (
          <div
            className={
              page === x
                ? 'nav active'
                : 'nav'
            }
            key={x}
            onClick={() => setPage(x)}
          >
            {['⌂', '⌖', '▣', '◌', '⚠', '₹'][i]}{' '}
            {x}
          </div>
        ))}

        <footer>
          SIH 2026
          <br />
          SIH26127
        </footer>
      </aside>

      <main>{content}</main>
    </div>
  );
}