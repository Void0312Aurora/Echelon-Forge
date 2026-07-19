// Bilingual (EN / zh-CN) display-only text catalog and localization helpers.
// Language switching never changes session state; it only re-renders labels.

import { vizState } from './store.js';
import { tacticalLayerSpec, tacticalWorkspaceDefinitions } from './symbology.js';

export const I18N_TEXT = Object.freeze({
    en: {
        'ui.brandSub': 'TACTICAL VIZ',
        'ui.tacticalView': 'TACTICAL VIEW',
        'ui.scaleEmpty': 'SCALE --',
        'ui.session': 'SESSION',
        'ui.unloaded': 'UNLOADED',
        'ui.ready': 'READY',
        'ui.running': 'RUNNING',
        'ui.paused': 'PAUSED',
        'ui.loading': 'LOADING',
        'ui.profileSuffix': 'PROFILE',
        'ui.mapWorkspace': 'Map workspace',
        'ui.setup': 'SETUP',
        'ui.data': 'DATA',
        'ui.mapOnly': 'MAP ONLY',
        'ui.exitMap': 'EXIT MAP',
        'ui.reload': 'RELOAD',
        'ui.stop': 'STOP',
        'ui.slow': 'SLOW',
        'ui.fast': 'FAST',
        'ui.speed': 'SPD',
        'ui.speedResetTitle': 'Click to reset speed to 1x',
        'ui.start': 'START',
        'ui.pause': 'PAUSE',
        'ui.resume': 'RESUME',
        'ui.camera': 'CAM',
        'ui.cameraChase': 'CHASE',
        'ui.cameraFree': 'FREE',
        'ui.sessionLifecycle': 'Session lifecycle',
        'ui.simSpeed': 'Simulation speed',
        'ui.panels': 'Panels',
        'ui.waypointShort': 'WP',
        'ui.languageButton': '中文',
        'ui.sessionSetup': 'SESSION SETUP',
        'ui.close': 'CLOSE',
        'ui.profile': 'PROFILE',
        'ui.scenario': 'SCENARIO',
        'ui.assetSet': 'ASSET SET',
        'ui.loadProfile': 'LOAD PROFILE',
        'ui.loadScenario': 'LOAD SCENARIO',
        'ui.load': 'LOAD',
        'ui.loadAssetSet': 'LOAD ASSET SET',
        'ui.tacticalData': 'TACTICAL DATA',
        'ui.workspace': 'WORKSPACE',
        'ui.layers': 'LAYERS',
        'ui.tacticalLayers': 'Tactical layers',
        'ui.telemetry': 'TELEMETRY',
        'ui.time': 'TIME',
        'ui.unit': 'UNIT',
        'ui.altAsl': 'ALT (ASL)',
        'ui.iasGs': 'IAS / GS',
        'ui.heading': 'HEADING',
        'ui.pitch': 'PITCH',
        'ui.roll': 'ROLL',
        'ui.mission': 'MISSION',
        'ui.c2Task': 'C2 TASK',
        'ui.phase': 'PHASE',
        'ui.command': 'COMMAND',
        'ui.waypoint': 'WAYPOINT',
        'ui.sequence': 'SEQUENCE',
        'ui.recentSwitches': 'RECENT SWITCHES',
        'ui.units': 'UNITS',
        'ui.controlsHelp': '[Map Wheel] Zoom | [Map Drag] Pan | [WASD/QE] 3D Free Camera | [Mouse Drag] 3D Orbit | [Space] Pause / Resume',
        'ui.noProfiles': '-- NO PROFILES --',
        'ui.scenarioOnly': 'Scenario only (no profile active)',
        'ui.scenarioOnlyTitle': 'The current session was loaded directly from a scenario.',
        'ui.noScenarios': '-- NO SCENARIOS --',
        'ui.noAssetSets': '-- NO ASSET SETS --',
        'ui.noUnits': 'NO UNITS',
        'ui.unitFallback': 'Unit',
        'ui.layerSuffix': 'layer',
        'ui.grid': 'grid',
        'ui.zoom': 'zoom',
        'ui.meters': 'M',
        'ui.kilometers': 'KM',
        'workspace.cop.label': 'COP',
        'workspace.cop.role': 'COMMON PICTURE',
        'workspace.environment.label': 'ENVIRONMENT',
        'workspace.environment.role': 'ENV / AREAS',
        'workspace.tracks.label': 'TRACKS',
        'workspace.tracks.role': 'SENSORS / LINKS',
        'workspace.inspect3d.label': '3D INSPECT',
        'workspace.inspect3d.role': 'MODEL / ASSET',
        'layer.environment.label': 'Environment overlays',
        'layer.environment.short': 'ENV',
        'layer.environment.summary': 'ENV',
        'layer.route.label': 'Routes and waypoints',
        'layer.route.short': 'ROUTE',
        'layer.route.summary': 'ROUTE',
        'layer.trails.label': 'Movement trails',
        'layer.trails.short': 'TRAIL',
        'layer.trails.summary': 'TRAILS',
        'layer.datalinks.label': 'Datalinks',
        'layer.datalinks.short': 'LINK',
        'layer.datalinks.summary': 'LINKS',
        'layer.sensorRings.label': 'Sensor rings',
        'layer.sensorRings.short': 'RING',
        'layer.sensorRings.summary': 'RINGS',
        'layer.tracks.label': 'Sensor tracks',
        'layer.tracks.short': 'TRACK',
        'layer.tracks.summary': 'TRACKS',
        'layer.weapons.label': 'Weapons and effects',
        'layer.weapons.short': 'WEPN',
        'layer.weapons.summary': 'WEAPONS',
        'layerGroup.environment.label': 'ENVIRONMENT',
        'layerGroup.environment.role': 'terrain / areas',
        'layerGroup.maneuver.label': 'MANEUVER',
        'layerGroup.maneuver.role': 'routes / trails',
        'layerGroup.sensors.label': 'SENSORS',
        'layerGroup.sensors.role': 'tracks / rings / links',
        'layerGroup.effects.label': 'EFFECTS',
        'layerGroup.effects.role': 'weapons / fires',
        'env.surface': 'SURFACE',
        'env.candidate': 'CANDIDATE',
        'env.structure': 'STRUCTURE',
        'env.vegetation': 'VEGETATION',
        'env.water': 'WATER',
        'env.asphalt': 'ASPHALT',
        'env.concrete': 'CONCRETE',
        'env.softdirt': 'SOFTDIRT',
        'env.hardpacked': 'HARDPACKED',
        'env.height': 'H',
        'env.surfaceCode': 'SURF',
        'env.surfaceIndexCode': 'SURF-IDX',
        'env.structureCode': 'STRUCT',
        'env.vegetationCode': 'VEG',
        'env.occlusionCode': 'OCC',
        'mission.task_scramble': 'Scramble',
        'mission.task_cap': 'CAP',
        'mission.task_rtb': 'RTB',
        'mission.task_recover_land': 'Recover Land',
        'mission.idle': 'Idle',
        'mission.takeoff': 'Takeoff',
        'mission.cruise': 'Cruise',
        'mission.rtb': 'RTB',
        'mission.landing': 'Landing',
    },
    zh: {
        'ui.brandSub': '战术可视化',
        'ui.tacticalView': '战术视图',
        'ui.scaleEmpty': '比例尺 --',
        'ui.session': '会话',
        'ui.unloaded': '未加载',
        'ui.ready': '就绪',
        'ui.running': '运行中',
        'ui.paused': '已暂停',
        'ui.loading': '加载中',
        'ui.profileSuffix': '配置',
        'ui.mapWorkspace': '地图工作区',
        'ui.setup': '设置',
        'ui.data': '数据',
        'ui.mapOnly': '仅地图',
        'ui.exitMap': '退出地图',
        'ui.reload': '重载',
        'ui.stop': '停止',
        'ui.slow': '减速',
        'ui.fast': '加速',
        'ui.speed': '速率',
        'ui.speedResetTitle': '点击恢复 1x 速度',
        'ui.start': '开始',
        'ui.pause': '暂停',
        'ui.resume': '继续',
        'ui.camera': '相机',
        'ui.cameraChase': '跟随',
        'ui.cameraFree': '自由',
        'ui.sessionLifecycle': '会话生命周期',
        'ui.simSpeed': '仿真速度',
        'ui.panels': '面板',
        'ui.waypointShort': '航点',
        'ui.languageButton': 'EN',
        'ui.sessionSetup': '会话设置',
        'ui.close': '关闭',
        'ui.profile': '配置',
        'ui.scenario': '场景',
        'ui.assetSet': '资产集',
        'ui.loadProfile': '加载配置',
        'ui.loadScenario': '加载场景',
        'ui.load': '加载',
        'ui.loadAssetSet': '加载资产集',
        'ui.tacticalData': '战术数据',
        'ui.workspace': '工作区',
        'ui.layers': '图层',
        'ui.tacticalLayers': '战术图层',
        'ui.telemetry': '遥测',
        'ui.time': '时间',
        'ui.unit': '单位',
        'ui.altAsl': '海拔',
        'ui.iasGs': '空速 / 地速',
        'ui.heading': '航向',
        'ui.pitch': '俯仰',
        'ui.roll': '横滚',
        'ui.mission': '任务',
        'ui.c2Task': '指挥任务',
        'ui.phase': '阶段',
        'ui.command': '命令',
        'ui.waypoint': '航路点',
        'ui.sequence': '序列',
        'ui.recentSwitches': '近期切换',
        'ui.units': '单位',
        'ui.controlsHelp': '[滚轮] 缩放地图 | [拖拽] 平移地图 | [WASD/QE] 3D 自由相机 | [鼠标拖拽] 3D 环视 | [空格] 暂停 / 继续',
        'ui.noProfiles': '-- 无配置 --',
        'ui.scenarioOnly': '仅场景（无配置）',
        'ui.scenarioOnlyTitle': '当前会话直接从场景加载。',
        'ui.noScenarios': '-- 无场景 --',
        'ui.noAssetSets': '-- 无资产集 --',
        'ui.noUnits': '无单位',
        'ui.unitFallback': '单位',
        'ui.layerSuffix': '图层',
        'ui.grid': '网格',
        'ui.zoom': '缩放',
        'ui.meters': '米',
        'ui.kilometers': '公里',
        'workspace.cop.label': '态势图',
        'workspace.cop.role': '共同态势',
        'workspace.environment.label': '环境',
        'workspace.environment.role': '环境 / 区域',
        'workspace.tracks.label': '航迹',
        'workspace.tracks.role': '传感器 / 链路',
        'workspace.inspect3d.label': '3D 检查',
        'workspace.inspect3d.role': '模型 / 资产',
        'layer.environment.label': '环境叠加',
        'layer.environment.short': '环境',
        'layer.environment.summary': '环境',
        'layer.route.label': '路线与航路点',
        'layer.route.short': '路线',
        'layer.route.summary': '路线',
        'layer.trails.label': '移动轨迹',
        'layer.trails.short': '轨迹',
        'layer.trails.summary': '轨迹',
        'layer.datalinks.label': '数据链',
        'layer.datalinks.short': '链路',
        'layer.datalinks.summary': '链路',
        'layer.sensorRings.label': '传感器范围',
        'layer.sensorRings.short': '范围',
        'layer.sensorRings.summary': '范围',
        'layer.tracks.label': '传感器航迹',
        'layer.tracks.short': '航迹',
        'layer.tracks.summary': '航迹',
        'layer.weapons.label': '武器与效果',
        'layer.weapons.short': '武器',
        'layer.weapons.summary': '武器',
        'layerGroup.environment.label': '环境',
        'layerGroup.environment.role': '地形 / 区域',
        'layerGroup.maneuver.label': '机动',
        'layerGroup.maneuver.role': '路线 / 轨迹',
        'layerGroup.sensors.label': '传感器',
        'layerGroup.sensors.role': '航迹 / 范围 / 链路',
        'layerGroup.effects.label': '效果',
        'layerGroup.effects.role': '武器 / 火力',
        'env.surface': '地表',
        'env.candidate': '候选',
        'env.structure': '建筑',
        'env.vegetation': '植被',
        'env.water': '水体',
        'env.asphalt': '沥青',
        'env.concrete': '混凝土',
        'env.softdirt': '软土',
        'env.hardpacked': '硬实地',
        'env.height': '高',
        'env.surfaceCode': '地表',
        'env.surfaceIndexCode': '地表索引',
        'env.structureCode': '建筑',
        'env.vegetationCode': '植被',
        'env.occlusionCode': '遮蔽',
        'mission.task_scramble': '起飞警戒',
        'mission.task_cap': '空中巡逻',
        'mission.task_rtb': '返航',
        'mission.task_recover_land': '回收着陆',
        'mission.idle': '待机',
        'mission.takeoff': '起飞',
        'mission.cruise': '巡航',
        'mission.rtb': '返航',
        'mission.landing': '着陆',
    },
});

