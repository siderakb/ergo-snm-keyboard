# rev41/case — 外殼設計（build123d）

## 開始 session 前
1. 讀 `docs/status.md`（進度、下一步、待使用者回答的問題）與 `docs/decisions.md`。
2. `uv run python tools/setup.py`（STEP 已是最新會自動跳過）。
3. 結束前更新 `docs/status.md`，有新的設計決定寫進 `docs/decisions.md`。

## 指令（皆在本目錄執行）
| 指令 | 用途 |
| :--- | :--- |
| `uv sync` | 建立環境 |
| `uv run python tools/setup.py` | 檢查 kicad-cli 並匯出 STEP 到 `step/` |
| `uv run python tools/check.py` | 全部設計檢查（失敗時 exit 1），結果寫入 `build/report.json` |
| `uv run python tools/render.py [--hand left\|right] --view iso\|top\|front\|side [--section y=-60] [--out NAME]` | 離屏渲染到 `build/renders/*.png`，用 Read 看圖 |
| `uv run pytest -q` | 單元測試 |

修改幾何後的迴圈：改程式 → `check.py` → `render.py` → 看報告與圖 → 修正，通過再結束。
不要要求使用者開 VS Code 預覽，除非是外觀或手感的判斷。

## 慣例
- 單位 mm。main_board 是 reversible，左右手共用：右手 F.Cu 朝上，左手翻面（B.Cu 朝上）。
  `params.HAND`（預設 left）決定預設手性；`params.PLACEMENTS[hand]` 給每塊板「STEP 區域座標
  （X = KiCad x，Y = -KiCad y，Z 從 B.Cu 面起算）→ 案體座標」的 R、t。
  KiCad → 案體座標一律經 `src/geometry.py:to_case(board, kx, ky, kz, hand=)`。
- thumb_cluster 是兩塊拼板：`thumb_2x3`（左手）、`thumb_1x2`（右手），見 `params.THUMB_BOARDS`。
- 共用數值只放 `src/params.py`，標 TODO 的是未驗證的假設，使用前先確認。
- `step/`、`build/` 是衍生檔，不進 git、不手改。PCB 改版後重跑 `tools/setup.py`。
- KiCad 的 STEP 缺少部分零件模型（電池連接器、USB-C、E73、滑動開關），不能用 STEP 的 Z 範圍
  決定高度；以 `params.py` 的數值為準。
- 過濾 STEP 零件時只能動最上層 `shape.children`，更深的葉節點的位置是相對父層，取出後會跑掉。
- 使用者提供的數值（如板間距 5.5 mm）視為事實；自己估的或從圖讀的要標示來源。

## 需要使用者的事
尺寸資料缺口、實體打樣結果、外觀與手感判斷。其餘盡量自行在迴圈內完成。
