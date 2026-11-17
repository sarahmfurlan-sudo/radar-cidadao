# IoT

ESP32 simulado no Wokwi com sensor ultrassônico HC-SR04 (nível de água no bueiro) e potenciômetro (intensidade de chuva). O ESP32 classifica o risco (NORMAL, ATENCAO ou ALERTA), publica por MQTT nos tópicos `radarcidadao/bueiro01/telemetria` e `radarcidadao/bueiro01/alerta`, e o Node-RED mostra o painel, grava no InfluxDB Cloud e expõe `GET /api/radar/status`, que o Front End consulta.

Arquivos:
- `app_radar_cidadao/`: código do ESP32 e projeto do Wokwi.
- `fluxo_envio_InfluxDB.json` e `dashboard.json`: fluxos do Node-RED (painel, API e gravação no InfluxDB).
- `relatorio_radar_cidadao.md` e `.pdf`: relatório com arquitetura, contrato das mensagens, regras, testes e limitações.
- `prints/`: evidências.

Vídeo: https://youtu.be/PKmweoWx3LY
