# System Architecture
Camera/CCTV -> Edge AI (YOLO + plate localization + enhancement + OCR) -> Kafka -> FastAPI AI orchestration -> vehicle re-identification (ByteTrack/DeepSORT) -> PostgreSQL/PostGIS -> React GIS dashboard.

Outputs: vehicle trajectory, heatmap, congestion analysis, real-time alerts and an authorized e-challan integration point.
