-- 1. 地点マスタ（PostGIS ジオメトリ対応）
CREATE TABLE IF NOT EXISTS locations (
    location_id   VARCHAR(64) PRIMARY KEY,              -- 例: 'site-01'
    name          VARCHAR(120) NOT NULL,                -- 地点名
    region        VARCHAR(120),                         -- 海域・地域名（任意）
    geom          GEOMETRY(Point, 4326) NOT NULL,       -- 経度・緯度 (WGS84: 4326)
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_locations_geom
    ON locations USING GIST (geom);


-- 2. 気候シナリオ
CREATE TABLE IF NOT EXISTS climate_scenarios (
    scenario_id          BIGSERIAL PRIMARY KEY,
    scenario_name        VARCHAR(100) NOT NULL,           -- 例: 'SSP2-4.5_2050_1.5C'
    target_year          INTEGER NOT NULL,                -- 対象年（例: 2050）
    temperature_anomaly  DOUBLE PRECISION NOT NULL,       -- 気温偏差 (°C)（例: 1.5）
    description          TEXT,                          -- 補足・前提条件
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (scenario_name, target_year, temperature_anomaly)
);


-- 3. シミュレーション結果
CREATE TABLE IF NOT EXISTS simulation_results (
    result_id                 BIGSERIAL PRIMARY KEY,
    location_id               VARCHAR(64) NOT NULL
        REFERENCES locations(location_id) ON DELETE CASCADE,
    scenario_id               BIGINT
        REFERENCES climate_scenarios(scenario_id) ON DELETE SET NULL,
    target_year               INTEGER NOT NULL,           -- 実行時の対象年
    temperature_anomaly       DOUBLE PRECISION NOT NULL,  -- 実行時の気温偏差 (°C)
    bleaching_rate_percent    DOUBLE PRECISION NOT NULL,  -- サンゴ白化率 (%)
    coral_status              VARCHAR(64) NOT NULL,       -- 'healthy' / 'partially_bleached' / 'severely_bleached (ruins)'
    turtle_presence_prob      DOUBLE PRECISION NOT NULL,  -- ウミガメ生息確率 (0.0〜1.0)
    raw_payload               JSONB,                      -- 拡張指標や入力パラメータの控え（任意）
    simulated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_simulation_results_loc_year
    ON simulation_results (location_id, target_year);
