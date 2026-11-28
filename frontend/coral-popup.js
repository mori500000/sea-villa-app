(() => {
  const mountPopup = () => {
    if (document.getElementById("coral-popup")) return;

    const style = document.createElement("style");
    style.textContent = `
      #mc-tank-overlay {
        position: fixed;
        inset: 0;
        z-index: 2500;
        display: none;
        flex-direction: column;
        background: rgba(3, 10, 20, 0.88);
        backdrop-filter: blur(8px);
        padding: 20px;
        box-sizing: border-box;
        color: #f1f5f9;
      }
      #mc-tank-overlay.is-open {
        display: flex;
      }
      #mc-tank-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        margin-bottom: 12px;
      }
      #mc-tank-title {
        font-size: 16px;
        font-weight: 700;
      }
      #mc-tank-actions {
        display: flex;
        align-items: center;
        gap: 8px;
      }
      .mc-tank-btn {
        border: 1px solid rgba(148, 163, 184, 0.35);
        background: rgba(15, 23, 42, 0.9);
        color: #f8fafc;
        border-radius: 8px;
        padding: 8px 14px;
        font-size: 12px;
        font-weight: 600;
        cursor: pointer;
      }
      .mc-tank-btn.primary {
        background: #22c55e;
        color: #052e16;
        border-color: transparent;
        font-weight: 700;
      }
      #mc-tank-frame {
        position: relative;
        flex: 1;
        min-height: 0;
        border-radius: 16px;
        overflow: hidden;
        border: 3px solid rgba(186, 230, 253, 0.35);
        box-shadow: inset 0 0 60px rgba(255, 255, 255, 0.08), 0 20px 50px rgba(0, 0, 0, 0.65);
        background: #061526;
      }
      #mc-tank-svg {
        width: 100%;
        height: 100%;
        display: block;
      }
      #mc-tank-footer {
        margin-top: 10px;
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        justify-content: space-between;
        gap: 8px;
        font-size: 12px;
        color: #cbd5e1;
      }
      #mc-tank-params {
        font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
        font-size: 11px;
        background: rgba(15, 23, 42, 0.85);
        padding: 6px 10px;
        border-radius: 6px;
        word-break: break-all;
      }
    `;
    document.head.appendChild(style);

    const container = document.createElement("div");
    container.id = "coral-popup-root";
    container.innerHTML = `
      <div id="coral-popup" role="dialog" aria-label="サンゴの海シミュレーション結果">
        <div id="coral-popup-header">
          <span>サンゴの海プレビュー</span>
          <button id="coral-popup-close" type="button" aria-label="閉じる">×</button>
        </div>
        <svg id="coral-scene-svg" viewBox="0 0 280 130" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <linearGradient id="seaGrad" x1="0" y1="0" x2="0" y2="1">
              <stop id="seaGradTop" offset="0%" stop-color="#00B4D8" />
              <stop id="seaGradBottom" offset="100%" stop-color="#007791" />
            </linearGradient>
          </defs>
          <rect x="0" y="0" width="280" height="130" fill="#061526" />
          <rect id="seaSurfaceRect" x="0" y="18" width="280" height="112" fill="url(#seaGrad)" opacity="0.82" />
          <path d="M0,18 Q35,14 70,18 T140,18 T210,18 T280,18" fill="none" stroke="#bae6fd" stroke-width="1.5" opacity="0.7" />
          <path d="M0,106 Q70,100 140,107 T280,104 L280,130 L0,130 Z" fill="#cbd5e1" opacity="0.35" />

          <g id="coralGroup">
            <!-- 左：枝サンゴ -->
            <path data-bleach-stroke="#fb7185"
                  d="M46,108 L46,76 M46,90 L32,74 M46,84 L60,70 M32,74 L26,62 M32,74 L38,61 M60,70 L66,58"
                  stroke="#fb7185" stroke-width="5.5" stroke-linecap="round" fill="none" />

            <!-- 中央左：テーブルサンゴ -->
            <g>
              <rect data-bleach-fill="#c084fc" x="108" y="88" width="8" height="20" rx="3" fill="#c084fc" />
              <ellipse data-bleach-fill="#a855f7" cx="112" cy="88" rx="30" ry="7" fill="#a855f7" />
              <ellipse data-bleach-fill="#e879f9" cx="112" cy="84" rx="22" ry="5" fill="#e879f9" />
            </g>

            <!-- 中央右：塊状＋枝サンゴ -->
            <ellipse data-bleach-fill="#f472b6" cx="176" cy="102" rx="22" ry="9" fill="#f472b6" />
            <path data-bleach-stroke="#fda4af"
                  d="M176,100 L176,78 M176,88 L162,75 M176,86 L190,74"
                  stroke="#fda4af" stroke-width="4.5" stroke-linecap="round" fill="none" />

            <!-- 右：オレンジ枝サンゴ -->
            <path data-bleach-stroke="#fb923c"
                  d="M236,108 L236,80 M236,92 L222,78 M236,88 L250,76"
                  stroke="#fb923c" stroke-width="5.5" stroke-linecap="round" fill="none" />
          </g>
        </svg>
        <div id="coral-popup-meta"></div>
        <button id="minecraft-bridge-btn" type="button">マインクライフ連携へ進む</button>
      </div>

      <div id="mc-tank-overlay" role="dialog" aria-modal="true" aria-label="マインクラフト海底水槽ビュー">
        <div id="mc-tank-header">
          <div id="mc-tank-title">海底水槽ビュー（マインクラフト連携プレビュー）</div>
          <div id="mc-tank-actions">
            <button id="mc-copy-btn" class="mc-tank-btn primary" type="button">連携パラメータをコピー</button>
            <button id="mc-tank-close" class="mc-tank-btn" type="button">閉じる (Esc)</button>
          </div>
        </div>
        <div id="mc-tank-frame">
          <svg id="mc-tank-svg" viewBox="0 0 1200 620" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <linearGradient id="mcTankWaterGrad" x1="0" y1="0" x2="0" y2="1">
                <stop id="mcTankGradTop" offset="0%" stop-color="#00B4D8" />
                <stop id="mcTankGradMid" offset="55%" stop-color="#007791" />
                <stop id="mcTankGradBottom" offset="100%" stop-color="#041c2c" />
              </linearGradient>
            </defs>

            <rect x="0" y="0" width="1200" height="620" fill="#051322" />
            <rect id="mcTankWaterRect" x="0" y="42" width="1200" height="578" fill="url(#mcTankWaterGrad)" opacity="0.88" />

            <polygon points="160,42 320,42 460,520 120,520" fill="#ffffff" opacity="0.06" />
            <polygon points="520,42 710,42 890,520 560,520" fill="#ffffff" opacity="0.05" />
            <polygon points="880,42 1030,42 1150,520 920,520" fill="#ffffff" opacity="0.04" />

            <path d="M0,42 Q75,34 150,42 T300,42 T450,42 T600,42 T750,42 T900,42 T1050,42 T1200,42"
                  fill="none" stroke="#e0f2fe" stroke-width="3" opacity="0.75" />

            <path d="M0,470 L130,420 L260,465 L410,435 L580,475 L760,430 L960,468 L1200,425 L1200,620 L0,620 Z"
                  fill="#0f172a" opacity="0.55" />

            <path d="M0,515 Q300,498 600,518 T1200,508 L1200,620 L0,620 Z" fill="#cbd5e1" opacity="0.42" />

            <g id="mcTankCoralGroup">
              <!-- 1. 左端：枝サンゴ（ローズピンク） -->
              <g data-bleach-stroke="#fb7185" stroke="#fb7185" stroke-width="14" stroke-linecap="round" fill="none">
                <path d="M150,520 L150,390" />
                <path d="M150,450 L98,395" />
                <path d="M150,425 L202,375" />
                <path d="M98,395 L78,350" />
                <path d="M98,395 L122,348" />
                <path d="M202,375 L226,332" />
              </g>

              <!-- 2. 左中：テーブルサンゴ（大型・パープル〜マゼンタ段状） -->
              <g>
                <!-- 幹 -->
                <path data-bleach-fill="#9333ea" d="M352,516 L362,438 L388,438 L398,516 Z" fill="#9333ea" />
                <!-- 下段テーブル -->
                <ellipse data-bleach-fill="#a855f7" cx="375" cy="442" rx="115" ry="20" fill="#a855f7" />
                <ellipse data-bleach-fill="#c084fc" cx="375" cy="434" rx="108" ry="15" fill="#c084fc" />
                <!-- 上段テーブル -->
                <ellipse data-bleach-fill="#d946ef" cx="385" cy="414" rx="74" ry="14" fill="#d946ef" />
                <ellipse data-bleach-fill="#f0abfc" cx="385" cy="408" rx="64" ry="10" fill="#f0abfc" />
              </g>

              <!-- 3. 中央：塊状サンゴ＋枝サンゴ（ピンク） -->
              <ellipse data-bleach-fill="#f472b6" cx="585" cy="508" rx="78" ry="24" fill="#f472b6" />
              <g data-bleach-stroke="#fda4af" stroke="#fda4af" stroke-width="11" stroke-linecap="round" fill="none">
                <path d="M585,500 L585,418" />
                <path d="M585,456 L538,410" />
                <path d="M585,446 L634,404" />
              </g>

              <!-- 4. 右中：テーブルサンゴ（エメラルド・ターコイズ段状） -->
              <g>
                <!-- 幹 -->
                <path data-bleach-fill="#0d9488" d="M774,515 L782,452 L804,452 L812,515 Z" fill="#0d9488" />
                <!-- 下段テーブル -->
                <ellipse data-bleach-fill="#14b8a6" cx="793" cy="454" rx="96" ry="17" fill="#14b8a6" />
                <ellipse data-bleach-fill="#2dd4bf" cx="793" cy="447" rx="88" ry="13" fill="#2dd4bf" />
                <!-- 上段テーブル -->
                <ellipse data-bleach-fill="#38bdf8" cx="782" cy="430" rx="58" ry="11" fill="#38bdf8" />
                <ellipse data-bleach-fill="#7dd3fc" cx="782" cy="425" rx="48" ry="8" fill="#7dd3fc" />
              </g>

              <!-- 5. 右端：サンゴ群（オレンジ） -->
              <ellipse data-bleach-fill="#fb923c" cx="1025" cy="508" rx="75" ry="24" fill="#fb923c" />
              <g data-bleach-stroke="#fdba74" stroke="#fdba74" stroke-width="12" stroke-linecap="round" fill="none">
                <path d="M1025,500 L1025,400" />
                <path d="M1025,450 L978,406" />
                <path d="M1025,438 L1075,398" />
              </g>
            
              <g class="table-coral-mc">
                <path data-bleach-fill="#9333ea" d="M356,516 L365,446 L389,446 L398,516 Z" fill="#9333ea" />
                <ellipse data-bleach-fill="#a855f7" cx="377" cy="448" rx="112" ry="18" fill="#a855f7" />
                <ellipse data-bleach-fill="#c084fc" cx="377" cy="441" rx="104" ry="14" fill="#c084fc" />
                <ellipse data-bleach-fill="#d946ef" cx="386" cy="422" rx="72" ry="13" fill="#d946ef" />
                <ellipse data-bleach-fill="#f0abfc" cx="386" cy="417" rx="62" ry="9" fill="#f0abfc" />
              </g>
              <g class="table-coral-mc">
                <path data-bleach-fill="#0d9488" d="M778,515 L785,456 L805,456 L812,515 Z" fill="#0d9488" />
                <ellipse data-bleach-fill="#14b8a6" cx="795" cy="458" rx="94" ry="16" fill="#14b8a6" />
                <ellipse data-bleach-fill="#2dd4bf" cx="795" cy="451" rx="86" ry="12" fill="#2dd4bf" />
                <ellipse data-bleach-fill="#38bdf8" cx="785" cy="435" rx="56" ry="10" fill="#38bdf8" />
                <ellipse data-bleach-fill="#7dd3fc" cx="785" cy="430" rx="46" ry="7" fill="#7dd3fc" />
              </g>
</g>

            <rect x="8" y="8" width="1184" height="604" rx="14" fill="none" stroke="#ffffff" stroke-opacity="0.14" stroke-width="2" />
          </svg>
        </div>
        <div id="mc-tank-footer">
          <div id="mc-tank-summary"></div>
          <div id="mc-tank-params"></div>
        </div>
      </div>
    `;
    document.body.appendChild(container);

    const setAttrSafe = (el, name, val) => {
      if (el && typeof el.setAttribute === "function") {
        el.setAttribute(name, val);
      }
    };

    const popupEl = document.getElementById("coral-popup");
    const closeBtn = document.getElementById("coral-popup-close");
    const topStop = document.getElementById("seaGradTop");
    const bottomStop = document.getElementById("seaGradBottom");
    const metaEl = document.getElementById("coral-popup-meta");
    const mcBtn = document.getElementById("minecraft-bridge-btn");

    const tankOverlay = document.getElementById("mc-tank-overlay");
    const tankCloseBtn = document.getElementById("mc-tank-close");
    const tankCopyBtn = document.getElementById("mc-copy-btn");
    const tankGradTop = document.getElementById("mcTankGradTop");
    const tankGradMid = document.getElementById("mcTankGradMid");
    const tankGradBottom = document.getElementById("mcTankGradBottom");
    const tankSummary = document.getElementById("mc-tank-summary");
    const tankParams = document.getElementById("mc-tank-params");

    let latestPayload = null;
    let latestQueryString = "";

    const scaleHex = (hex, factor = 0.65) => {
      const clean = (hex || "#00B4D8").replace("#", "");
      if (clean.length !== 6) return "#007791";
      const rgb = [0, 2, 4].map((i) =>
        Math.max(0, Math.min(255, Math.round(parseInt(clean.slice(i, i + 2), 16) * factor)))
      );
      return "#" + rgb.map((v) => v.toString(16).padStart(2, "0")).join("");
    };

    // 白骨化率 pct (0〜100) に応じて元の色から完全な白 (#ffffff) へ線形補間
    const mixWithWhite = (baseHex, pct) => {
      const clean = (baseHex || "#ffffff").replace("#", "");
      if (clean.length !== 6) return "#ffffff";
      const t = Math.max(0, Math.min(1, pct / 100));
      const rgb = [0, 2, 4].map((i) => {
        const c = parseInt(clean.slice(i, i + 2), 16);
        return Math.round(c + (255 - c) * t);
      });
      return "#" + rgb.map((v) => v.toString(16).padStart(2, "0")).join("");
    };

    const applyCoralBleaching = (pct) => {
      document.querySelectorAll("[data-bleach-fill]").forEach((el) => {
        const base = el.getAttribute("data-bleach-fill");
        el.setAttribute("fill", mixWithWhite(base, pct));
      });
      document.querySelectorAll("[data-bleach-stroke]").forEach((el) => {
        const base = el.getAttribute("data-bleach-stroke");
        el.setAttribute("stroke", mixWithWhite(base, pct));
      });
    };

    const applySeaVisuals = ({ seaHex, pct }) => {
      setAttrSafe(topStop, "stop-color", seaHex);
      setAttrSafe(bottomStop, "stop-color", scaleHex(seaHex, 0.65));

      setAttrSafe(tankGradTop, "stop-color", seaHex);
      setAttrSafe(tankGradMid, "stop-color", scaleHex(seaHex, 0.72));
      setAttrSafe(tankGradBottom, "stop-color", scaleHex(seaHex, 0.35));

      applyCoralBleaching(pct);
    };

    window.showCoralPopup = ({ hexColor, bleachingRate, year, lat, lon, locationName }) => {
      const seaHex = hexColor || "#00B4D8";
      const pct = Math.max(0, Math.min(100, Number(bleachingRate ?? 0)));

      latestPayload = { locationName: locationName || "", lat, lon, year, bleachingRate: pct, seaHex };
      latestQueryString = new URLSearchParams({
        lat: String(lat ?? ""),
        lon: String(lon ?? ""),
        year: String(year ?? ""),
        bleaching: String(pct),
        sea_hex: seaHex,
      }).toString();

      applySeaVisuals({ seaHex, pct });
      if (metaEl) {
        metaEl.innerHTML = `白化率: <b>${pct}%</b> ／ 海色: <code>${seaHex}</code>` + (year ? ` ／ ${year}年` : "");
      }
      if (popupEl) popupEl.classList.add("is-open");
    };

    const openTankView = () => {
      const payload = latestPayload || {
        locationName: "",
        lat: "",
        lon: "",
        year: "",
        bleachingRate: 0,
        seaHex: "#00B4D8",
      };
      applySeaVisuals({ seaHex: payload.seaHex, pct: payload.bleachingRate });

      const locLabel = payload.locationName ? `${payload.locationName} ／ ` : "";
      const yearLabel = payload.year ? `${payload.year}年 ／ ` : "";
      if (tankSummary) {
        tankSummary.textContent = `${locLabel}${yearLabel}白化率 ${payload.bleachingRate}% ／ 海色 ${payload.seaHex}`;
      }
      if (tankParams) {
        tankParams.textContent = latestQueryString || `bleaching=${payload.bleachingRate}&sea_hex=${payload.seaHex}`;
      }
      if (tankOverlay) tankOverlay.classList.add("is-open");
    };

    const closeTankView = () => {
      if (tankOverlay) tankOverlay.classList.remove("is-open");
    };

    if (closeBtn) closeBtn.addEventListener("click", () => popupEl && popupEl.classList.remove("is-open"));
    if (mcBtn) mcBtn.addEventListener("click", openTankView);
    if (tankCloseBtn) tankCloseBtn.addEventListener("click", closeTankView);

    if (tankCopyBtn) {
      tankCopyBtn.addEventListener("click", async () => {
        const text = (tankParams && tankParams.textContent) || "";
        if (!text) return;
        try {
          if (navigator.clipboard && navigator.clipboard.writeText) {
            await navigator.clipboard.writeText(text);
            const prev = tankCopyBtn.textContent;
            tankCopyBtn.textContent = "コピー済み";
            setTimeout(() => {
              tankCopyBtn.textContent = prev;
            }, 1400);
          }
        } catch (_) {}
      });
    }

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && tankOverlay && tankOverlay.classList.contains("is-open")) {
        closeTankView();
      }
    });
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", mountPopup);
  } else {
    mountPopup();
  }
})();
