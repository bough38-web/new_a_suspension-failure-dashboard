<!DOCTYPE html>
<html>
<head>
  <base target="_top">
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>KTT 정지/부실 관리 대시보드</title>
  
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1"></script>
  <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2.2.0"></script>
  <script src="https://cdn.jsdelivr.net/npm/chartjs-chart-matrix@1.3.0"></script>
  
  <link rel="stylesheet" as="style" crossorigin href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css" />

  <style>
    :root {
      --bg: #f8f9fa; --card: #ffffff; --ink: #343a40; --muted: #868e96; 
      --line: #e9ecef; --brand: #228be6; --brand-light: #e7f5ff;
      --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
      --shadow-hover: 0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -2px rgba(0, 0, 0, 0.025);
    }
    
    body {
      margin: 0; background: var(--bg); color: var(--ink);
      font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, sans-serif;
      -webkit-font-smoothing: antialiased;
    }
    
    .wrap { max-width: 1400px; margin: 32px auto; padding: 0 24px; }
    
    h1 { font-size: 26px; font-weight: 700; margin: 0 0 24px; color: #212529; letter-spacing: -0.5px; }
    h2 { font-size: 16px; font-weight: 600; margin: 0 0 12px; color: #495057; }
    
    /* Panel Design */
    .panel {
      background: var(--card); border: 1px solid var(--line); border-radius: 16px;
      padding: 24px; margin-bottom: 24px; box-shadow: var(--shadow);
      transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .panel:hover { transform: translateY(-2px); box-shadow: var(--shadow-hover); }
    
    .panel-row { display: flex; gap: 24px; flex-wrap: wrap; }
    .panel-row > .panel { flex: 1; min-width: 320px; }
    
    /* Controls */
    .row { display: flex; gap: 20px; flex-wrap: wrap; align-items: center; }
    .hint { color: var(--muted); font-size: 12px; margin-bottom: 6px; font-weight: 500; }
    
    /* Segmented Control */
    .seg { display: inline-flex; background: #f1f3f5; border-radius: 10px; padding: 4px; }
    .seg button {
      padding: 8px 16px; border: 0; background: transparent; cursor: pointer;
      font-size: 14px; font-weight: 600; color: var(--muted); border-radius: 8px;
      transition: all 0.2s;
    }
    .seg button:hover { color: var(--ink); }
    .seg button.on { background: #fff; color: var(--brand); box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    
    /* Chips */
    .chips { display: flex; gap: 8px; flex-wrap: wrap; }
    .chip {
      font-size: 13px; padding: 8px 14px; border-radius: 99px; background: #fff;
      cursor: pointer; border: 1px solid var(--line); color: var(--ink); font-weight: 500;
      transition: all 0.15s;
    }
    .chip:hover { background: #f8f9fa; border-color: #ced4da; }
    .chip.on { background: var(--brand-light); border-color: var(--brand); color: var(--brand); font-weight: 600; }
    
    /* Buttons */
    .btn-small {
      font-size: 12px; padding: 6px 12px; border: 1px solid var(--line);
      background: #fff; border-radius: 8px; cursor: pointer; font-weight: 600; color: var(--muted);
      transition: all 0.15s; margin-top: 8px;
    }
    .btn-small:hover { background: #f8f9fa; color: var(--ink); }
    .btn-small.on { background: var(--brand); color: #fff; border-color: var(--brand); }
    
    /* Chart Area */
    .chart-panel { min-height: 500px; position: relative; }
    canvas { width: 100% !important; height: 100% !important; max-height: 600px; }
    
    /* Toolbar */
    .toolbar { display: flex; gap: 8px; align-items: center; margin-top: 16px; flex-wrap: wrap; }
  </style>
</head>
<body>
<div class="wrap">

  <h1>📊 정지/부실 관리 통합 대시보드</h1>

  <div class="panel">
    <div class="row">
      <div>
        <div class="hint">데이터셋 선택</div>
        <div class="seg" id="dsSeg">
          <button data-v="TOTAL" class="on">총정지</button>
          <button data-v="SP">SP기준</button>
          <button data-v="DELINQUENCY">부실율(KPI)</button>
        </div>
      </div>
      <div>
        <div class="hint">차트 유형</div>
        <div class="seg" id="typeSeg">
          <button data-v="bar" class="on">막대</button>
          <button data-v="line">선 (추이)</button>
          <button data-v="mix">혼합</button>
          <button data-v="radar">레이더</button>
        </div>
      </div>
    </div>
  </div>

  <div class="panel-row">
    <div class="panel">
      <h2>🏢 본부 선택</h2>
      <div id="hubButtons" class="chips"></div>
      <button id="hubAll" class="btn-small">본부 전체 선택</button>
    </div>

    <div class="panel">
      <h2>📍 지사 선택</h2>
      <div id="branchChips" class="chips"></div>
      <div style="display:flex; gap:8px;">
        <button id="branchAll" class="btn-small">지사 전체</button>
        <button id="branchNone" class="btn-small">선택 해제</button>
      </div>
    </div>
  </div>

  <div class="panel">
    <h2>📈 분석 지표 선택</h2>
    <div class="hint" style="margin-bottom:8px;">건수 지표 (클릭하여 다중 선택 가능)</div>
    <div id="chipsCounts" class="chips" style="margin-bottom:16px;"></div>
    
    <div class="hint" style="margin-bottom:8px;">금액/비율 지표</div>
    <div id="chipsFees" class="chips"></div>
    
    <div class="toolbar">
      <button id="btnReset" class="btn-small">선택 초기화</button>
      <button id="btnSelectCounts" class="btn-small">건수 전체</button>
      <button id="btnSelectFees" class="btn-small">월정료 전체</button>
      <div style="flex-grow:1"></div>
      <button id="toggleTopN" class="btn-small">🏆 Top 5 보기</button>
    </div>
  </div>

  <div id="chartContainer" class="panel-row">
      <div class="panel chart-panel">
          <canvas id="chart"></canvas>
      </div>
      <div class="panel chart-panel" id="secondChartPanel" style="display: none;">
          <canvas id="chart2"></canvas>
      </div>
  </div>

</div>

<script>
Chart.register(ChartDataLabels);

// === 1. 설정 및 상수 ===
// 요청하신 커스텀 정렬 순서
const PREFERRED_ORDER = [
  "강북강원", "본부", // 본부 우선
  "중앙", "강북", "서대문", "고양", "의정부", "남양주", "강릉", "원주", // 강북/강원 지사
  "강남", "수원", "분당", "강동", "용인", "평택", "인천", "강서", "부천", "안산", "안양", "관악", // 강남/서부
  "동부산", "남부산", "창원", "서부산", "김해", "울산", "진주", // 부산/경남
  "광주", "전주", "익산", "북광주", "순천", "제주", "목포", // 전남/전북
  "서대전", "충북", "천안", "대전", "충남서부", // 충남/충북
  "동대구", "서대구", "구미", "포항" // 대구/경북
];

const HUB_ALLOWED = ["강남/서부","강북/강원","부산/경남","전남/전북","충남/충북","대구/경북"];

// 고급 컬러 팔레트 (Prism 스타일)
const COLORS = [
  '#228be6', '#fa5252', '#40c057', '#fcc419', '#7950f2', '#e64980', 
  '#15aabf', '#82c91e', '#fd7e14', '#20c997', '#868e96', '#be4bdb'
];
const COLORS_BG = COLORS.map(c => c + 'BB'); // 투명도 추가

// 인덱스 범위
const COUNT_INDEXES = [0,1,2,3,4,5]; 
const FEE_INDEXES   = [6,7,8,9,10,11]; 
const DELINQUENCY_COUNT_INDEXES = [28, 29, 30, 31, 32, 33]; 
const DELINQUENCY_FEE_INDEXES = [34, 35, 36, 37, 38, 39];   

// === 2. 상태 관리 ===
let CHART = null;
let CHART2 = null;
const state = {
  raw: null, ds: 'TOTAL', type: 'bar',
  selectedIdx: new Set(), labelSel: new Set(),
  selectedHub: null, mode: 'hubAll',
  showTopN: false, topNCount: 5
};

// === 3. 초기화 ===
// Google Apps Script 연동
try {
  google.script.run.withSuccessHandler(init).fetchAll();
} catch(e) {
  console.warn("로컬 테스트 모드입니다. 데이터를 로드할 수 없습니다.");
}

function init(payload){
  if(!payload || !payload.ok){ alert("데이터 로딩 실패: " + (payload?.error || "Unknown error")); return; }
  state.raw = payload;

  // DELINQUENCY 메타데이터 보정
  if(state.raw.DELINQUENCY) {
      if (!state.raw.meta.datasets.includes('DELINQUENCY')) state.raw.meta.datasets.push('DELINQUENCY');
      state.raw.meta.datasetNames['DELINQUENCY'] = '부실율';
      state.raw.meta.countIndex = state.raw.meta.countIndex.concat(DELINQUENCY_COUNT_INDEXES);
      state.raw.meta.feeIndex = state.raw.meta.feeIndex.concat(DELINQUENCY_FEE_INDEXES);
  }

  buildHubButtons(); buildBranchChips(); buildHeaderChips(true);
  bindTopNButton();
  renderChart();

  // 이벤트 바인딩
  bindSeg(dsSeg, v => {
    state.ds = v; state.mode = 'hubAll'; state.selectedHub = null;
    state.selectedIdx.clear(); state.labelSel.clear(); state.showTopN = false;
    buildHubButtons(); buildBranchChips(); buildHeaderChips(true); bindTopNButton(); renderChart();
  });
  
  bindSeg(typeSeg, v => {
    state.type = v;
    renderChart(); // 차트 타입 변경 시 즉시 렌더링
  });

  btnReset.onclick = () => { state.selectedIdx.clear(); syncHeaderChips(); renderChart(); };
  btnSelectCounts.onclick = () => quickSelect('count');
  btnSelectFees.onclick = () => quickSelect('fee');
  
  hubAll.onclick = () => {
    state.mode='hubAll'; state.selectedHub=null; 
    buildHubButtons(); buildBranchChips(); state.showTopN=false; bindTopNButton(); renderChart();
  };
  
  branchAll.onclick = () => {
    state.mode='branchAll'; state.selectedHub=null; 
    buildBranchChips(true); state.showTopN=false; bindTopNButton(); renderChart();
  };
  
  branchNone.onclick = () => {
    state.labelSel.clear(); syncBranchChips(); renderChart();
  };
}

// === 4. UI 빌더 ===
function buildHubButtons(){
  hubButtons.innerHTML='';
  HUB_ALLOWED.forEach(h=>{
    const chip = document.createElement('div');
    chip.className = 'chip' + (state.selectedHub===h && state.mode==='branch' ? ' on' : '');
    chip.textContent = h;
    chip.onclick = () => {
      if(state.mode==='branch' && state.selectedHub===h){ state.mode='hubAll'; state.selectedHub=null; }
      else { state.mode='branch'; state.selectedHub=h; }
      state.showTopN = false;
      buildHubButtons(); buildBranchChips(); bindTopNButton(); renderChart();
    };
    hubButtons.appendChild(chip);
  });
}

function buildBranchChips(all=false){
  branchChips.innerHTML=''; 
  let branches=[];
  
  if(state.mode==='branchAll' || all){ branches = state.raw[state.ds].branch.labels.slice(); }
  else if(state.mode==='branch' && state.selectedHub){ branches = state.raw.meta.hubBranchMap[state.selectedHub] || []; }
  else return;

  const blockLabels = currentBlock().labels;
  const filteredBranches = branches.filter(b => blockLabels.includes(b));
  
  // 지사 칩 생성 시에도 커스텀 정렬 적용
  filteredBranches.sort((a, b) => getSortIndex(a) - getSortIndex(b));
  
  state.labelSel = new Set(filteredBranches); 

  filteredBranches.forEach(n => {
    const el = document.createElement('div');
    el.className = 'chip on'; el.textContent = n;
    el.onclick = () => {
      if(state.labelSel.has(n)) state.labelSel.delete(n); else state.labelSel.add(n);
      el.classList.toggle('on'); renderChart();
    };
    branchChips.appendChild(el);
  });
}

function currentBlock(){ return state.mode==='hubAll' ? state.raw[state.ds].hub : state.raw[state.ds].branch; }

function buildHeaderChips(init=false){
  const headers = currentBlock().header; 
  chipsCounts.innerHTML=''; chipsFees.innerHTML='';
  
  headers.forEach((h, i) => {
    const chip = document.createElement('div'); 
    chip.className = 'chip'; chip.textContent = h; chip.dataset.idx = i;
    chip.onclick = () => {
      const idx = +chip.dataset.idx;
      if(state.selectedIdx.has(idx)) state.selectedIdx.delete(idx); else state.selectedIdx.add(idx);
      chip.classList.toggle('on'); renderChart();
    };
    if(state.raw.meta.countIndex.includes(i)) chipsCounts.appendChild(chip);
    else if(state.raw.meta.feeIndex.includes(i)) chipsFees.appendChild(chip);
  });
  
  if(init) state.selectedIdx = new Set([0, 6]); 
  syncHeaderChips();
}

function syncHeaderChips(){
  document.querySelectorAll('#chipsCounts .chip, #chipsFees .chip').forEach(ch => 
    ch.classList.toggle('on', state.selectedIdx.has(+ch.dataset.idx))
  );
}
function syncBranchChips(){
  document.querySelectorAll('#branchChips .chip').forEach(ch => 
    ch.classList.toggle('on', state.labelSel.has(ch.textContent))
  );
}

function quickSelect(kind){
  state.selectedIdx.clear();
  (kind==='count' ? state.raw.meta.countIndex : state.raw.meta.feeIndex).forEach(i => state.selectedIdx.add(i));
  syncHeaderChips(); renderChart();
}

// === 5. 차트 렌더링 로직 (핵심) ===
function renderChart(){
  const block = currentBlock();
  let idxs = [...state.selectedIdx];

  // 1. 라벨 필터링
  let labelsToProcess = [];
  let labelIndices = [];

  if(state.mode === 'hubAll'){
    labelsToProcess = block.labels.filter(l => HUB_ALLOWED.includes(l));
    labelIndices = block.labels.map((l, i) => HUB_ALLOWED.includes(l) ? i : -1).filter(i => i >= 0);
  } else if(state.mode === 'branch' || state.mode === 'branchAll'){
    const blockLabels = block.labels;
    labelsToProcess = Array.from(state.labelSel).filter(l => blockLabels.includes(l));
    labelIndices = labelsToProcess.map(l => blockLabels.indexOf(l)).filter(i => i !== -1);
  }

  if (!labelsToProcess.length || !idxs.length) { drawEmpty('데이터가 선택되지 않았습니다.'); return; }

  // 2. 커스텀 정렬 적용 (Top N 아닐 때만)
  if (!state.showTopN) {
    const combined = labelsToProcess.map((l, i) => ({ label: l, idx: labelIndices[i] }));
    combined.sort((a, b) => getSortIndex(a.label) - getSortIndex(b.label));
    labelsToProcess = combined.map(c => c.label);
    labelIndices = combined.map(c => c.idx);
  }

  // 3. Top N 로직
  if (state.showTopN && idxs.length > 0) {
    const sortIdx = idxs[0];
    const dataArr = labelIndices.map(origIdx => ({
        label: block.labels[origIdx],
        value: parseNum(block.data[origIdx]?.[sortIdx]),
        origIdx: origIdx
    }));
    dataArr.sort((a, b) => (b.value || 0) - (a.value || 0)); // 내림차순
    const topData = dataArr.slice(0, state.topNCount);
    
    labelsToProcess = topData.map(d => d.label);
    labelIndices = topData.map(d => d.origIdx);
  }

  // 4. 데이터셋 구축
  const datasets = buildDatasets(block.header, idxs, (ci) => labelIndices.map(i => parseNum(block.data[i]?.[ci])), labelsToProcess);
  const cfg = buildChartCfg(labelsToProcess, datasets, block.header, idxs);

  // 5. 차트 그리기
  const cvs1 = document.getElementById('chart');
  const cvs2 = document.getElementById('chart2');
  const p2 = document.getElementById('secondChartPanel');
  const container = document.getElementById('chartContainer');

  if(CHART) CHART.destroy();
  if(CHART2) CHART2.destroy();

  // 2개 차트로 분리 (막대/레이더 모드에서만)
  if ((state.type === 'bar' || state.type === 'radar') && idxs.length > 3) {
      container.classList.add('panel-row');
      p2.style.display = 'block';

      const mid = Math.ceil(idxs.length / 2);
      const idxs1 = idxs.slice(0, mid);
      const idxs2 = idxs.slice(mid);

      const d1 = buildDatasets(block.header, idxs1, (ci) => labelIndices.map(i => parseNum(block.data[i]?.[ci])), labelsToProcess);
      const c1 = buildChartCfg(labelsToProcess, d1, block.header, idxs1);
      CHART = new Chart(cvs1, c1);

      const d2 = buildDatasets(block.header, idxs2, (ci) => labelIndices.map(i => parseNum(block.data[i]?.[ci])), labelsToProcess);
      const c2 = buildChartCfg(labelsToProcess, d2, block.header, idxs2);
      CHART2 = new Chart(cvs2, c2);
  } else {
      container.classList.remove('panel-row');
      p2.style.display = 'none';
      CHART = new Chart(cvs1, cfg);
  }
}

// === 6. 헬퍼 함수 ===
function getSortIndex(label) {
  const idx = PREFERRED_ORDER.indexOf(label);
  return idx === -1 ? 999 : idx;
}

function buildDatasets(headers, idxs, valCol, labels) {
  return idxs.map((ci, k) => {
    const isFee = state.raw.meta.feeIndex.includes(ci);
    const isPct = (headers[ci]||'').includes('%') || (headers[ci]||'').includes('율');

    let type = state.type;
    let yAxisID = 'y';
    if(state.type === 'mix') {
        if(isFee || isPct) { type = 'line'; yAxisID = 'y2'; }
        else { type = 'bar'; }
    }

    return {
      type: type,
      label: headers[ci],
      data: valCol(ci),
      backgroundColor: isFee ? COLORS_BG[k % COLORS_BG.length] : COLORS[k % COLORS.length],
      borderColor: isFee ? COLORS[k % COLORS.length] : COLORS[k % COLORS.length],
      borderWidth: type === 'line' ? 3 : 0,
      borderRadius: 4,
      tension: 0.3,
      yAxisID: yAxisID,
      datalabels: {
        display: labels.length <= 15 ? 'auto' : false, // 데이터 많으면 라벨 숨김
        align: 'end', anchor: 'end',
        formatter: (v) => formatValue(v, isPct)
      }
    };
  });
}

function buildChartCfg(labels, datasets, headers, idxs) {
  // 공통 옵션
  const options = {
    responsive: true, maintainAspectRatio: false,
    animation: { duration: 1000, easing: 'easeOutQuart' },
    layout: { padding: { top: 20, right: 20, left: 10, bottom: 10 } },
    plugins: {
      legend: { labels: { usePointStyle: true, font: { family: 'Pretendard', size: 12 } } },
      tooltip: {
        backgroundColor: 'rgba(33, 37, 41, 0.95)',
        titleFont: { family: 'Pretendard', size: 14 },
        bodyFont: { family: 'Pretendard', size: 13 },
        padding: 12, cornerRadius: 8,
        callbacks: {
          label: (ctx) => {
             const isPct = ctx.dataset.yAxisID === 'y2' || ctx.dataset.label.includes('%') || ctx.dataset.label.includes('율');
             return ` ${ctx.dataset.label}: ${formatValue(ctx.parsed.y || ctx.parsed.r, isPct)}`;
          }
        }
      }
    },
    scales: {
      x: { grid: { display: false }, ticks: { font: { family: 'Pretendard' } } },
      y: { 
        beginAtZero: true, grid: { color: '#f1f3f5' }, border: { display: false },
        ticks: { font: { family: 'Pretendard' }, callback: (v) => v.toLocaleString() }
      }
    }
  };

  if(state.type === 'mix') {
    options.scales.y2 = {
      position: 'right', beginAtZero: true, grid: { display: false },
      ticks: { callback: (v) => v + '%' } // 오른쪽 축 % 표시
    };
  }
  
  if(state.type === 'radar') {
    options.scales = { r: { beginAtZero: true, pointLabels: { font: { family: 'Pretendard', size: 12 } } } };
  }

  return { type: state.type === 'mix' ? 'bar' : state.type, data: { labels, datasets }, options };
}

function bindTopNButton() {
    const btn = document.getElementById('toggleTopN');
    btn.onclick = () => {
        state.showTopN = !state.showTopN;
        btn.textContent = state.showTopN ? `전체 보기 (${state.topNCount} 적용됨)` : `🏆 Top ${state.topNCount} 보기`;
        btn.classList.toggle('on', state.showTopN);
        renderChart();
    };
}

function bindSeg(container, onChange){
  container.querySelectorAll('button').forEach(btn => {
    btn.onclick = () => {
      container.querySelectorAll('button').forEach(b => b.classList.remove('on'));
      btn.classList.add('on');
      onChange(btn.dataset.v);
    };
  });
}

// === 유틸리티 ===
function parseNum(v) {
  if (v === "" || v === null || v === undefined) return null;
  const num = Number(String(v).replace(/[,%\s]/g, ''));
  return isNaN(num) ? null : num;
}

function formatValue(v, isPct) {
  if (v == null || isNaN(v)) return '';
  if (isPct) {
      // 1 미만(예: 0.005)인 경우 100을 곱해서 표시할지, 원본이 이미 %인지 판단 필요
      // 여기서는 값이 1보다 작으면 100을 곱하는 로직을 추가 (상황에 따라 조정 필요)
      let val = Number(v);
      if (Math.abs(val) <= 1 && val !== 0) val *= 100; 
      return val.toFixed(1) + '%'; // 소수점 1자리 + %
  }
  return Number(v).toLocaleString('ko-KR');
}

function drawEmpty(msg){
  const ctx = document.getElementById('chart').getContext('2d');
  ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
  if(CHART) CHART.destroy(); if(CHART2) CHART2.destroy();
  ctx.save();
  ctx.font = '16px Pretendard'; ctx.fillStyle = '#868e96'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  ctx.fillText(msg, ctx.canvas.width/2, ctx.canvas.height/2);
  ctx.restore();
}

</script>
</body>
</html>
