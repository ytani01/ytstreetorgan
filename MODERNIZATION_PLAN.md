# Street Organ Roll Book Maker - モダン化計画書

## 概要

現在の `Tornado` ベースの Web UI を、**FastAPI + Astro** で完全にリプレースし、モダンで使いやすいプラットフォームへ移行します。

**重要：既存のコアロジック（RollBook）は保持され、Python プロジェクト内で統合されます。**

---

## 現在の状態

```
ytstreetorgan/
├── src/ytstreetorgan/
│   ├── __main__.py           ← CLI エントリーポイント
│   ├── webapp.py             ← Tornado Web UI（古い）❌
│   ├── handler1.py           ← リクエストハンドラー（削除予定）❌
│   ├── rollbook.py           ← コアロジック（MIDI → SVG）✅ 保持
│   ├── my_logger.py          ← ロギング機能✅ 保持
│   └── __init__.py
├── webroot/
│   ├── templates/            ← Bootstrap 4.5（古い）❌
│   ├── static/               ← jQuery（古い）❌
│   ├── midi/                 ← アップロード先
│   └── svg/                  ← 出力先
├── pyproject.toml            ← Python 設定
└── README.md
```

**問題点：**
- ❌ Tornado は古い（2020年の Flask より遅い）
- ❌ Bootstrap 4.5 は時代遅れ
- ❌ jQuery による状態管理は保守困難
- ❌ テンプレート混在で スケーラビリティなし

---

## 目標

1. **モダンな UI/UX**
   - Astro + Tailwind CSS で洗練されたインターフェース
   - ドラッグ&ドロップ対応
   - リアルタイム進捗表示（WebSocket）
   - SVG インラインプレビュー

2. **高速でスケーラブルなバックエンド**
   - Tornado → FastAPI へ移行
   - async/await で高速・効率的
   - Threading Queue でシンプルなバックグラウンド処理

3. **Python に集中**
   - フロントエンド・バックエンド を 1 つのリポジトリで管理
   - Node.js は開発・ビルド時のみ（本番は Python 単独）
   - 既存のコアロジック（RollBook）は完全に保持

4. **保守しやすい構成**
   - Python 関連は既存メンテナンス方針を継続
   - フロントエンドは独立した構成で対応可能

---

## アーキテクチャ

### 新しい構成

```
ytstreetorgan/
│
├── src/ytstreetorgan/
│   ├── __main__.py              ← CLI + WebServer（修正）
│   ├── webapp.py                ← FastAPI に置き換え ✅ NEW
│   ├── rollbook.py              ← そのまま ✅
│   ├── my_logger.py             ← そのまま ✅
│   └── __init__.py              ← そのまま
│
├── frontend/                    ← NEW: フロントエンド
│   ├── src/
│   │   ├── pages/
│   │   │   └── index.astro       ← メインページ（静的HTML）
│   │   └── app.js                ← Vanilla JS（軽量）
│   ├── public/
│   ├── dist/                     ← ビルド出力（本番で配信）
│   ├── package.json
│   ├── astro.config.mjs
│   └── tailwind.config.cjs
│
├── webroot/                     ← 削除予定
│   ├── templates/
│   ├── static/
│   └── ...
│
├── pyproject.toml               ← 更新：FastAPI 追加
├── MODERNIZATION_PLAN.md        ← このドキュメント
└── README.md                    ← 更新予定
```

### ランタイム構成

**開発時：**
```
┌──────────────────────┐
│ Astro dev server     │
│ http://localhost:3000│ ← npm run dev
└──────────────────────┘
          ↕ (API proxy)
┌──────────────────────┐
│ FastAPI             │
│ http://localhost:8000│ ← python -m ytstreetorgan webapp
└──────────────────────┘
          ↕
┌──────────────────────┐
│ RollBook (Python)   │
│ Threading Queue     │
└──────────────────────┘
```

