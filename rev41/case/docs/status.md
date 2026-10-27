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

## 上蓋大輪廓草稿（`src/outline.py`，`top_skin(hand)`）
- 外觀件：平面輪廓不跟 PCB 階梯。**左手**（依使用者畫的紅線）：主板+核心板的凸包 ∪ 拇指板區 ∪ 兩者間的窄連接區，
  外偏移 2.5 mm（0.5 間隙 + 2 壁），再用 `CONCAVE_FILLET`（6 mm）圓滑凹角（shapely）；罩得住核心板。
  **右手**暫時仍是全部的凸包（先不處理）。
- 上表面 = 主平面（z = 3.8）與拇指傾斜面兩者取較低，相交處是一條折線；再往下 `PLATE_T` 取同樣的面得到板厚（2026-10-23 由 1.5 改 1.9 mm）。
- 拇指板（兩手）整體抬高 `THUMB_LIFT_Z = 3.07`，使折線落在拇指 PCB 內側邊緣往主板方向約 1.6 mm（外牆範圍內）。
- 右手球孔中心改為內側 2x2 鍵（2x3 板 SW2/3/6/7）的中心：(77.2, −141.9, −3.8)（板頂面上）；
  rev4 右側 FreeCAD 的球孔位置比這裡靠近主板約 29 mm，已不採用。
- 側壁與螺絲柱（`src/topcase.py`，僅左手）：壁厚 `BOTTOM_WALL` 2.0，沿上表面法線往下 `SEAM_DEPTH` 6.1 mm
  （板頂到 PCB 底 3.8 + 熱插拔座 1.8 + 0.5），接縫面隨主平面／拇指斜面折疊。螺絲柱 Ø7.8（螺母口 Ø3.8 外壁 2.0）放在
  PCB 外框與外牆之間的空角，目前 4 根（上方缺口 1、下緣 2、拇指頸部 1），螺母口在接縫面開口、螺絲孔 Ø2.8 盲孔到蒙皮下 0.5 mm。
  外框在拇指區多放 `THUMB_TILT_MARGIN` 0.7 mm（傾斜的板與熱插拔座向側面凸出）。拇指區左手整體往主板滑 `THUMB_LEFT_SHIFT_IN` 3.0 mm。
- 尚未：鍵軸開孔（蒙皮目前還被軸體穿過）、PCB/電池避讓槽、球孔、與下蓋的接合；整體尺寸 >100 mm 的 JLC 壁厚表要求 2.0 mm，
  蒙皮已改 1.9 mm（接近 2.0）；板底到 PCB 頂面只剩 0.3 mm，二極體（1.2 mm）與軸體卡榫都要開避讓槽。

## 拇指區外牆垂直於板面
- `outline.plan_prism`：主板側用鉛直柱，拇指側（以兩頂面的平分面為界）用沿板面法線的斜柱，所以拇指區外牆與接縫跟傾斜的板面成 90°。
- 牆在深處往主板方向傾倒（板底 3.8 mm 處約 1.4 mm），所以拇指區輪廓在下坡端多加這個量（`_left_outline_polygon` 內的 `lean`）。

## 鍵軸開孔（`topcase.key_cutouts`，左手）
- 主板 29 + 拇指 6 個軸，各開 `SWITCH_BODY`(13.95) + `CUTOUT_COMP` 的方孔，沿各自板面法線切穿蒙皮（拇指區斜面也是正方形）。
- 板下避讓槽（`topcase.relief_cutouts`）：由主板／拇指板 STEP 取板面朝定位板側高於 `PLATE_PCB_GAP` 的零件（二極體 1.2 mm、
  兩排 2x10 排母凸出的針腳 12.5×2.1），在蒙皮底面挖出外擴 `RELIEF_XY_CLEAR` 0.3、上方留 `RELIEF_Z_CLEAR` 0.2 的槽，
  蒙皮與兩板的干涉為 0。二極體處蒙皮剩約 0.8 mm（< JLC 2.0 mm 壁厚建議，待評估）。軸體卡榫在方孔內，不另開。
- LED 導光槽（`topcase.led_slots`）：板面朝定位板側的 2 顆 LED（LD1、LD3）各挖一條槽，寬 = LED + 0.6，沿板 Y 軸通到
  最近且對齊的鍵軸孔；槽頂留蒙皮 `LED_SLOT_SKIN` 0.8 mm。
