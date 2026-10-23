# ErgoSNM rev4.1 外殼

使用 build123d 設計的外殼，對應的 PCB 在 `../pcb`。

## 環境

需要 [uv](https://docs.astral.sh/uv/) 與 KiCad 10（`kicad-cli`）。

```powershell
uv sync
uv run python tools/setup.py     # 匯出 PCB STEP 到 step/（已是最新則跳過）
uv run python tools/check.py     # 設計檢查
uv run python tools/render.py    # 渲染到 build/renders/
uv run pytest -q
```

`step/` 與 `build/` 是衍生檔，不進版控，PCB 改版後重跑 `tools/setup.py` 即可。

VS Code 預覽：安裝「OCP CAD Viewer」，Python 直譯器選 `.venv`，執行 `src/assembly.py`。
agent 的工作方式見 [CLAUDE.md](CLAUDE.md)。

## 目錄

| 路徑 | 內容 |
| :--- | :--- |
| `docs/` | 設計方向、調查資料、決策記錄、進度（`status.md`） |
| `refs/` | 規格書與原廠尺寸圖（手動加入） |
| `tools/` | 可執行腳本：setup、export_step、check、render |
| `src/params.py` | 共用參數 |
| `src/pcb_ref.py` | 從 `.kicad_pcb` 讀取孔位、鍵位和外框 |
| `src/geometry.py` | KiCad 座標轉案體座標 |
| `src/parts/` | 各個零件 |
| `src/assembly.py` | 組合與預覽 |
| `tests/` | pytest |
| `step/`、`build/` | 衍生檔（不進版控） |