export const ENVIRONMENT_LABEL_ZH = Object.freeze({
    'ao test terrain extent': '测试地形范围',
    'blue base hardstand': '蓝方基地硬化地面',
    'msr asphalt east west': '东西向沥青主补给路',
    'village north south road': '村庄南北道路',
    'dirt track to treeline': '通向林线土路',
    'village center concrete yard': '村庄中心混凝土院',
    'soft field west': '西侧软质田地',
    'irrigation ditch water': '灌溉水渠',
    'contact line degraded ground': '接触线退化地面',
    'vegetation north tree belt': '北侧林带',
    'vegetation west tree patch': '西侧树丛',
    'vegetation south orchard': '南侧果园',
});

export function i18n(key, fallback = '') {
    const lang = I18N_TEXT[vizState.uiLanguage] || I18N_TEXT.en;
    return String(lang[key] ?? I18N_TEXT.en[key] ?? fallback ?? key);
}

export function updateStaticI18nText() {
    for (const el of document.querySelectorAll('[data-i18n]')) {
        el.innerText = i18n(el.dataset.i18n, el.innerText);
    }
    for (const el of document.querySelectorAll('[data-i18n-aria]')) {
        el.setAttribute('aria-label', i18n(el.dataset.i18nAria, el.getAttribute('aria-label') || ''));
    }
    document.documentElement.lang = vizState.uiLanguage === 'zh' ? 'zh-CN' : 'en';
}