**本番時：**
```
┌──────────────────────┐
│ nginx / Gunicorn    │
│ http://example.com   │
└──────────────────────┘
          ↕
┌──────────────────────┐
│ FastAPI + Uvicorn   │
│ (Python)            │
│ - 静的HTML配信      │
│ - API処理           │
│ - WebSocket         │
└──────────────────────┘
          ↕
┌──────────────────────┐
│ RollBook (Python)   │
│ Threading Queue     │
│ ytmidilib           │
└──────────────────────┘
```

---

## 実装戦略

### Phase 1: バックエンド移行（1-2 週間）

#### 1-1. FastAPI へ置き換え

**変更点：**
- `webapp.py`: Tornado → FastAPI
- `handler1.py`: 削除（API ルートに統合）
- API エンドポイント統一

**新しい API:**
```
POST   /api/upload              ← MIDI ファイルアップロード
POST   /api/generate            ← SVG 生成をキューに登録
GET    /api/status/{task_id}    ← 処理状態確認
GET    /api/download/{task_id}  ← SVG ダウンロード
WS     /ws/{task_id}            ← WebSocket（進捗通知）
GET    /health                  ← ヘルスチェック
```

#### 1-2. pyproject.toml 更新

**追加：**
```toml
dependencies = [
  "fastapi",           # ← 新規（Tornado 削除）
  "uvicorn[standard]", # ← 新規
  # 既存は保持
  "click",
  "pygame-ce",
  "ytmidilib",
  "loguru>=0.7.3",
]
```

#### 1-3. CLI インターフェース維持

```bash
# 既存コマンドは変わらない
ytstreetorgan webapp --port 8000 --debug

# 他のコマンドも継続
ytstreetorgan rollbook <midi_file>
ytstreetorgan parse <midi_file>
```

#### 1-4. テスト

```bash
pytest tests/  # 既存テスト継続
```

---

### Phase 2: フロントエンド構築（1-2 週間）

#### 2-1. Astro プロジェクト作成

```bash
cd ytstreetorgan
mkdir frontend
cd frontend
npm create astro@latest . -- --template minimal
npm install
```

#### 2-2. UI コンポーネント実装

- `index.astro`: メインページ（静的 HTML）
- `app.js`: インタラクティブ機能（Vanilla JS）

**特徴：**
- ✅ ドラッグ&ドロップ対応
- ✅ WebSocket で進捗表示
- ✅ SVG インラインプレビュー
- ✅ Tailwind CSS で最小限のコード

#### 2-3. Tailwind CSS 導入

```bash
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

---

### Phase 3: 統合・テスト（1 週間）

#### 3-1. CORS 設定

FastAPI で Astro dev サーバーからのアクセスを許可：
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:4321"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### 3-2. 機能テスト

- [ ] MIDI ファイルアップロード
- [ ] SVG 生成処理
- [ ] WebSocket 進捗通知
- [ ] ダウンロード機能
- [ ] エラーハンドリング

#### 3-3. 互換性テスト

- [ ] 既存 CLI コマンド動作確認
- [ ] RollBook ロジック動作確認
- [ ] ytmidilib 統合確認

---

### Phase 4: ビルド・デプロイ準備（1 週間）

#### 4-1. フロントエンド ビルド

```bash
cd frontend
npm run build  # dist/ に HTML 生成
```

#### 4-2. Python パッケージング

```bash
pip install build
python -m build
```

#### 4-3. Docker 対応（オプション）

```dockerfile
FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install -e .

COPY src ./src

# フロントエンド構築済み HTML をコピー
COPY frontend/dist ./frontend_dist

