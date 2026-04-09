# PoseCoach - The Modern Exercise Form Checker

This application is designed to provide real-time feedback on exercise form using computer vision and machine learning techniques. It consists of a backend server that processes video input and a frontend interface that allows users to interact with the system.

## Repository Structure
```bash
.
├── feedback_ai.py
├── form_checkers
│   ├── __init__.py
│   ├── _utilityFunctions.py
│   ├── benchpress_formChecker.py
│   ├── bentOver_formChecker.py
│   └── squat_formChecker.py
├── frontend
│   ├── eslint.config.mjs
│   ├── next.config.ts
│   ├── package-lock.json
│   ├── package.json
│   ├── postcss.config.mjs
│   ├── public
│   ├── src
│   │   └── app
│   │       ├── components
│   │       │   ├── countdown.tsx
│   │       │   ├── exercise-video.tsx
│   │       │   ├── formChecker_button.tsx
│   │       │   ├── navbar.tsx
│   │       │   └── webcam-feed.tsx
│   │       ├── exercises
│   │       │   ├── bench-press
│   │       │   │   ├── form_checker
│   │       │   │   │   └── page.tsx
│   │       │   │   └── page.tsx
│   │       │   ├── bent-over-barbell-row
│   │       │   │   ├── form_checker
│   │       │   │   │   └── page.tsx
│   │       │   │   └── page.tsx
│   │       │   └── squat
│   │       │       ├── form_checker
│   │       │       │   └── page.tsx
│   │       │       └── page.tsx
│   │       ├── globals.css
│   │       ├── layout.tsx
│   │       └── page.tsx
│   └── tsconfig.json
├── init_functions.py
├── pose_estimator.py
├── pose_estimator_supine.py
├── requirements.txt
├── trained_models
│   └── yolo26s-pose.pt
└── server.py
```

## How to use it
Create a venv and download the required libraries:
```bash
python3 -m venv .venv
source .venv/bin/activate
cd src
pip install -r requirements.txt
```

### Prerequisites
To test the application, it is required that the backend as well as the frontend uses a secure tunnel to be able to request camera access on a webbrowser. Follow the next steps to ensure that the whole application is secure:

### First Terminal: 
```bash
cd src
uvicorn server:app --reload --port 8000
```

### Second Terminal:

#### macOs:
```bash
brew install cloudflared
cloudflared tunnel --url http://localhost:8000
```

#### Windows
```bash
winget install --id Cloudflare.cloudflared
cloudflared tunnel --url http://localhost:8000
```

### Third Terminal:

Copy the link from your cloudflare Tunnel and reuse it.
```bash
cd src/frontend
NEXT_PUBLIC_BACKEND_WS_URL=YOUR_CLOUDFLARE_LINK  npm run dev
```

### Fourth Terminal
You can use ngrok. For more information look up the [ngrok Website](https://ngrok.com/docs/getting-started#mac-os) or if you have already installed ngrok do following:

```bash
ngrok http 3000
```
