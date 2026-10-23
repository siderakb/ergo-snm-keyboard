# 參考資料

| 檔案 | 內容 | 備註 |
| :--- | :--- | :--- |
| `drawings/choc_v2.png` | Kailh Choc V2 軸體尺寸圖與建議 PCB 開孔 | 使用者提供截圖 |
| `drawings/SK12D07.png` | SK12D07 滑動開關尺寸圖 | 手柄長 7 mm（使用者） |
| `drawings/TYPE-C-31-M-12.png` | HRO TYPE-C-31-M-12 USB-C 座尺寸圖 | |
| `drawings/JST PH CONNECTOR.png` | JST PH SMT 公座（S2B-PH-SM4-TB 側入型：2 路 A=2.0、B=7.9，深度 6（+2.6）、高 5.5） | 數字讀自圖面，建模時再核對 |
| `drawings/pmw3610.png` | PMW3610 封裝外形（16.2 × 9.1~10.1 × 4.05，腳距 1.78/0.5） | |
| `drawings/pmw3610-lens.png` | PMW3610 參考設計剖面：鏡頭面到追蹤面 2.40、板頂到追蹤面 7.40、板厚 1.60 | |
| `drawings/pmw3610-pcb.png` | PMW3610 小板 KiCad 圖（23.5 × 31.5，M3 ×4，光學中心） | |
| `drawings/螺母參考.png` | 銅花齒熱熔螺母廠商規格表（型號 = 內徑×高度×外徑） | 實際用 M2.5×2×3.5，不在表內 |
| `drawings/E73-2G4M08S1C.png` | E73-2G4M08S1C 模組尺寸圖 | 天線淨空待確認 |

規格書 PDF 放在 `datasheets/`。建模前才從圖面讀尺寸；讀到的數字寫進 `src/params.py` 並註明來源。

## 3D 模型（由 `tools/setup.py` 取得，不進版控）

| 模型 | 來源 | 備註 |
| :--- | :--- | :--- |
| `step/vendor/choc_v2.step` | https://github.com/koktoh/keyswitch_model @2b6bcfa（`choc/v2/step/blue.step`） | 無授權檔，只下載不提交；量測值見 `src/refmodels.py` |
| `step/pmw3610_board.step` | `../pmw3610-pcb/pmw3610_pcb.kicad_pcb`（可用環境變數 `PMW3610_PCB_DIR` 指定，CERN-OHL-P v2） | IC（U1）與 FPC 座沒有 3D 模型，需補簡化方塊；1x7 排針在 F.Cu 面 |