- `CUTOUT_COMP` 待 coupon 決定。

## 對位用的簡化模型（`src/placeholders.py`）
- 核心板有三個連接器槽（KiCad x 136.525 / 152.4 / 168.275，y = 50.8）：F.Cu 的 USB-C J4、J9、J1，以及 B.Cu 的開關 SW1 / SW2（與 J4 / J1 同位置）。
  左手依使用者指示：兩個 USB-C = J4、J9，開關 = SW2（案體座標 X 29.2 / 45.1 / 61.0，俯視由左到右：開關、USB、USB）。
- USB-C：8.94 × 7.35 × 3.26，前緣在 footprint +3.9，超出核心板邊 1.36 mm；開關 SK12D07：本體 8.6 × 4.5 × 4.7（高度讀自圖面，待確認），
  手柄 2.0 × 2.7 × 7 mm 伸出板邊約 6.7 mm。`render.py` 與 `assembly.py` 會顯示（洋紅=開關、銀=USB）。
- 電池連接器 JST S2B-PH-SM4-TB（`J8`，F.Cu）：7.9 × 7.6 × 5.5 方塊（footprint fab 外框，高度讀自圖面），掛在核心板下方（最低 z = −12.6），開口朝板下緣方向；青色顯示。
- 右手：假設為左手的鏡像（USB-C J1、J9，開關 SW1，J8；見「Right hand, R1」，待確認）。

## 下一步
0. （已完成）PCB 外框多邊形：`pcb_ref.outline_loops/outline_area`（含封裝內的郵票孔邊緣）、
   `geometry.outline_in_case(board, hand)`。thumb 拼板是一個相連的外框（兩塊以兩個連接片相連，中間有一個挖空）。
1. P1：用簡化方塊補上缺模型的零件（`src/placeholders.py`），需要使用者提供尺寸。
2. P2：測試片腳本（Choc V2 開孔、螺母卡槽、鋼珠座、電池槽、陰影槽）。
3. 第一個零件穩定後執行 `check.py --update-baseline`。

## 待使用者回答 / 提供
- 電池連接器（JST PH S2B-PH-SM4-TB）、USB-C、SK12D07、E73 的外形尺寸：原廠圖面已放在 `refs/drawings/`，建模時再讀；
  SK12D07 為直角型，手柄 7 mm 從 USB 孔那一側伸出（需確認是從本體頂面算起）。
- 你的 PMW3610 小板是否與參考圖一樣：感測器本體在背離球的那一面、鏡頭穿過板上的窗口朝向球（見下方堆疊）；板厚 1.6 mm。
- 鍵帽實際高度（`KEYCAP_H` 目前用 4.0 mm 估計）與電池盒尺寸 583×142×322 的單位與軸向
  （目前讀成 58.3 × 14.2 × 32.2 mm，14.2 低於 AA 直徑 14.5，請確認哪一軸是高度）。
- 球座與感測器小板怎麼固定：尚未決定。

## 已知事項
- **緊固件**：螺絲 M2.5×6 / M2.5×4（頭 Φ5.5 × 1.3）；螺母銅花齒 M2.5×2×3.5（內徑×高×外徑，壁僅 0.5，
  不在廠商表格內，表上最接近 M2.5×3×4）。樹脂不能熱熔，以瞬間膠 / 含橡膠瞬間膠 / AB 環氧固定。孔徑與間隙
  （`SCREW_M25_CLEAR_D`、`NUT_POCKET_CLEAR`）待螺母卡槽測試片決定。
- **電池盒**位置：左手主板下方，鍵軸 kx=101.6 與 120.65 兩欄（各 4 列）的範圍，左手案體座標 X 73.7–111.8、
  Y −117.5 – −39.0（38.1 × 78.5）；盒 58.3 × 32.2 放得下（長邊沿 Y，餘裕 20 × 6 mm），離核心板約 7 mm。
  Z 方向要避開主板下面的熱插拔座（koktoh `socket/step/choc.step`，總高 3.05 mm，其中一部分在 PCB 厚度內，凸出 PCB 面僅 1.8 mm（使用者確認），
  永遠在軸體的反面＝下面，比二極體 1.2 mm 高）：盒頂面 Z ≈ −2.3（主板下面為 0），盒高 14.2 時盒底 −16.5，加 0.5 間隙與 2 mm 壁 → 下蓋底 ≈ −19.0，
  比核心板區域（−15.1）深約 4 mm。盒的「高度」是哪一軸仍待確認。