CMD ["uvicorn", "ytstreetorgan.webapp:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 実装詳細

### FastAPI ベースの webapp.py

```python
# src/ytstreetorgan/webapp.py
import asyncio
import queue
import threading
import uuid
from pathlib import Path
from typing import Dict

from fastapi import FastAPI, UploadFile, File, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import uvicorn

from .rollbook import RollBook
from .my_logger import loggerInit
from loguru import logger


class WebServer:
    """FastAPI ベースの Web サーバー"""
    
    DEF_PORT = 10081
    DEF_WEBROOT = './webroot'
    DEF_WORKDIR = '/tmp/storgan'
    DEF_SIZE_LIMIT = 100 * 1024 * 1024
    
    def __init__(self, port=DEF_PORT, webroot=DEF_WEBROOT,
                 workdir=DEF_WORKDIR, size_limit=DEF_SIZE_LIMIT,
                 version='current', debug=False):
        """Constructor"""
        self._dbg = debug
        logger.info('port={}, workdir={}, size_limit={}',
                   port, workdir, size_limit)
        
        self._port = port
        self._workdir = workdir
        self._size_limit = size_limit
        self._version = version
        
        # ディレクトリ作成
        Path(self._workdir).mkdir(parents=True, exist_ok=True)
        self.upload_dir = Path(self._workdir) / 'midi'
        self.output_dir = Path(self._workdir) / 'svg'
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # グローバル状態
        self.job_queue: queue.Queue = queue.Queue()
        self.task_status: Dict[str, dict] = {}
        self.active_connections: Dict[str, list] = {}
        
        # FastAPI アプリ
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            # 起動時：ワーカースレッド開始
            worker_thread = threading.Thread(
                target=self._worker, daemon=True
            )
            worker_thread.start()
            yield
        
        self.app = FastAPI(
            title="Street Organ Roll Book Maker",
            lifespan=lifespan
        )
        
        # CORS 設定
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=[
                "http://localhost:3000",
                "http://localhost:4321"
            ],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # ルート定義
        self._setup_routes()
    
    def _setup_routes(self):
        """API ルート定義"""
        
        @self.app.post("/api/upload")
        async def upload_midi(file: UploadFile = File(...)):
            """MIDI ファイルアップロード"""
            task_id = str(uuid.uuid4())
            file_path = self.upload_dir / f"{task_id}_{file.filename}"
            content = await file.read()
            
            with open(file_path, "wb") as f:
                f.write(content)
            
            logger.info('Uploaded: {} ({})', file.filename, len(content))
            
            return {
                "task_id": task_id,
                "filename": file.filename,
                "size": len(content),
                "status": "uploaded"
            }
        
        @self.app.post("/api/generate")
        async def generate_rollbook(
            task_id: str,
            model_name: str = "ModelName"
        ):
            """SVG 生成をキューに登録"""
            midi_files = list(
                self.upload_dir.glob(f"{task_id}_*")
            )
            if not midi_files:
                return {"error": "MIDI file not found"}, 404
            
            midi_path = midi_files[0]
            self.job_queue.put((task_id, midi_path, model_name))
            
            self.task_status[task_id] = {
                "status": "queued",
                "progress": 0,
                "message": "Waiting for processing..."
            }
            
            logger.info('Queued: task_id={}', task_id)
            
            return {"task_id": task_id, "status": "queued"}
        
        @self.app.get("/api/status/{task_id}")
        async def get_status(task_id: str):
            """タスク状態確認"""
            return self.task_status.get(
                task_id,
                {"status": "not found"}
            )
        
        @self.app.get("/api/download/{task_id}")
        async def download_svg(task_id: str):
            """SVG ダウンロード"""
            svg_path = self.output_dir / f"{task_id}.svg"
            
            if svg_path.exists():
                logger.info('Downloaded: {}', task_id)
                return FileResponse(
                    svg_path,
                    media_type="image/svg+xml",
                    filename=f"{task_id}.svg"
                )
            
            return {"error": "File not found"}, 404
        
        @self.app.websocket("/ws/{task_id}")
        async def websocket_endpoint(websocket, task_id: str):
            """WebSocket: リアルタイム進捗通知"""
            await websocket.accept()
            
            if task_id not in self.active_connections:
                self.active_connections[task_id] = []
            self.active_connections[task_id].append(websocket)
            
            try:
                while True:
                    status = self.task_status.get(task_id, {})
                    await websocket.send_json(status)
                    
                    await asyncio.sleep(1)
                    
                    if status.get("status") in ["completed", "error"]:
                        break
            
            except WebSocketDisconnect:
                pass
            finally:
                if task_id in self.active_connections:
                    self.active_connections[task_id].remove(
                        websocket
                    )
        
        @self.app.get("/health")
        async def health_check():
            """ヘルスチェック"""
            return {"status": "ok"}
    
    def _worker(self):
        """バックグラウンドワーカースレッド"""
        # 既存のコアロジック利用
        rollbook = RollBook()
        
        while True:
            try:
                task_id, midi_path, model_name = \
                    self.job_queue.get(timeout=1)
            except queue.Empty:
                continue
            
            try:
                logger.info('Processing: {}', task_id)
                
                # 進捗更新
                self.task_status[task_id] = {
                    "status": "processing",
                    "progress": 10,
                    "message": "Analyzing MIDI..."
                }
                
                # 既存のコアロジック実行
                svg_data = rollbook.parse(str(midi_path))
                
                # 進捗更新
                self.task_status[task_id]["progress"] = 80
                self.task_status[task_id]["message"] = \
                    "Generating SVG..."
                
                # SVG 保存
                svg_path = self.output_dir / f"{task_id}.svg"
                with open(svg_path, "w") as f:
                    f.write(svg_data)
                
                # 完了
                self.task_status[task_id] = {
                    "status": "completed",
                    "progress": 100,
                    "message": "Done!",
                    "svg_file": str(svg_path),
                    "svg_filename": f"{task_id}.svg"
                }
                
                logger.info('Completed: {}', task_id)
            
            except Exception as e:
                logger.error('Error in task {}: {}', task_id, str(e))
                self.task_status[task_id] = {
                    "status": "error",
                    "progress": 0,
                    "error": str(e)
                }
            
            finally:
                self.job_queue.task_done()
    
    def main(self):
        """メイン実行"""
        logger.info('Starting FastAPI server on port {}',
                   self._port)
        uvicorn.run(
            self.app,
            host="0.0.0.0",
            port=self._port
        )
```

### Astro メインページ

```astro
<!-- frontend/src/pages/index.astro -->
---
---
<html lang="ja">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Street Organ Roll Book Maker</title>
    <script src="/app.js" defer></script>
    <style>
      * { margin: 0; padding: 0; box-sizing: border-box; }
      body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto;
        background: linear-gradient(to bottom right, #f3f4f6, #e0e7ff);
      }
      .container { max-width: 64rem; margin: 0 auto; padding: 1.5rem; }
      header { background: #4f46e5; color: white; padding: 2rem 0; }
      h1 { font-size: 2.25rem; font-weight: bold; text-align: center; }
      .subtitle { color: #e0e7ff; margin-top: 0.5rem; text-align: center; }
      main { padding: 3rem 0; }
      .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 2rem; }
      .card { background: white; padding: 1.5rem; border-radius: 0.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
      h2 { font-size: 1.5rem; font-weight: bold; margin-bottom: 1rem; }
      button { background: #4f46e5; color: white; padding: 0.75rem 1.5rem; border: none; border-radius: 0.5rem; cursor: pointer; font-weight: bold; }
      button:hover:not(:disabled) { background: #4338ca; }
      button:disabled { opacity: 0.5; cursor: not-allowed; }
      #upload-area { border: 2px dashed #d1d5db; padding: 2rem; text-align: center; border-radius: 0.5rem; }
      #upload-area.dragover { background: #f3f4f6; border-color: #4f46e5; }
      .progress-bar { width: 100%; height: 1rem; background: #e5e7eb; border-radius: 9999px; overflow: hidden; margin-top: 0.5rem; }
      .progress-fill { height: 100%; background: #4f46e5; transition: width 0.3s; }
      .error { background: #fee2e2; color: #991b1b; padding: 1rem; border-radius: 0.5rem; margin-top: 1rem; }
      .success { background: #dcfce7; color: #166534; padding: 1rem; border-radius: 0.5rem; margin-top: 1rem; }
    </style>
  </head>
  <body>
    <header>
      <div class="container">
        <h1>Street Organ Roll Book Maker</h1>
        <p class="subtitle">Convert MIDI files to printable roll book SVGs</p>
      </div>
    </header>

    <main class="container">
      <div class="grid">
        <div>
          <div class="card">
            <h2>Step 1: Upload MIDI</h2>
            <div id="upload-area">
              <p>Drag and drop MIDI file or click to select</p>
              <input type="file" id="file-input" accept=".mid,.midi" style="display: none;">
              <button onclick="document.getElementById('file-input').click()">Select File</button>
            </div>
          </div>

          <div id="model-section" style="display: none;">
            <div class="card" style="margin-top: 1.5rem;">
              <h2>Step 2: Select Model</h2>
              <label style="display: block; padding: 0.75rem; border: 1px solid #d1d5db; border-radius: 0.5rem; cursor: pointer;">
                <input type="radio" name="model" value="ModelName" checked style="margin-right: 0.5rem;">
                <span style="font-weight: 500;">ModelName</span>
                <div style="font-size: 0.875rem; color: #6b7280;">34 notes (default)</div>
              </label>
              <button id="generate-btn" onclick="generate()" style="width: 100%; margin-top: 1rem;">Generate SVG</button>
            </div>
          </div>
        </div>

        <div id="output-section"></div>
      </div>
    </main>
  </body>
</html>
```

### Vanilla JavaScript（軽量）

```javascript
// frontend/src/app.js
let taskId = null;
let selectedModel = 'ModelName';
let ws = null;

const uploadArea = document.getElementById('upload-area');
const fileInput = document.getElementById('file-input');
const modelSection = document.getElementById('model-section');
const outputSection = document.getElementById('output-section');

// ドラッグ&ドロップ
uploadArea.addEventListener('dragover', (e) => {
  e.preventDefault();
  uploadArea.classList.add('dragover');
});

uploadArea.addEventListener('dragleave', () => {
  uploadArea.classList.remove('dragover');
});

uploadArea.addEventListener('drop', (e) => {
  e.preventDefault();
  uploadArea.classList.remove('dragover');
  
  const files = e.dataTransfer.files;
  if (files.length > 0) uploadFile(files[0]);
});

fileInput.addEventListener('change', (e) => {
  if (e.target.files) uploadFile(e.target.files[0]);
});

async function uploadFile(file) {
  const formData = new FormData();
  formData.append('file', file);

  try {
    const res = await fetch('http://localhost:8000/api/upload', {
      method: 'POST',
      body: formData
    });

    const data = await res.json();
    taskId = data.task_id;
    
    uploadArea.innerHTML = `
      <p style="color: #059669; font-weight: bold;">
        ✓ ${data.filename} uploaded (${(data.size / 1024).toFixed(1)} KB)
      </p>
    `;
    uploadArea.style.background = '#f0fdf4';
    uploadArea.style.borderColor = '#86efac';
    
    modelSection.style.display = 'block';
  } catch (error) {
    showError('Upload failed: ' + error);
  }
}

async function generate() {
  const btn = document.getElementById('generate-btn');
  btn.disabled = true;
  btn.textContent = 'Generating...';

  try {
    const res = await fetch('http://localhost:8000/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        task_id: taskId,
        model_name: selectedModel
      })
    });

    if (!res.ok) throw new Error('Generate failed');

    connectWebSocket();
  } catch (error) {
    showError(error.message);
    btn.disabled = false;
    btn.textContent = 'Generate SVG';
  }
}

function connectWebSocket() {
  outputSection.innerHTML = `
    <div class="card">
      <h2>Processing...</h2>
      <div style="margin-bottom: 1rem;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
          <span>Progress</span>
          <span id="progress-percent">0%</span>
        </div>
        <div class="progress-bar">
          <div id="progress-fill" class="progress-fill"></div>
        </div>
      </div>
      <p id="progress-message" style="font-size: 0.875rem; color: #6b7280;"></p>
    </div>
  `;

  ws = new WebSocket(`ws://localhost:8000/ws/${taskId}`);

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    document.getElementById('progress-fill').style.width = data.progress + '%';
    document.getElementById('progress-percent').textContent = data.progress + '%';
    document.getElementById('progress-message').textContent = data.message || '';

    if (data.status === 'completed') {
      ws.close();
      showResult(data.svg_filename);
    } else if (data.status === 'error') {
      ws.close();
      showError(data.error || 'An error occurred');
    }
  };

  ws.onerror = () => {
    showError('WebSocket connection failed');
  };
}

