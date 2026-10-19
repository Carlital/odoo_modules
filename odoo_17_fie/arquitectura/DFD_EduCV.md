flowchart LR

%% Actores
A1[Docente]
A2[Coordinador Académico]
A3[Administrador Institucional]
A4[Servicios Institucionales / Google Sheets]
A5[Repositorio de CV en PDF]

%% Procesos
P1((P1 Nginx / Proxy HTTPS))
P2((P2 Odoo 17 - Modulo EduCV))
P3((P3 n8n - Flujos ETL))
P4((P4 Auditoria / Logging))

%% Almacenes
D1[(D1 PostgreSQL - Perfiles y Estados)]
D2[(D2 Bitacoras - Nginx / Odoo / n8n)]

%% Flujos
A1 -->|Peticiones HTTPS| P1
A2 -->|Consultas y reportes| P1
A3 -->|Administracion| P1

P1 -->|Rutas Web / API| P2
P2 <-->|Integracion| P3
P2 <--> D1
P1 --> P4
P2 --> P4
P3 --> P4
P4 --> D2

A4 <-->|Extraccion de datos| P3
A5 -->|Descarga de CVs| P3

%% Limites de confianza
subgraph TB1_Internet [TB1: Internet / HTTPS Publico]
  A1
  A2
  A3
end

subgraph TB2_RedInterna [TB2: Red Interna Docker]
  P1
  P2
  P3
  D1
  D2
end

%% Estilos (asignacion por clase clasica)
classDef actor fill:#ffffff,stroke:#333333,stroke-width:1px;
classDef proc fill:#e8f0fe,stroke:#3366cc,stroke-width:1.5px;
classDef data fill:#fff9db,stroke:#e67700,stroke-width:1.2px;

class A1,A2,A3,A4,A5 actor;
class P1,P2,P3,P4 proc;
class D1,D2 data;