- **PMW3610 垂直尺寸鏈**（`refs/drawings/pmw3610-lens.png`，距球面）：鏡頭參考面 2.40（± 0.2）、板的朝球面 5.80、
  板的感測器面 7.40、晶粒 7.83、感測器本體頂 9.05；板厚 1.60，鏡頭伸出板朝球面 3.40。感測器本體在板的
  背球面，鏡頭穿過板上窗口朝向球（小板已確認與參考圖相同：IC 焊在 F.Cu，鏡頭凸出 B.Cu，所以 B.Cu 朝球、F.Cu 朝下）。沿板法向、從球面最近點往下（`geometry.sensor_stack()`，右手案體座標）：
  距板面下 26.7（球面）/ 29.1（鏡頭）/ 32.5（板朝球面）/ 34.1（板感測器面）/ 35.75（本體頂）mm；
  z = −23.2 / −25.4 / −28.6 / −30.1 / −31.7。再加間隙 0.5 與壁 2 → 球座處下蓋底 z ≈ −34.0
  （傾斜的板角還會更低）。±0.2 的工作距離與 SLA 公差相同，需墊片調整；感測器小板固定在球座上。
- **球高計算**（沿定位板法向，`params`）：Choc V2 圖面的 6.4 mm 是軸心頂到凸緣底（= 定位板表面），
  軸心高出外殼頂 3.1 mm，所以外殼頂在板上 3.3 mm；鍵帽 4.0 mm、底緣在外殼頂 → 鍵帽頂 7.3 mm。
  球頂與鍵帽頂等高 → 球心在板面下 17 − 7.3 = **9.7 mm**，球最低點在板面下 26.7 mm。
  鍵帽頂每增加 1 mm，球心深度減 1 mm。右手球心 ≈ (109.4, −142.9, −7.2)，球最低點 z ≈ −24.2
  （`geometry.ball_center()`）。
- **腳架高度的影響（估算）**：核心板區域最低零件 z = −12.6（含 5.5 mm 連接器），加 0.5 mm 間隙與 2 mm 壁 → 下蓋底 ≈ −15.1；
  球座處球最低點 −24.2，再加感測器、支撐與壁（尚未設計）後至少約 −30，比主體低約 15 mm（拇指板往外傾斜下去）。
  腳架／整機高度要以球座底為依據；電池盒（高 14.2）放置後主體下蓋底也要重算。
- **右手 `thumb_1x2` 與軌跡球**：右手 = 左手拇指區的鏡像，內側 2x2 鍵換成軌跡球，保留外側 1x2。依據
  rev4 右側 FCStd：傾斜面只剩 2 個鍵孔（與左側 2x3 第一欄 SW1/SW5 的孔位完全相同）加 1 個球孔
  （約 35.3 × 36.5，取直徑 36.5）。`PLACEMENTS["right"]["thumb_1x2"]` 與 `BALL_HOLE_CENTER_RIGHT` 由此推得，
  同樣是 20° 傾斜。1x2 板的 SW4/SW8 對應 2x3 板的 SW1/SW5。
- **手性**：main_board 是 reversible，左右手共用同一片。右手 F.Cu 朝上；左手翻面（B.Cu 朝上）。
  `params.HAND` 預設為 `left`；`PLACEMENTS[hand]` 給每塊板的 R、t（STEP 區域座標 → 案體座標）。
- **左手干涉風險**：B.Cu 朝上時，29 顆 SOD-323（模型高 1.2）、R_0402（0.44）、B.Cu 的 LED（1.19）與 TL3342（1.63）
  都在定位板下方，只有 `PLATE_PCB_GAP` = 0.3 mm（定位板改 1.9 mm 後），定位板底面要開避讓槽（1.2 mm 高的二極體要挖 ≥ 0.5 mm 深，另加間隙）。右手 F.Cu 朝上時，這些在板下方，
  而 F.Cu 的 2 顆 LED（1.19）則在定位板下方，同樣要開避讓（TL3342 只焊下面，上面那顆不存在）。
  核心板在左手也在主板下方 -Z，面對面間距 5.5 mm（對稱，沿用右手位姿，X 對位翻面後的排母）。BTN1/BTN2、2x10 排母只焊在實際下面：`assembly._fit_main_board` 依手性處理——只保留下面那一顆 TL3342（右手 BTN1/B.Cu、左手 BTN2/F.Cu），左手把兩個 2x10 排母從 B.Cu 鏡射到 F.Cu 面（下面，面向核心板）。