async function showResult(svgFilename) {
  const res = await fetch(`http://localhost:8000/api/download/${taskId}`);
  const svgData = await res.text();

  outputSection.innerHTML = `
    <div class="card">
      <h2>Result</h2>
      <div style="border: 1px solid #d1d5db; border-radius: 0.5rem; padding: 1rem; max-height: 400px; overflow-y: auto;">
        ${svgData}
      </div>
      <a href="http://localhost:8000/api/download/${taskId}" download style="display: block; margin-top: 1rem; background: #059669; color: white; padding: 0.75rem 1.5rem; border-radius: 0.5rem; text-align: center; text-decoration: none; font-weight: bold;">
        ⬇️ Download SVG
      </a>
      <button onclick="location.reload()" style="width: 100%; margin-top: 0.5rem; background: #6b7280;">Start Over</button>
    </div>
  `;
}

function showError(message) {
  outputSection.innerHTML = `
    <div class="error"><strong>Error:</strong> ${message}</div>
  `;
}
```

---

## 実装スケジュール

| フェーズ | 期間 | 内容 |
|---------|------|------|
| **Phase 1** | 1-2 週間 | FastAPI への置き換え、テスト |
| **Phase 2** | 1-2 週間 | Astro フロントエンド構築 |
| **Phase 3** | 1 週間 | 統合テスト、互換性確認 |
| **Phase 4** | 1 週間 | ビルド、デプロイメント準備 |
| **合計** | **1 ヶ月** | 完成 |

---

## 開発環境セットアップ

### 前提条件

- Python 3.13+
- Node.js 20+
- npm 10+

### インストール

```bash
# リポジトリクローン
git clone https://github.com/ytani01/ytstreetorgan.git
cd ytstreetorgan

