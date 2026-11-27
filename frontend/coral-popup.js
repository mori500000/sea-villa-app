(() => {
  const mountPopup = () => {
    if (document.getElementById("coral-popup")) return;

    const wrapper = document.createElement("div");
    wrapper.innerHTML = `
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
            <path d="M58,108 L58,76 M58,90 L42,74 M58,84 L73,70 M42,74 L36,62 M42,74 L49,61 M73,70 L79,58"
                  stroke="#fb7185" stroke-width="6" stroke-linecap="round" fill="none" />
            <ellipse cx="140" cy="102" rx="28" ry="11" fill="#f472b6" />
            <path d="M140,100 L140,78 M140,88 L124,75 M140,86 L156,74"
                  stroke="#fda4af" stroke-width="5" stroke-linecap="round" fill="none" />
            <path d="M218,108 L218,80 M218,92 L204,78 M218,88 L232,76"
                  stroke="#fb923c" stroke-width="5.5" stroke-linecap="round" fill="none" />
          </g>
        </svg>
        <div id="coral-popup-meta"></div>
        <button id="minecraft-bridge-btn" type="button">マインクライフ連携へ進む</button>
      </div>
    `;
    document.body.appendChild(wrapper.firstElementChild);

    const popupEl = document.getElementById("coral-popup");
    const closeBtn = document.getElementById("coral-popup-close");
    const topStop = document.getElementById("seaGradTop");
    const bottomStop = document.getElementById("seaGradBottom");
    const coralGroup = document.getElementById("coralGroup");
    const metaEl = document.getElementById("coral-popup-meta");
    const mcBtn = document.getElementById("minecraft-bridge-btn");
    let latestPayload = null;

    const darkenHex = (hex, factor = 0.65) => {
      const clean = (hex || "#00B4D8").replace("#", "");
      if (clean.length !== 6) return "#007791";
      const rgb = [0, 2, 4].map((i) =>
        Math.max(0, Math.min(255, Math.round(parseInt(clean.slice(i, i + 2), 16) * factor)))
      );
      return "#" + rgb.map((v) => v.toString(16).padStart(2, "0")).join("");
    };

    window.showCoralPopup = ({ hexColor, bleachingRate, year, lat, lon, locationName }) => {
      const seaHex = hexColor || "#00B4D8";
      const pct = Math.max(0, Math.min(100, Number(bleachingRate ?? 0)));

      topStop.setAttribute("stop-color", seaHex);
      bottomStop.setAttribute("stop-color", darkenHex(seaHex, 0.65));

      const sat = Math.max(0.15, 1 - (pct / 100) * 0.85);
      const bright = 1 + (pct / 100) * 0.25;
      coralGroup.style.filter = `saturate(${sat.toFixed(2)}) brightness(${bright.toFixed(2)})`;

      latestPayload = { locationName: locationName || "", lat, lon, year, bleachingRate: pct, seaHex };
      metaEl.innerHTML = `白化率: <b>${pct}%</b> ／ 海色: <code>${seaHex}</code>` + (year ? ` ／ ${year}年` : "");
      popupEl.classList.add("is-open");
    };

    closeBtn.addEventListener("click", () => popupEl.classList.remove("is-open"));
    mcBtn.addEventListener("click", () => {
      if (!latestPayload) return;
      const params = new URLSearchParams({
        lat: String(latestPayload.lat ?? ""),
        lon: String(latestPayload.lon ?? ""),
        year: String(latestPayload.year ?? ""),
        bleaching: String(latestPayload.bleachingRate ?? 0),
        sea_hex: latestPayload.seaHex,
      });
      console.log("Minecraft bridge params:", params.toString(), latestPayload);
    });
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", mountPopup);
  } else {
    mountPopup();
  }
})();
