# 進度與待辦

更新：2026-10-23（P0 完成；手性與拇指區已建模）

## 已完成（P0 基礎建設）
- `tools/setup.py`、`tools/export_step.py`：可重現的 STEP 匯出（manifest + 雜湊，過期才重匯）。
- `tools/check.py`（`--fast`、`--update-baseline`）：STEP 新鮮度、實體有效性、板外框包含、排針對位、
  板間距、PCB 厚度；對已登錄零件檢查有效性、JLC 最大尺寸、最小壁厚（依尺寸級別）、零件間與零件對 PCB
  的干涉（`params.ALLOWED_INTERFERENCE` 列刻意的例外）、`docs/baseline.json` 回歸比對。
- `src/parts/__init__.py`：零件登錄（`register(name, build, material)`），`check`/`render`/`assembly` 自動載入。
- `tools/render.py` + `src/viz.py`：pyvista 離屏渲染（iso/top/front/side、剖面）。
- `src/analysis.py`：干涉體積、薄壁取樣（沿表面法線向內射線）、尺寸上限。
- 測試：座標轉換、分析函式，以及用故意做壞的零件驗證 check 流程確實會失敗。

## 尚未涵蓋的檢查
- 最小孔徑、最小凸字等需要特徵辨識的 JLC 規則（目前靠設計時遵守 `params.py`）。
- 零件間最小間隙（目前只檢查體積重疊，不檢查是否留有 0.2/0.5 mm 的組裝間隙）。
- 薄壁取樣是抽樣（預設 4000 點），可能漏掉很小的薄處；定稿前可加大取樣數。

## 下一步
1. P1：用簡化方塊補上缺模型的零件（`src/placeholders.py`），需要使用者提供尺寸。
2. P2：測試片腳本（Choc V2 開孔、螺母卡槽、鋼珠座、電池槽、陰影槽）。
3. 第一個零件穩定後執行 `check.py --update-baseline`。

## 待使用者回答 / 提供
- 電池連接器（JST PH S2B-PH-SM4-TB）、USB-C、SK12D07、E73 的外形尺寸：原廠圖面已放在 `refs/drawings/`，建模時再讀；
  SK12D07 為直角型，手柄 7 mm 從 USB 孔那一側伸出（需確認是從本體頂面算起）。
- 右手側 `thumb_1x2` 的位置（相對主板、軌跡球）：rev4 的右側 FCStd 主區孔位與左側完全相同，無法直接沿用，
  需要你提供或從新設計決定。

## 已知事項
- **手性**：main_board 是 reversible，左右手共用同一片。右手 F.Cu 朝上；左手翻面（B.Cu 朝上）。
  `params.HAND` 預設為 `left`；`PLACEMENTS[hand]` 給每塊板的 R、t（STEP 區域座標 → 案體座標）。
- **左手干涉風險**：B.Cu 朝上時，29 顆 SOD-323（模型高 1.2）、R_0402（0.44）、B.Cu 的 LED（1.19）與 TL3342（1.63）
  都在定位板下方，只有 `PLATE_PCB_GAP` = 0.15 mm，定位板底面要開避讓槽。右手 F.Cu 朝上時，這些在板下方，
  而 F.Cu 的 2 顆 LED（1.19）則在定位板下方，同樣要開避讓（TL3342 只焊下面，上面那顆不存在）。
  核心板在左手也在主板下方 -Z，面對面間距 5.5 mm（對稱，沿用右手位姿，X 對位翻面後的排母）。BTN1/BTN2、2x10 排母只焊在實際下面：`assembly._fit_main_board` 依手性處理——只保留下面那一顆 TL3342（右手 BTN1/B.Cu、左手 BTN2/F.Cu），左手把兩個 2x10 排母從 B.Cu 鏡射到 F.Cu 面（下面，面向核心板）。
- **thumb_cluster 是拼板**：兩塊以郵票孔連接，`params.THUMB_BOARDS`：`thumb_2x3`（左手，X 116.84–175.29，
  6 顆軸體，FPC J1）、`thumb_1x2`（右手，X 177.29–197.61，2 顆軸體，FPC J2）。載入時用布林切割分開。
- **左手 `thumb_2x3` 位置**由 `rev4/case/ErgoSNM_case_left.FCStd` 解析：傾斜面法向傾斜剛好 20.00°，
  6 個孔 6/6 吻合 2x3 軸體；主區 29 孔中 28 個吻合主板（X 鏡像 = 翻面）。左手座標系：
  X 同 FreeCAD，Y = Y_fc − 60.023，Z = Z_fc − 6.6 + 3.25。板翻面所以板的 +Z 朝下：傾斜 160°（板面傾斜 20°）、yaw 150°。
  位於主板右下方，與主板無 XY 重疊。連到核心板的 FPC 長度還沒量。
- 定位板 1.5 mm，板外面到 PCB 上面 1.65 mm，所以板下與 PCB 之間只有 0.15 mm：PCB 完全靠軸體吊著，
  定位板下方不能做墊高柱；定位銷只能穿過 PCB 孔。PCB 外框外才有空間做螺絲柱與支撐。
- J7（2x5 燒錄座）NPI：不焊（`CORE_J7_POPULATED = False`）。
- PCB 實際厚度 1.6 mm（使用者確認）；KiCad STEP 基板為 1.51 mm，差 0.09 mm，干涉檢查時略偏小。
- STEP 中兩塊板的排針/排母模型互相穿插，是 KiCad 通用模型造成，不代表實際干涉。