# Python 環境セットアップ
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Python 依存関係
pip install -e ".[dev]"

# フロントエンド環境
cd frontend
npm install
```

### 開発実行

**ターミナル 1：バックエンド**
```bash
source venv/bin/activate
python -m ytstreetorgan webapp --debug
# または
uvicorn ytstreetorgan.webapp:app --reload
```

**ターミナル 2：フロントエンド**
```bash
cd frontend
npm run dev
```

ブラウザで `http://localhost:3000` にアクセス

---

## 本番デプロイ

### フロントエンド ビルド

```bash
cd frontend
npm run build
# dist/ に静的ファイルが生成される
```

### Python パッケージングと実行

```bash
# ビルド
python -m build

# インストール
pip install dist/ytstreetorgan-*.whl

# 実行
python -m ytstreetorgan webapp --port 8000
```

### Docker での実行（オプション）

```dockerfile
FROM python:3.13-slim

WORKDIR /app

# Node.js を一時的に使用（ビルドのみ）
FROM node:20-alpine AS builder
WORKDIR /app
COPY frontend/ .
RUN npm install && npm run build

# Python イメージ
FROM python:3.13-slim
WORKDIR /app

COPY pyproject.toml .
RUN pip install -e .

COPY src ./src
COPY --from=builder /app/dist ./static

EXPOSE 8000
CMD ["uvicorn", "ytstreetorgan.webapp:app", "--host", "0.0.0.0"]
```