export function localizedLayerText(layerKey, field) {
    const spec = tacticalLayerSpec(layerKey);
    const fallback = field === 'short'
        ? spec.shortLabel
        : field === 'summary'
            ? spec.summaryLabel
            : spec.label;
    return i18n(`layer.${layerKey}.${field}`, fallback);
}

export function localizedWorkspaceText(workspaceId, field) {
    const workspace = tacticalWorkspaceDefinitions[workspaceId] || tacticalWorkspaceDefinitions.cop;
    return i18n(`workspace.${workspaceId}.${field}`, workspace[field] || '');
}

export function formatSpeed(value) {
    const speed = Number(value);
    if (!Number.isFinite(speed)) return '1';
    return speed >= 1 ? String(Math.round(speed)) : speed.toFixed(2).replace(/0+$/, '').replace(/\.$/, '');
}

export function formatSpeedButton(value) {
    return `${i18n('ui.speed')}: ${formatSpeed(value)}x`;
}

export function localizeCameraMode(mode) {
    return String(mode || '').toUpperCase() === 'FREE'
        ? i18n('ui.cameraFree')
        : i18n('ui.cameraChase');
}

export function formatTacticalScaleText(kmPer100px, gridStepM, zoomPct) {
    if (vizState.uiLanguage === 'zh') {
        return `100 px = ${kmPer100px.toFixed(1)}公里 | ${i18n('ui.grid')} ${(gridStepM / 1000.0).toFixed(1)}公里 | ${i18n('ui.zoom')} ${zoomPct}%`;
    }
    return `100 px = ${kmPer100px.toFixed(1)} km | ${i18n('ui.grid')} ${(gridStepM / 1000.0).toFixed(1)} km | ${i18n('ui.zoom')} ${zoomPct}%`;
}