- **thumb_cluster 是拼板**：兩塊以郵票孔連接，`params.THUMB_BOARDS`：`thumb_2x3`（左手，X 116.84–175.29，
  6 顆軸體，FPC J1）、`thumb_1x2`（右手，X 177.29–197.61，2 顆軸體，FPC J2）。載入時用布林切割分開。
- **左手 `thumb_2x3` 位置**由 `rev4/case/ErgoSNM_case_left.FCStd` 解析：傾斜面法向傾斜剛好 20.00°，
  6 個孔 6/6 吻合 2x3 軸體；主區 29 孔中 28 個吻合主板（X 鏡像 = 翻面）。左手座標系：
  X 同 FreeCAD，Y = Y_fc − 60.023，Z = Z_fc − 6.6 + 3.8。板翻面所以板的 +Z 朝下：傾斜 160°（板面傾斜 20°）、yaw 150°。
  位於主板右下方，與主板無 XY 重疊。連到核心板的 FPC 長度還沒量。
- 定位板 1.9 mm（原 1.5），定位板頂面到 PCB 頂面 2.2 mm（Choc V2 凸緣底高度：圖面 5.30 − 3.10，實測約 2.2；先前的 1.65 是讀錯標記），
  所以板底到 PCB 頂面 0.7 mm（卡榫上緣在 0.6）；定位板與軸體凸緣之間有 0.2 mm 餘裕以內的誤差。PCB 完全靠軸體吊著，
  定位板下方只有 0.7 mm 空間，不能做墊高柱；定位銷只能穿過 PCB 孔。PCB 外框外才有空間做螺絲柱與支撐。
- J7（2x5 燒錄座）NPI：不焊（`CORE_J7_POPULATED = False`）。
- PCB 實際厚度 1.6 mm（使用者確認）；KiCad STEP 基板為 1.51 mm，差 0.09 mm，干涉檢查時略偏小。
- STEP 中兩塊板的排針/排母模型互相穿插，是 KiCad 通用模型造成，不代表實際干涉。

## Wall openings for USB-C and the slide switch (left)
The PCB hangs on the top case, so the openings are cut in the top case wall. `topcase.wall_openings`: the part of each
placeholder that reaches the +Y wall, grown by `WALL_OPEN_CLEAR` 0.6 (the handle slot also by `SLIDE_SW_TRAVEL`/2 each side).
TODO: `SLIDE_SW_TRAVEL` and the handle position from the SK12D07 drawing; USB plug overmold size; battery J8 wire exit.

## Nested bottom plate (left, 2026-10-24; replaces the seam at 6.1 / 16.7 deep and the set-back step)
- The top case walls run from the top surface all the way down. The bottom case is a 2.0 mm plate inside them
  (`PLATE_SIDE_CLEAR` 0.2 to the wall's inner face), its outer face `BOTTOM_RECESS` 0.8 up from the wall's bottom edge:
  from the side only the top case shows, from below the seam is a ring inside the wall edge.
- Plate outer face (`topcase.floor_depths` / `below_floor`) = lower of two planes: Z = -19.0 under the main plate (battery
  holder bottom -16.5 + 0.5 + 2.0) and 8.1 mm below the thumb plate along its normal. The main side is one flat 23 mm deep box for now.
- Posts (Ø7.8) run along the local top-plane normal from the skin down to the plate's inner face (`post_axis`); the nut pocket is
  open at the post's lower end, blind Ø2.8 hole `POST_HOLE_LEN` 5.0 above. M2.5 x 6 from below: head in a 0.6 counterbore
  (0.7 proud, inside the 0.8 recess), 1.4 of plate, 3.3 into the post.
- Head counterbores (Ø6.0) are cut through the plate and the wall's bottom edge alike (`topcase.screw_counterbores`): two posts sit near
  the wall; the one at (76.3, -36.1) has its hole only 1.2 mm from the plate edge, so the plate is notched there (TODO move that post).
- Not yet: battery compartment and door, J8 wire, feet, the plate's support between posts (it only rests on the 4 post ends),
  posts vs the battery holder (no holder model yet), shaping the underside shallower away from the battery / core board.

## Floor profile, battery holder and +Y edge (2026-10-24)
- +Y outline edge: the hull gets an extra point at the main board's right edge (`MAIN_TOP_RIGHT_GROW` 5.9, from the user's red line), so the
  edge runs nearly straight from the core board corner (66.6, -30.8) to (115, -35.8) instead of dropping to -39.9.
