# Visão Computacional

Detector de lixo e entulho em via pública, ligado ao alagamento porque o lixo entope bueiros. O modelo YOLO11n foi treinado com a base pública TACO, com divisão em treino, validação e teste sem vazamento.

Resultados no conjunto de teste: mAP@0,5 = 0,400, mAP@0,5:0,95 = 0,254, recall = 0,367 e F1 = 0,457.

Arquivos:
- `Radar_Cidadao_Visao_Computacional.ipynb`: notebook executado no Google Colab (GPU), com treinamento, teste, análise de erros, interface Gradio e testes com fotos reais.
- `Relatorio_Tecnico_Visao_Computacional_Radar_Cidadao.pdf`: relatório técnico.
- `Radar_Cidadao_Visao_Computacional.mp4`: vídeo de demonstração.
- `lixo-em-calcada-na-vila-protestantes.jpeg` e `lixo-rodoviaria.jpg`: fotos usadas no teste.