export function normalizeI18nToken(value) {
    const raw = String(value || '').trim();
    if (!raw) return '';
    const tail = raw.split(':').filter(Boolean).pop() || raw;
    return tail
        .replace(/^deterministic[-_]/i, '')
        .replace(/^test[-_]/i, '')
        .replace(/[-_]+/g, ' ')
        .replace(/\s+/g, ' ')
        .trim()
        .toLowerCase();
}

export function localizeEnvironmentToken(value) {
    const token = normalizeI18nToken(value);
    if (!token) return '';
    if (vizState.uiLanguage !== 'zh') return '';
    if (ENVIRONMENT_LABEL_ZH[token]) return ENVIRONMENT_LABEL_ZH[token];
    const villageHouse = token.match(/^village house (\d+)$/);
    if (villageHouse) return `村屋 ${villageHouse[1]}`;
    if (token === 'structure') return i18n('env.structure');
    if (token === 'vegetation') return i18n('env.vegetation');
    if (token === 'surface') return i18n('env.surface');
    if (token === 'candidate') return i18n('env.candidate');
    if (token === 'water') return i18n('env.water');
    if (token === 'asphalt') return i18n('env.asphalt');
    if (token === 'concrete') return i18n('env.concrete');
    if (token === 'softdirt') return i18n('env.softdirt');
    if (token === 'hardpacked') return i18n('env.hardpacked');
    return '';
}

export function localizeMissionLabel(value) {
    const raw = String(value || '').trim();
    if (!raw || raw === '--') return '--';
    const key = raw
        .replace(/^TASK_/, 'task_')
        .replace(/([a-z])([A-Z])/g, '$1_$2')
        .replace(/[\s/-]+/g, '_')
        .toLowerCase();
    return i18n(`mission.${key}`, raw.replace(/^TASK_/, '').replaceAll('_', ' '));
}