- Battery holder placeholder (`placeholders.battery_holder`): X 76.65-108.85, pushed against the +Y wall (Y -94.3 ~ -36.0, Z -16.5 ~ -2.3);
  its footprint is a post keep-out (`pcb_union`).
- Bottom plate outer face (`topcase.floor_profile`, only a function of Y on the main side): Z -19.0 from the +Y wall to 2.0 mm past the
  battery tail (Y -96.3), 45 degree ramp (`BOTTOM_RAMP_ANGLE`) up to Z -4.3 (socket 1.8 + 0.5 + plate 2.0); thumb side unchanged
  (plane 8.1 deep, lower envelope). Posts in the shallow zone are 6.1 long and their blind hole is limited to stay 0.5 under the skin.
- The +Y strip post (73.8, -34.2) is still trimmed (about 57% of the boss kept): a whole boss needs the edge about 4 mm further out there.
- Wall openings now use the wall position at each part's X (the outline max Y is no longer the flat edge).

## Stepped underside, tenting, feet and support pillars (left, 2026-10-24)
- Plate outer face (`topcase.floor_profile` / `floor_z`) = the shallower of two stepped profiles, each with ramps:
  X: Z -4.3 at -X (sockets only) -> -15.0 under the core board (J8 bottom -12.5) -> -19.0 under the battery holder;
  Y: -19.0 from the +Y wall to 2 mm past the battery tail (Y -96.3) -> -4.3. Thumb side: plane 8.1 mm below the thumb plate.
  The top case walls follow it (BOTTOM_RECESS below). Screw heads must sit on a flat level: a ramp moves off a post or
  gets steeper (X ramps now ~72 deg at X 17.6-21.0, ~57 deg at X 67.2-69.8; the +Y post (73.8, -34.2) sits on the deep level).
- Tenting (`TENT_ANGLE` 10 deg, TODO user): desk plane tilted about Y, +X (thumb side) up (`bottomcase.desk_plane`), as high
  as the walls' bottom edge allows with `FOOT_END_T` 1.5 + `FOOT_MIN_CLEAR` 1.0. Feet columns Ø8 (`FEET_LEFT`, near the
  user's four circles) perpendicular to the desk, ending on the pads: lengths ~11.5 / 11.5 (-X), 14.9 (battery corner), 28.1 (thumb neck).
- Support pillars at main-board holes H2, H3, H4 (`SUPPORT_HOLES_LEFT`): a Ø5 body up to Z -2.3 (under the hot-swap sockets)
  and a Ø1.8 pin through the Ø2.2 hole touching the skin underside. Free radius around the holes from the F.Cu socket pads
  (estimate, the STEP has no sockets): H3/H4 ~3.4 mm, H2 ~1.3 mm. H1 is under the battery holder; H5, H6 unused for now.
  At H2/H4 (shallow level) the pillar is only the pin. Pin top touches the skin at zero nominal gap (SLA +-0.2: check on print).
- Not yet: rubber pad recess at the column ends, thumb-key stability outside the feet (6 thumb keys + a few edge keys are outside
  the four feet), battery door, J8 wire.
- Thumb: a 5th foot column at thumb board hole H5 (123.4, -140.1), ~24.8 long; a 10 mm ledge on the thumb end wall
  (`thumb_ledge`, a rectangle centred on the middle of the thumb end edge) 2.0 past the wall's inner face, from the plate's
  inner face up to 0.3 under the thumb PCB; the thumb board goes in tilted past it.
- Later: the thumb-neck foot was dropped; feet are now (2, -124), (2, -55), (100, -45) (on the battery door), H5. Two posts are
  hand-shifted away from the edge (`BOSS_SHIFT_LEFT`): (57.6, -134.2) and (92.3, -138.9).