---

## 既存コードの互換性

### 保持される機能

- ✅ **CLI コマンド** - そのまま動作
  ```bash
  ytstreetorgan rollbook input.mid -m ModelName
  ytstreetorgan parse input.mid --visual
  ```

- ✅ **RollBook ロジック** - 完全に保持
  ```python
  from ytstreetorgan import RollBook
  rollbook = RollBook()
  svg = rollbook.parse('input.mid')
  ```

- ✅ **ytmidilib 統合** - 変わらない
  ```python
  from ytmidilib import Parser
  ```

- ✅ **ロギング** - loguru は継続
  ```python
  from loguru import logger
  logger.info('message')
  ```

- ✅ **設定ファイル** - そのまま使用
  ```python
  rollbook = RollBook(model='ModelName', conf_file='storgan.conf')
  ```

### 削除・変更される部分

| 項目 | 現在 | 新規 | 理由 |
|------|------|------|------|
| **Web Framework** | Tornado | FastAPI | モダン化・高速化 |
| **UI Template** | Bootstrap 4.5 | Astro + Tailwind | 最新・軽量 |
| **JavaScript** | jQuery | Vanilla JS | 軽量・依存削減 |
| **HTML ハンドラー** | handler1.py | API Routes | シンプル化 |

---

## テスト戦略