## Battery door (left, 2026-10-24)
- `batterydoor.py`: the 2xAA holder is glued onto a 2.0 mm door (MJF PA12) flush in a pocket of the plate's outer face.
  Three mushroom studs (Ø2.5, head Ø5 x 1.5 with a 0.5 lead-in chamfer, root fillet 0.3; two on the -X edge, one on the
  +X edge) hang it from keyholes (Ø6.0 with a 0.4 entry chamfer + 3.1 slot along Y; the +X one 0.6 wider along X so only
  the -X pair locates) in the plate, which is thickened 2.0 inside around the opening. Push the door 4 mm towards +Y and
  it drops out with the holder (wires stay connected); pushed back to -Y a 0.8 bump on a 6 x 12 tongue at the -Y end
  clicks into a dimple. Clearances from the JLC guideline for moving parts (0.6 total): slot/stud and pocket sides 0.3 per
  side, vertical 0.3 + 0.3. The door's X edges lap 7.5 under the plate, -Y 2.5, +Y 1.0; door and pocket are notched around
  the corner post's counterbore (1.5 of plate kept). Door top edge chamfer 0.4, pocket floor edge 0.3; grip grooves.
- Holder moved to X 67.2-99.4 (0.5 past the core board), Y -104.4 ~ -46.1, Z -17.0 ~ -2.8 (on the door). The deep level of
  the floor now covers the pocket + 1 mm: X from 58.2 (under the core board's right part, the core-level step is X 21-54),
  Y down to -108.4.
- The +Y strip post (73.8, -34.2) is replaced by a fixed corner post (109.5, -38.6) (`BOSS_FIXED_LEFT`, ~95% of the boss).
- Holder nest (user, 2026-10-27, `batterydoor.nest`): the door's top face has a 0.5 deep nest for the glued holder, its footprint + 0.3 (glue gap),
  so the holder is located in X and Y. The holder stays where it was (floor unchanged): the door is `BATTERY_FLOOR_T` 2.0 thick under
  it and `BATTERY_DOOR_T` 2.5 round it, the plate's rim went up to `BATTERY_RIM_H` 2.5 so the ceiling over the door is still 1.7
  thick, and the pocket ceiling, stud heads and keyholes rose 0.5 with the door top. The tongue (6 x 12) is recessed with the nest from
  y0 + 2.7 on (its stiffness is as before), the bump (0.8 above the door top) sits outside the nest. Foot columns and flares stay under
  the nest floor; the edge rib no longer enters the pocket (it ended 0.1 inside the sliding door's footprint). Both hands.
- Foot (105, -45) moved to (100, -45) so it stands wholly on the door; the door carries it (desk load goes into the laps).
- Feet moved inward (user, 2026-10-26), so the root flares (radius 6.5) are not cut by the plate edge / the door edge: the -X pair
  from x 2.0 to 4.5 (edge 5.7 -> 8.2), the door foot from (100, -45) to (98, -48.5) (+Y door edge 4.4 -> 7.9, +X 7.4 -> 9.4, post notch
  7.0 -> 10.4). The right hand mirrors them (+X pair, door foot on the core board's -X side). `FEET_LEFT` is shared by both hands.
- Battery wire (J8 to the holder): not modelled, it lies loose inside the shell (user). J8 is about 54-80 mm from the holder's
  +Y end in a straight line; leave about 150 mm so the door can be pushed 4 mm and the holder dropped out of the plate.
- Ribs (`bottomcase.ribs`, `foot_flares`): (1) every foot column root gets a conical flare (+2.5 radial over 3.75, clipped to the
  plate outline / door slab, the door's one also to the post notch); (2) an edge rim 1.5 x 4.0 along the +Y and +X plate edge on
  the deep level, starting 1.0 past the core board's right edge (the USB-C is there); (3) a bar 1.5 x 5.0 across the strip between
  the battery opening and the pocket's +Y end, 1.0 from the opening, with a 12 mm gap centred on the holder for the wire. Both rims
  keep clear of the post cylinders (Ø8.4).
- Support pillars (H2-H4): a 45 degree shoulder at the Ø1.8 pin root (1.0 wide at H2 where the plate is 7 mm below; only 0.3 at H3/H4
  where the plate's inner face is already 0.7 under the sockets) and a 0.3 chamfer at the pin tip as a lead-in into the PCB hole.
  The shoulder top stays 0.2 under the sockets (`PIN_SHOULDER*`, `PIN_TIP_CHAMFER`).
- Tactile dots (`topcase.tactile_bumps`, `TACTILE_*`): two Ø3.0 x 0.8 domes on the +Y wall's outer face, 2.5 from the opening edge to
  the dot centre: below the middle USB-C (J9, centred on its opening, z -13.4) and beside the slide switch (SW2, at the opening's mid
  height, on its +X side, x 35.8). 0.8 is the JLC minimum emboss. TODO: the USB plug overmold size is unknown (the dot is 1.0 from the
  opening's lower edge); the case's +Y bounding box now stands 0.8 proud of the wall there.
- USB-C wall openings are rounded rectangles: corner radius = shell fillet 1.2 (drawing TYPE-C-31-M-12, shell 8.94 x 3.26, corner R about
  1.2-1.3) + 0.6 clearance = 1.8, concentric with the receptacle; the switch slot stays rectangular.
- TODO: bump/tongue stiffness on a print test.
- Rubber feet Ø6 x 2.0 (user): each column end has a Ø6.4 x 0.5 recess, so the column ends `FOOT_END_T` = 1.5 above the
  desk (same geometry as before) and the pad stands 1.5 proud.

## Right hand, R1: the left case mirrored (2026-10-25)
- The right case frame is the left one mirrored about X = `MIRROR_X`/2 (X_right = 203.847 - X_left): main board and core board
  map exactly. `THUMB_SHIFT_IN` (3.0 towards the main board) now applies to both hands, so the right 1x2 keys sit exactly where
  the left 2x3 outer column is mirrored; `BALL_HOLE_CENTER_RIGHT` moved with it (ball centre now (82.7, -138.8, -12.9)).
- Mirrored from the left (no right-hand tuning): outline (`case_outline_polygon`), floor (`floor_profile` / `below_floor` /
  `floor_z`), posts incl. shifts and the corner post, battery holder and door (two studs on the core board side, the third floats),
  ribs, feet positions; the desk tilts with the inner (-X) side up. Right bottom case and door have the left ones' volume exactly.
- Computed for the right boards: key openings (main + 1x2), PCB reliefs and LED slots (F.Cu up), USB-C / switch openings and
  tactile dots, thumb ledge, Ø36.5 ball hole through the thumb plate along its normal.
- Right core board population assumed as the mirror of the left (TODO confirm): USB-C J1 + J9, switch SW1 (dot on its -X side), J8.
- Ball hole 0.7 from the wall's inner face, ball 2.3 from the thumb_1x2 board (handled in R2 below).

## Right hand, R2: ball cup, sensor and pod (2026-10-25, `src/trackball.py`)
- User: nothing holds the ball (tip the keyboard over to take it out; also before opening the battery door); PMW3610 board on
  FPC (J2 AFC01-S08FCA-00, 2.0 high, no pin header), cable 150 mm (not modelled, like the battery wire); keep the outline and
  lower the cup rim instead.
- Ball frame: ball centre, u uphill along the thumb plate, v across, n plate normal; sensor axis along n.
- Cup (separate part, gold): shell Ø34 + 2 x 0.8 gap, 1.5 wall, rim 7.0 below the ball centre (about 2.4 to the
  arm walls), trimmed to radius 18.46 (0.5 inside the pod wall); three Ø2.5 steel balls at 45 deg from the pole (user) (azimuth 0/120/240 from +u) in
  blind seats Ø2.5 with Ø5.5 bosses, plus a second set of three seats at 49 deg, azimuths 60/180/300 (midway), to try the steeper
  angle on the same cup (fit one set or the other; the 49 deg bosses reach 16.52 from the axis); seat block 32 x 25 (top 14.5 below the ball centre) for the board; lens window 19 x 11 + 0.5
  (TODO lens outline) and a recess over U1's through-hole pins on B.Cu (pads + 1.0).
- PMW3610 board: long side along u, FPC end uphill, B.Cu (lens) up. Sandwich (user): four M2.5 x 10 socket head screws (head
  Ø4.5 x 2.5, user has them) come up through the pod floor (counterbore Ø5.0 x 1.7, head 0.8 proud = BOTTOM_RECESS, so no lower
  than the walls' edge), a Ø5.0 x 3.5 standoff on the floor, the board and the shims into nuts in the seat block: 3.8 under the
  head, 4.4 into the cup (whole nut + blind hole). The seat sits 0.2 nearer the ball than nominal, shims set the 2.4 working
  distance (+-0.2). M2.5 x 12 would go through the block.
- Pod (round, bottom plate only; user: the top case walls stay as on the left): a cup on the ball axis hanging below the arm,
  inner radius 18.96 (the sensor board's R3 corners, 18.46 from the axis, + 0.5: the board shifts up to 0.35 on its screws),
  outer 20.96, flush with the arm walls (20.98); floor parallel to
  the thumb plate, 0.5 under the FPC connector (outer face 28.9 below the ball centre = 38.6 below the plate top); bottom edge
  rounded R2.5 inside / R4.5 outside. Over the arm walls it starts at the plate edge 0.2 under the walls' bottom edge and widens
  at 45 degrees; the opening up into the arm keeps 0.6 round the ball (wall ~1.2 there, on the arm's two sides only). Outline,
  walls and the plate around the pod are the mirrored left ones (`below_floor(..., pod=False)`). The cup is trimmed to radius
  18.46. FPC connector -> pod wall about 4. Taking the bottom plate off brings the cup and the board with it.
- The thumb foot (FEET_LEFT[THUMB_FOOT]) stands under the middle of the pod on the right. The post next to the crease moves
  2.5 uphill (`BOSS_SHIFT_RIGHT`, at the 0.4 PCB clearance) so it stays out of the pod.
- Raised 5 (user, `BALL_RAISE`; first 10, then 5 back): the whole module (ball, cup, sensor, pod) moves 5 up along the plate normal:
  the ball centre is 4.7 below the plate top and the ball top 5 above the keycap tops. The pod hangs 14.5 under the walls and the
  desk plane is 5 higher than at BALL_RAISE 0 (-57.4, was -62.3): every foot column is ~5 shorter. The arm's flat plate has a
  17.6 cavity round the pod neck (the plate edge is 18.8 out, so it cannot widen); the cup rim (7.0 below the centre, 6.0 at
  BALL_RAISE 0) stays where the neck's 45 deg cone widens: 0.4 to the plate, 0.2 under the 49 deg boss tops, ball -> plate 0.66.
  With BALL_RAISE 10 the rim had to go to 9.0.
- Collar round the ball hole (user, `topcase.ball_collar`): a 2.0 wall hangs from the skin underside along the plate normal down to the
  bottom plate's inner face (like the posts), so the ball sits in a closed shaft; inner radius = the hole (18.25), outer 20.25, so it
  merges with the arm walls on the two sides. The thumb_1x2 board's edge is only 0.16 outside the hole edge (18.41 from the axis in
  the plate plane), so on that side the wall is cut back to the board outline + 0.3 and what is left thinner than 1.0 is dropped:
  an open slot about 36 deg (11.5 mm) wide, with the wall growing back 1.0 -> 2.0 over the next 8 deg each side. Nothing of the
  collar touches the boards, ball or cup.
- The ball hole's top edge has a 0.8 x 45 deg chamfer (user, `BALL_HOLE_CHAMFER`; cut in the skin only, the collar below is unchanged).
- Cables (user: both FPCs go through the pod, option A; lens 12.9 x 8.1 and FPC connector 10 x 4.5 are now the real sizes). The core
  board's FPC connectors J5 / J6 are at (158.8 / 171.5, -84.1), opening towards -Y, on its lower face; the free height map over the
  right plate (11-15 mm in the deep area, 1.0 over the battery holder, 0.5 under the main board's sockets) gives a corridor along
  y = -110 from the crease to the core board. The ball and the collar close the thumb arm, so there are two cable windows
  (`trackball.fpc_windows`, 8 wide, radius 16.8 - 19.3 from the axis, one on each side along the arm) through the plate ring and the
  pod wall (>= 1.6 of wall left beside them), and a 2.0 high arch in the collar's lower edge on the uphill side (`fpc_arch`); on the
  downhill side the collar's slot at the thumb board is the way out. The standoffs are 3.5 high (`BALL_POD_FLOOR_CLEAR` 1.5, was
  0.5; user): under the sensor board along v = 0 there are 1.85 under the IC and 1.5 under the FPC connector (was 0.85 / 0.5), 3.6
  beside them but only 1.2 wide between the IC and the standoffs, and 6.5 wide round the cup block (v 12.5 - 19). Cable lengths (planar + up/down in the
  pod): sensor -> J5 about 125 mm, thumb J2 -> J5 about 190-230 mm (the user buys the cables).
- Height: the lowest points are the pod's rounded edge and the sensor screw heads (`trackball.lowest_points`).
- TODO: test print of the cup (steel-ball seat fit, working distance / shims, rolling); FPC connector width/depth and the lens
  outline from drawings; FPC route from the pod to the core board; the pod is a separate grey cup below the orange walls.