### ユニットテスト

```python
# tests/test_rollbook.py - 既存テスト継続
from ytstreetorgan import RollBook

def test_parse_midi():
    rollbook = RollBook()
    svg = rollbook.parse('test.mid')
    assert '<svg' in svg
```

### API テスト

```python
# tests/test_api.py - 新規
from fastapi.testclient import TestClient
from ytstreetorgan.webapp import WebServer

def test_upload_midi():
    server = WebServer()
    client = TestClient(server.app)
    
    with open('test.mid', 'rb') as f:
        response = client.post(
            '/api/upload',
            files={'file': f}
        )
    
    assert response.status_code == 200
    assert 'task_id' in response.json()
```

### 手動テスト

- [ ] ブラウザでアップロード
- [ ] 進捗表示確認
- [ ] SVG プレビュー確認
- [ ] ダウンロード確認
- [ ] エラーハンドリング確認

---

## トラブルシューティング

### CORS エラー

**症状：** フロントエンドから API 呼び出し時に CORS エラー

**解決：** `webapp.py` の CORS 設定確認
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
)
```

### WebSocket 接続失敗

**症状：** 進捗表示が更新されない

**確認：** 
```bash
# ブラウザコンソールで確認
ws = new WebSocket('ws://localhost:8000/ws/task-id')
```

### ファイル権限エラー

**症状：** `/tmp/storgan/` へのアクセス拒否

**解決：**
```bash
mkdir -p /tmp/storgan/midi /tmp/storgan/svg
chmod 755 /tmp/storgan
```

---

## まとめ

このモダン化計画は以下を実現します：

✅ **UI/UX の大幅な改善**
- モダンなデザイン（Tailwind CSS）
- リアルタイム進捗表示
- 使いやすいインターフェース

✅ **バックエンド高速化**
- Tornado → FastAPI（非同期・効率的）
- シンプルな実装（Threading Queue）

✅ **既存コード活用**
- RollBook ロジックは完全に保持
- CLI コマンドは変わらない
- ytmidilib 統合は継続

✅ **保守性向上**
- 1 つのリポジトリで管理
- Python に集中できる
- 本番環境は Python 単独

✅ **スケーラビリティ**
- 将来的に Celery + Redis に拡張可能
- マイクロサービス化も可能

---

**次ステップ：** Phase 1 の FastAPI 移行から開始

質問や提案があればお知らせください！
